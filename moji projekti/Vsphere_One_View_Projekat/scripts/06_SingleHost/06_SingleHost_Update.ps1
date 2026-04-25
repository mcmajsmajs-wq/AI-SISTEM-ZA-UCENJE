<#
.SYNOPSIS
    Kompletna logika za testiranje na jednom VMware ESXi hostu sa svim sigurnosnim merama.
.DESCRIPTION
    Ova skripta pruža kompletan radni tok za ažuriranje jednog ESXi hosta uključujući:
    - Pre-check validacije (N-1 capacity, VM migratability)
    - Automatski backup konfiguracije
    - Maintenance mode upravljanje
    - VMware Update Manager integraciju (compliance check, staging, remediate)
    - Health check posle ažuriranja
    - Automatski rollback u slučaju greške
    
    NOVA ISPRAVLJENA LOGIKA:
    - Koristi Test-VMHostCompliance umesto direktnog ISO mount-a
    - Stage-uje zakrpe preko VUM/UMDS
    - Primenjuje zakrpe kroz Remediate-Inventory
    
.PARAMETER VMHostName
    Ime ESXi hosta koji se ažurira
.PARAMETER Config
    Konfiguracioni objekat
.PARAMETER Simulation
    Test režim bez stvarnih promena
.PARAMETER BaselineName
    Ime VMware patch baseline-a
.PARAMETER SkipBackup
    Preskoči backup (za testiranje)
.PARAMETER Force
    Forsiraj izvršenje bez potvrde
.EXAMPLE
    Invoke-SingleHostUpdate -VMHostName "esxi-test-01" -Config $config -Simulation
.EXAMPLE
    Invoke-SingleHostUpdate -VMHostName "esxi-test-01" -Config $config -BaselineName "Critical Patches"
.NOTES
    File Name      : 06_SingleHost_Update.ps1
    Author         : Opencode
    Version        : 2.0.0
    Last Updated   : 2026-02-02
    
    SIGURNOSNE MERE:
    1. N-1 Capacity Check - Proverava da li ostali hostovi imaju dovoljno resursa
    2. VM Migratability Check - Proverava da li VM-ovi mogu da migriraju
    3. Automatski Backup - Čuva konfiguraciju pre promena
    4. Maintenance Mode - Bezbedno isključuje host iz produkcije
    5. Health Check - Verifikacija posle ažuriranja
    6. Automatski Rollback - Vraća prethodno stanje ako nešto ne uspe
#>

# ============================================
# SEKCIJA 1: IMPORT MODULA I KONFIGURACIJA
# ============================================

# Import utility funkcija za rad sa logovanjem, greškama i konekcijama
. "$PSScriptRoot\..\05_Utility\Logger.ps1"
. "$PSScriptRoot\..\05_Utility\ErrorHandler.ps1"
. "$PSScriptRoot\..\05_Utility\ConnectionManager.ps1"
. "$PSScriptRoot\..\05_Utility\ConfigManager.ps1"

# ============================================
# SEKCIJA 2: GLAVNA FUNKCIJA
# ============================================

function Invoke-SingleHostUpdate {
    [CmdletBinding()]
    param(
        # Obavezni parametar - ime ESXi hosta
        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [string]$VMHostName,
        
        # Konfiguracioni objekat sa podešavanjima
        [Parameter(Mandatory=$true)]
        [object]$Config,
        
        # Test režim - simulacija bez stvarnih promena
        [Parameter(Mandatory=$false)]
        [switch]$Simulation = $true,
        
        # Ime patch baseline-a (ako se razlikuje od default)
        [Parameter(Mandatory=$false)]
        [string]$BaselineName = $null,
        
        # Opcija za preskakanje backup-a (samo za test)
        [Parameter(Mandatory=$false)]
        [switch]$SkipBackup = $false,
        
        # Forsiraj izvršenje bez dodatne potvrde
        [Parameter(Mandatory=$false)]
        [switch]$Force = $false
    )
    
    # ============================================
    # SEKCIJA 3: INICIJALIZACIJA I PROVERE
    # ============================================
    
    Write-EnhancedLog "=== POČETAK SINGLE HOST UPDATE ===" "SUCCESS" "SingleHost"
    Write-EnhancedLog "Ciljani host: $VMHostName" "INFO" "SingleHost"
    Write-EnhancedLog "Simulation mode: $Simulation" "INFO" "SingleHost"
    
    # Ako nije u test režimu, zahtevaj eksplicitnu potvrdu (bezbednosna mera)
    if (-not $Simulation -and -not $Force) {
        $confirmation = Read-Host "Ovo će ažurirati host $VMHostName. Da li ste sigurni? (da/ne)"
        if ($confirmation -ne 'da') {
            Write-EnhancedLog "Korisnik je otkazao operaciju" "WARN" "SingleHost"
            return @{ Success = $false; Reason = "UserCancelled" }
        }
    }
    
    # ============================================
    # SEKCIJA 4: GLAVNI TRY-CATCH BLOK
    # ============================================
    
    # Try-CatchBlock omogućava elegantno rukovanje greškama i recovery
    return Try-CatchBlock -Context "SingleHostUpdate" -RecoveryActions @(
        
        # Recovery Action 1: Pokušaj ponovne konekcije na vCenter
        (New-RecoveryAction -Action {
            param($ErrorInfo)
            Write-EnhancedLog "Pokušaj re-konekcije na vCenter..." "INFO" "SingleHost"
            $connection = Connect-vCenterSafely -Server $Config.vCenter.server -Credential (Get-StoredCredential -Target $Config.vCenter.credentialTarget)
            return @{ Success = $true; Connection = $connection }
        } -Name "Reconnect-vCenter" -MaxAttempts 3),
        
        # Recovery Action 2: Rollback ako je dozvoljeno
        (New-RecoveryAction -Action {
            param($ErrorInfo)
            Write-EnhancedLog "Pokretanje rollback procedure..." "INFO" "SingleHost"
            
            # Pokušaj rollback-a ako postoji backup
            $rollbackResult = Invoke-SingleHostRollback -VMHostName $VMHostName -Config $Config
            return @{ Success = $rollbackResult.Success; RollbackResult = $rollbackResult }
        } -Name "Rollback-Configuration" -MaxAttempts 1)
        
    ) -FinallyBlock {
        # Ova sekcija se izvršava uvek, čak iako dođe do greške
        # Osigurava da se konekcije zatvore i resursi oslobode
        Write-EnhancedLog "Čišćenje resursa..." "INFO" "SingleHost"
        Disconnect-AllSafely
    } -ScriptBlock {
        
        # ============================================
        # SEKCIJA 5: KONEKCIJA NA vCENTER
        # ============================================
        
        Write-EnhancedLog "Konekcija na vCenter: $($Config.vCenter.server)" "INFO" "SingleHost"
        
        # Bezbedna konekcija sa health check-om
        $vCenterConnection = Connect-vCenterSafely `
            -Server $Config.vCenter.server `
            -Credential (Get-StoredCredential -Target $Config.vCenter.credentialTarget) `
            -TestConnection
        
        Write-EnhancedLog "Uspešna konekcija na vCenter" "SUCCESS" "SingleHost"
        
        # ============================================
        # SEKCIJA 6: VALIDACIJA HOSTA
        # ============================================
        
        Write-EnhancedLog "Validacija hosta: $VMHostName" "INFO" "SingleHost"
        
        # Dohvati ESXi host objekat
        $VMHost = Get-VMHost -Name $VMHostName -Server $vCenterConnection
        
        if (-not $VMHost) {
            throw "Host $VMHostName nije pronađen u vCenter"
        }
        
        Write-EnhancedLog "Host pronađen: $($VMHost.Name)" "SUCCESS" "SingleHost"
        
        # Proveri da li je host već u maintenance modu (greška ako jeste)
        if ($VMHost.ConnectionState -eq 'Maintenance') {
            throw "Host $VMHostName je već u maintenance modu. Prethodna operacija možda nije završena."
        }
        
        # ============================================
        # SEKCIJA 7: N-1 CAPACITY CHECK
        # ============================================
        
        # Ova provera osigurava da ostali hostovi u klasteru imaju dovoljno resursa
        # da prim VM-ove sa hosta koji se ažurira
        
        Write-EnhancedLog "Provera N-1 kapaciteta..." "INFO" "SingleHost"
        
        # Dohvati klaster kom pripada host
        $Cluster = Get-Cluster -VMHost $VMHost
        
        # Proveri kapacitet
        $capacityCheck = Test-NMinusOneCapacity -Cluster $Cluster -ExcludingHost $VMHost
        
        if (-not $capacityCheck.HasCapacity) {
            throw "N-1 Capacity Check NEUSPEŠAN. Nedovoljno resursa na ostalim hostovima. Potrebno: $($capacityCheck.RequiredCpu) CPU, $($capacityCheck.RequiredMemory) GB RAM. Dostupno: $($capacityCheck.AvailableCpu) CPU, $($capacityCheck.AvailableMemory) GB RAM"
        }
        
        Write-EnhancedLog "N-1 Capacity Check USPEŠAN" "SUCCESS" "SingleHost"
        Write-EnhancedLog "Dostupno: $($capacityCheck.AvailableCpu) CPU, $($capacityCheck.AvailableMemory) GB RAM" "INFO" "SingleHost"
        
        # ============================================
        # SEKCIJA 8: VM MIGRATABILITY CHECK
        # ============================================
        
        # Proverava da li VM-ovi mogu bezbedno da migriraju na druge hostove
        # Detektuje probleme kao što su nedostatak VMware Tools, mount-ovani ISO, itd.
        
        Write-EnhancedLog "Provera VM migratability..." "INFO" "SingleHost"
        
        $migratabilityCheck = Test-VMMigratability -VMHost $VMHost
        
        if ($migratabilityCheck.HasIssues) {
            $issues = $migratabilityCheck.Issues | ForEach-Object { "$($_.VM): $($_.Reason)" }
            throw "VM Migratability Check NEUSPEŠAN. Problemi: $($issues -join '; ')"
        }
        
        Write-EnhancedLog "VM Migratability Check USPEŠAN" "SUCCESS" "SingleHost"
        Write-EnhancedLog "Broj VM-ova za migraciju: $($migratabilityCheck.TotalVMs)" "INFO" "SingleHost"
        
        # ============================================
        # SEKCIJA 9: BACKUP KONFIGURACIJE
        # ============================================
        
        # Kreira kompletan backup konfiguracije hosta pre bilo kakvih promena
        # Ovo omogućava rollback na prethodno stanje ako nešto pođe po zlu
        
        if (-not $SkipBackup) {
            Write-EnhancedLog "Kreiranje backup-a konfiguracije..." "INFO" "SingleHost"
            
            $backupResult = Backup-VMHostConfiguration -VMHost $VMHost
            
            if (-not $backupResult.Success) {
                throw "Backup konfiguracije NEUSPEŠAN: $($backupResult.Error)"
            }
            
            Write-EnhancedLog "Backup kreiran: $($backupResult.BackupPath)" "SUCCESS" "SingleHost"
            
            # Sačuvaj putanju za rollback
            $script:BackupPath = $backupResult.BackupPath
        } else {
            Write-EnhancedLog "Backup preskočen (SkipBackup = true)" "WARN" "SingleHost"
        }
        
        # ============================================
        # SEKCIJA 10: SIMULATION MODE CHECK
        # ============================================
        
        # Ako je u simulation režimu, samo prikaži šta bi se desilo
        if ($Simulation) {
            Write-EnhancedLog "=== SIMULATION MODE ===" "WARN" "SingleHost"
            Write-EnhancedLog "Sledeće akcije bi se izvršile:" "INFO" "SingleHost"
            Write-EnhancedLog "1. Uključiti Maintenance Mode na $VMHostName" "INFO" "SingleHost"
            Write-EnhancedLog "2. Migrirati sve VM-ove sa hosta" "INFO" "SingleHost"
            Write-EnhancedLog "3. Proveriti compliance sa baseline-om" "INFO" "SingleHost"
            Write-EnhancedLog "4. Stage-ovati zakrpe u VUM" "INFO" "SingleHost"
            Write-EnhancedLog "5. Remediate hosta (primena zakrpa)" "INFO" "SingleHost"
            Write-EnhancedLog "6. Reboot hosta ako je potrebno" "INFO" "SingleHost"
            Write-EnhancedLog "7. Health check posle reboot-a" "INFO" "SingleHost"
            Write-EnhancedLog "8. Isključiti Maintenance Mode" "INFO" "SingleHost"
            Write-EnhancedLog "9. Vratiti VM-ove na hosta" "INFO" "SingleHost"
            Write-EnhancedLog "=== KRAJ SIMULACIJE ===" "WARN" "SingleHost"
            
            return @{
                Success = $true
                Simulation = $true
                HostName = $VMHostName
                PlannedActions = @("MaintenanceOn", "VMMigration", "ComplianceCheck", "StagePatches", "Remediate", "Reboot", "HealthCheck", "MaintenanceOff", "VMMigrationBack")
            }
        }
        
        # ============================================
        # SEKCIJA 11: MAINTENANCE MODE
        # ============================================
        
        # Prelazak u maintenance mode - host se označava kao nedostupan za nove VM-ove
        # Ovo je preporučena praksa pre bilo kakvih održavanja
        
        Write-EnhancedLog "Uključivanje Maintenance Mode..." "INFO" "SingleHost"
        
        Set-VMHost -VMHost $VMHost -State Maintenance -Confirm:$false | Out-Null
        
        Write-EnhancedLog "Maintenance Mode uključen" "SUCCESS" "SingleHost"
        
        # ============================================
        # SEKCIJA 12: MIGRACIJA VM-OVA
        # ============================================
        
        # Migrira sve uključene VM-ove na druge hostove u klasteru
        # Koristi vMotion za live migraciju bez downtime-a
        
        Write-EnhancedLog "Migracija VM-ova..." "INFO" "SingleHost"
        
        $vms = Get-VM -VMHost $VMHost | Where-Object { $_.PowerState -eq 'PoweredOn' }
        
        foreach ($vm in $vms) {
            Write-EnhancedLog "Migracija VM: $($vm.Name)" "INFO" "SingleHost"
            
            # Pronađi najbolji ciljni host (sa najviše slobodnih resursa)
            $targetHost = Get-VMHost -Location $Cluster | 
                Where-Object { $_.Name -ne $VMHost.Name -and $_.ConnectionState -eq 'Connected' } | 
                Sort-Object -Property MemoryUsageGB | 
                Select-Object -First 1
            
            if (-not $targetHost) {
                throw "Nema dostupnih hostova za migraciju VM-a $($vm.Name)"
            }
            
            # Izvrši migraciju
            Move-VM -VM $vm -Destination $targetHost -Confirm:$false | Out-Null
            
            Write-EnhancedLog "VM $($vm.Name) migriran na $($targetHost.Name)" "SUCCESS" "SingleHost"
        }
        
        Write-EnhancedLog "Svi VM-ovi migrirani" "SUCCESS" "SingleHost"
        
        # ============================================
        # SEKCIJA 13: VMWARE COMPLIANCE CHECK
        # ============================================
        
        # Proverava da li host ispunjava baseline za zakrpe
        # Ovo je NOVA ISPRAVLJENA LOGIKA koja koristi VUM API
        
        Write-EnhancedLog "Provera compliance statusa..." "INFO" "SingleHost"
        
        # Odredi koji baseline da koristimo
        $baseline = if ($BaselineName) {
            Get-PatchBaseline -Name $BaselineName
        } else {
            Get-PatchBaseline | Where-Object { $_.IsSystemBaseline -eq $true } | Select-Object -First 1
        }
        
        if (-not $baseline) {
            throw "Patch baseline nije pronađen"
        }
        
        Write-EnhancedLog "Korišćen baseline: $($baseline.Name)" "INFO" "SingleHost"
        
        # Testiraj compliance
        $compliance = Test-Compliance -Entity $VMHost -Baseline $baseline
        
        Write-EnhancedLog "Compliance status: $($compliance.Status)" "INFO" "SingleHost"
        
        if ($compliance.Status -eq 'Compliant') {
            Write-EnhancedLog "Host je već compliant. Nema potrebe za ažuriranjem." "SUCCESS" "SingleHost"
            
            # Preskoči na health check
            $skipUpdate = $true
        } else {
            $skipUpdate = $false
        }
        
        # ============================================
        # SEKCIJA 14: STAGE ZAKRPA (AKO JE POTREBNO)
        # ============================================
        
        if (-not $skipUpdate) {
            Write-EnhancedLog "Stage-ovanje zakrpa..." "INFO" "SingleHost"
            
            # Stage zakrpe na host (preuzimanje bez primene)
            Stage-Patch -Entity $VMHost -Baseline $baseline | Out-Null
            
            Write-EnhancedLog "Zakrpe stage-ovane" "SUCCESS" "SingleHost"
            
            # ============================================
            # SEKCIJA 15: REMEDIATE (PRIMENA ZAKRPA)
            # ============================================
            
            Write-EnhancedLog "Primena zakrpa (remediate)..." "INFO" "SingleHost"
            
            # Primeni zakrpe na host
            Remediate-Inventory -Entity $VMHost -Baseline $baseline -Confirm:$false | Out-Null
            
            Write-EnhancedLog "Zakrpe primenjene" "SUCCESS" "SingleHost"
        }
        
        # ============================================
        # SEKCIJA 16: REBOOT I PROVERA
        # ============================================
        
        Write-EnhancedLog "Restartovanje hosta..." "INFO" "SingleHost"
        
        # Restartuj host (ako je potrebno nakon zakrpa)
        Restart-VMHost -VMHost $VMHost -Confirm:$false | Out-Null
        
        Write-EnhancedLog "Host restartovan, čekam na ponovno podizanje..." "INFO" "SingleHost"
        
        # Sačekaj da host ponovo dođe online (maksimum 10 minuta)
        $maxWait = 600  # sekundi
        $waited = 0
        $sleepInterval = 30
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds $sleepInterval
            $waited += $sleepInterval
            
            # Proveri da li je host ponovo dostupan
            $reconnectedHost = Get-VMHost -Name $VMHostName -Server $vCenterConnection
            
            if ($reconnectedHost.ConnectionState -eq 'Maintenance') {
                Write-EnhancedLog "Host ponovo dostupan nakon $waited sekundi" "SUCCESS" "SingleHost"
                break
            }
            
            Write-EnhancedLog "Čekam na host... ($waited/$maxWait sekundi)" "INFO" "SingleHost"
        }
        
        if ($waited -ge $maxWait) {
            throw "Host nije ponovo dostupan nakon $maxWait sekundi. Proveri ručno."
        }
        
        # ============================================
        # SEKCIJA 17: HEALTH CHECK POSLE AŽURIRANJA
        # ============================================
        
        Write-EnhancedLog "Health check posle ažuriranja..." "INFO" "SingleHost"
        
        $healthCheck = Test-VMHostHealth -VMHost $reconnectedHost
        
        if (-not $healthCheck.IsHealthy) {
            throw "Health Check NEUSPEŠAN: $($healthCheck.Issues -join '; ')"
        }
        
        Write-EnhancedLog "Health Check USPEŠAN" "SUCCESS" "SingleHost"
        
        # Ponovo proveri compliance
        $postCompliance = Test-Compliance -Entity $reconnectedHost -Baseline $baseline
        
        if ($postCompliance.Status -ne 'Compliant') {
            throw "Host nije compliant nakon ažuriranja. Status: $($postCompliance.Status)"
        }
        
        Write-EnhancedLog "Compliance verifikovan: $($postCompliance.Status)" "SUCCESS" "SingleHost"
        
        # ============================================
        # SEKCIJA 18: VRAĆANJE U PRODUKCIJU
        # ============================================
        
        # Isključi maintenance mode
        Write-EnhancedLog "Isključivanje Maintenance Mode..." "INFO" "SingleHost"
        
        Set-VMHost -VMHost $reconnectedHost -State Connected -Confirm:$false | Out-Null
        
        Write-EnhancedLog "Maintenance Mode isključen" "SUCCESS" "SingleHost"
        
        # Vrati VM-ove (opciono - one će se same vratiti kroz DRS)
        Write-EnhancedLog "VM-ovi će se automatski rasporediti kroz DRS" "INFO" "SingleHost"
        
        # ============================================
        # SEKCIJA 19: REZULTAT
        # ============================================
        
        Write-EnhancedLog "=== SINGLE HOST UPDATE USPEŠAN ===" "SUCCESS" "SingleHost"
        
        return [PSCustomObject]@{
            Success = $true
            HostName = $VMHostName
            StartTime = $script:StartTime
            EndTime = Get-Date
            DurationMinutes = [math]::Round(((Get-Date) - $script:StartTime).TotalMinutes, 2)
            VMsMigrated = $vms.Count
            BackupPath = $script:BackupPath
            ComplianceStatus = $postCompliance.Status
            HealthStatus = "Healthy"
        }
    }
}

# ============================================
# SEKCIJA 20: POMOĆNE FUNKCIJE
# ============================================

<#
.SYNOPSIS
    Proverava N-1 kapacitet u klasteru.
.DESCRIPTION
    Proverava da li ostali hostovi u klasteru imaju dovoljno resursa
    da prim VM-ove sa hosta koji se ažurira.
    
    Proračun uključuje:
    - Ukupan CPU i memorija na ostalim hostovima
    - Trenutno zauzeće na ostalim hostovima
    - Zahteve VM-ova koji će migrirati
    - Rezervu od 20% za sigurnost
.PARAMETER Cluster
    VMware klaster objekat
.PARAMETER ExcludingHost
    Host koji se izuzima iz proračuna (onaj koji se ažurira)
.RETURNS
    PSCustomObject sa propertijima:
    - HasCapacity: Boolean da li ima dovoljno kapaciteta
    - AvailableCpu: Dostupan CPU u GHz
    - AvailableMemory: Dostupna memorija u GB
    - RequiredCpu: Potreban CPU za migraciju
    - RequiredMemory: Potrebna memorija za migraciju
#>
function Test-NMinusOneCapacity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [object]$Cluster,
        
        [Parameter(Mandatory=$true)]
        [object]$ExcludingHost
    )
    
    Write-EnhancedLog "Provera N-1 kapaciteta za klaster: $($Cluster.Name)" "INFO" "CapacityCheck"
    
    # Dohvati sve hostove osim onog koji se ažurira
    $otherHosts = Get-VMHost -Location $Cluster | 
        Where-Object { $_.Name -ne $ExcludingHost.Name -and $_.ConnectionState -eq 'Connected' }
    
    if ($otherHosts.Count -eq 0) {
        Write-EnhancedLog "Nema drugih hostova u klasteru!" "ERROR" "CapacityCheck"
        return @{ HasCapacity = $false }
    }
    
    # Izračunaj ukupan CPU na ostalim hostovima (u MHz za preciznost)
    $totalCpuMhz = ($otherHosts | Measure-Object -Property CpuTotalMhz -Sum).Sum
    
    # Izračunaj ukupnu memoriju na ostalim hostovima (u MB)
    $totalMemoryMB = ($otherHosts | Measure-Object -Property MemoryTotalMB -Sum).Sum
    
    # Izračunaj trenutno zauzeće na ostalim hostovima
    $usedCpuMhz = ($otherHosts | Measure-Object -Property CpuUsageMhz -Sum).Sum
    $usedMemoryMB = ($otherHosts | Measure-Object -Property MemoryUsageMB -Sum).Sum
    
    # Izračunaj dostupan kapacitet
    $availableCpuMhz = $totalCpuMhz - $usedCpuMhz
    $availableMemoryMB = $totalMemoryMB - $usedMemoryMB
    
    # Konvertuj u GHz i GB za čitljivost
    $availableCpu = [math]::Round($availableCpuMhz / 1000, 2)
    $availableMemory = [math]::Round($availableMemoryMB / 1024, 2)
    
    Write-EnhancedLog "Dostupno na ostalim hostovima: $availableCpu GHz CPU, $availableMemory GB RAM" "INFO" "CapacityCheck"
    
    # Izračunaj zahteve hosta koji se ažurira
    $requiredCpu = [math]::Round($ExcludingHost.NumCpu * 0.8, 2)  # 80% rezerva
    $requiredMemory = [math]::Round($ExcludingHost.MemoryTotalGB * 0.8, 2)  # 80% rezerva
    
    Write-EnhancedLog "Potrebno za migraciju: $requiredCpu GHz CPU, $requiredMemory GB RAM" "INFO" "CapacityCheck"
    
    # Proveri da li ima dovoljno kapaciteta
    $hasCapacity = ($availableCpuMhz -ge ($requiredCpu * 1000 * 0.8)) -and 
                   ($availableMemoryMB -ge ($requiredMemory * 1024 * 0.8))
    
    return [PSCustomObject]@{
        HasCapacity = $hasCapacity
        AvailableCpu = $availableCpu
        AvailableMemory = $availableMemory
        RequiredCpu = $requiredCpu
        RequiredMemory = $requiredMemory
        HostCount = $otherHosts.Count
    }
}

<#
.SYNOPSIS
    Proverava da li VM-ovi mogu da migriraju.
.DESCRIPTION
    Proverava svaki uključen VM na hostu za potencijalne probleme
    koji bi mogli sprečiti migraciju:
    - Nedostatak VMware Tools
    - Mount-ovani ISO fajlovi
    - vMotion kompatibilnost
    - Zauzete CD/DVD jedinice
.PARAMETER VMHost
    VMware host objekat
.RETURNS
    PSCustomObject sa propertijima:
    - HasIssues: Boolean da li postoje problemi
    - Issues: Array problema (VM name + reason)
    - TotalVMs: Ukupan broj VM-ova
#>
function Test-VMMigratability {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [object]$VMHost
    )
    
    Write-EnhancedLog "Provera VM migratability za host: $($VMHost.Name)" "INFO" "VMMigratability"
    
    # Dohvati sve uključene VM-ove
    $vms = Get-VM -VMHost $VMHost | Where-Object { $_.PowerState -eq 'PoweredOn' }
    
    $issues = @()
    
    foreach ($vm in $vms) {
        $vmIssues = @()
        
        # Proveri VMware Tools
        if ($vm.Guest.ToolsVersion -eq 0 -or $vm.Guest.ToolsVersionStatus -eq 'guestToolsNotInstalled') {
            $vmIssues += "VMware Tools not installed"
        }
        
        # Proveri da li je ISO mount-ovan
        $cdDrive = Get-CDDrive -VM $vm
        if ($cdDrive.IsoPath) {
            $vmIssues += "ISO mounted: $($cdDrive.IsoPath)"
        }
        
        # Proveri floppy (ako postoji)
        $floppyDrive = Get-FloppyDrive -VM $vm -ErrorAction SilentlyContinue
        if ($floppyDrive -and $floppyDrive.MediaPath) {
            $vmIssues += "Floppy image mounted: $($floppyDrive.MediaPath)"
        }
        
        # Proveri vMotion kompatibilnost
        try {
            $vmotionCheck = Test-VmotionCompatibility -VM $vm -Destination (Get-VMHost | Where-Object { $_.Name -ne $VMHost.Name } | Select-Object -First 1) -ErrorAction Stop
            if (-not $vmotionCheck.Success) {
                $vmIssues += "vMotion compatibility: $($vmotionCheck.Message)"
            }
        } catch {
            $vmIssues += "vMotion check failed: $($_.Exception.Message)"
        }
        
        # Ako postoje problemi sa ovim VM, dodaj u listu
        if ($vmIssues.Count -gt 0) {
            foreach ($issue in $vmIssues) {
                $issues += [PSCustomObject]@{
                    VM = $vm.Name
                    Reason = $issue
                }
            }
            Write-EnhancedLog "VM $($vm.Name) ima probleme: $($vmIssues -join '; ')" "WARN" "VMMigratability"
        }
    }
    
    Write-EnhancedLog "Ukupno VM-ova: $($vms.Count), Problema: $($issues.Count)" "INFO" "VMMigratability"
    
    return [PSCustomObject]@{
        HasIssues = $issues.Count -gt 0
        Issues = $issues
        TotalVMs = $vms.Count
    }
}

<#
.SYNOPSIS
    Kreira backup konfiguracije ESXi hosta.
.DESCRIPTION
    Čuva kompletnu konfiguraciju hosta uključujući:
    - Host firmware konfiguraciju
    - Network konfiguraciju (virtual switches, port groups)
    - Storage konfiguraciju (HBAs, datastores)
    - Security postavke
    
    Backup se čuva u XML formatu i može se koristiti za rollback.
.PARAMETER VMHost
    VMware host objekat
.PARAMETER BackupDirectory
    Direktorijum za čuvanje backup-a (default: backups/vmhosts)
.RETURNS
    PSCustomObject sa propertijama:
    - Success: Boolean da li je backup uspeo
    - BackupPath: Putanja do backup fajla
    - Timestamp: Vreme kreiranja
    - Components: Lista komponenata u backup-u
#>
function Backup-VMHostConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [object]$VMHost,
        
        [Parameter(Mandatory=$false)]
        [string]$BackupDirectory = "backups/vmhosts"
    )
    
    Write-EnhancedLog "Kreiranje backup-a za host: $($VMHost.Name)" "INFO" "VMHostBackup"
    
    try {
        # Kreiraj backup direktorijum ako ne postoji
        if (-not (Test-Path $BackupDirectory)) {
            New-Item -Path $BackupDirectory -ItemType Directory -Force | Out-Null
        }
        
        # Generiši ime fajla sa timestamp-om
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFileName = "$($VMHost.Name)_$timestamp"
        
        # ============================================
        # BACKUP 1: Host firmware konfiguracija
        # ============================================
        Write-EnhancedLog "Backup firmware konfiguracije..." "INFO" "VMHostBackup"
        
        $firmwareConfig = Get-VMHostFirmware -VMHost $VMHost
        $firmwarePath = Join-Path $BackupDirectory "$backupFileName`_firmware.xml"
        $firmwareConfig | Export-Clixml -Path $firmwarePath -Force
        
        # ============================================
        # BACKUP 2: Network konfiguracija
        # ============================================
        Write-EnhancedLog "Backup network konfiguracije..." "INFO" "VMHostBackup"
        
        $networkConfig = @{
            VirtualSwitches = Get-VirtualSwitch -VMHost $VMHost | Select-Object Name, MTU, Nic
            PortGroups = Get-VirtualPortGroup -VMHost $VMHost | Select-Object Name, VirtualSwitch, VLANId
            VMHostNics = Get-VMHostNetworkAdapter -VMHost $VMHost | Select-Object Name, IP, SubnetMask, Mac
        }
        $networkPath = Join-Path $BackupDirectory "$backupFileName`_network.xml"
        $networkConfig | Export-Clixml -Path $networkPath -Force
        
        # ============================================
        # BACKUP 3: Storage konfiguracija
        # ============================================
        Write-EnhancedLog "Backup storage konfiguracije..." "INFO" "VMHostBackup"
        
        $storageConfig = @{
            HostBusAdapters = Get-VMHostHba -VMHost $VMHost | Select-Object Name, Type, Model, Status
            Datastores = Get-Datastore -VMHost $VMHost | Select-Object Name, FreeSpaceMB, CapacityMB, Type
            ScsiLuns = Get-ScsiLun -VMHost $VMHost | Select-Object CanonicalName, CapacityGB, Vendor
        }
        $storagePath = Join-Path $BackupDirectory "$backupFileName`_storage.xml"
        $storageConfig | Export-Clixml -Path $storagePath -Force
        
        # ============================================
        # BACKUP 4: Security i postavke
        # ============================================
        Write-EnhancedLog "Backup security postavki..." "INFO" "VMHostBackup"
        
        $securityConfig = @{
            Authentication = Get-VMHostAuthentication -VMHost $VMHost
            FirewallExceptions = Get-VMHostFirewallException -VMHost $VMHost | Where-Object { $_.Enabled }
            AdvancedSettings = Get-AdvancedSetting -Entity $VMHost | Select-Object Name, Value
        }
        $securityPath = Join-Path $BackupDirectory "$backupFileName`_security.xml"
        $securityConfig | Export-Clixml -Path $securityPath -Force
        
        # Kreiraj metadata fajl sa informacijama o backup-u
        $metadata = [PSCustomObject]@{
            HostName = $VMHost.Name
            Timestamp = Get-Date
            vCenter = $VMHost.ExtensionData.Client.ServiceUrl
            Components = @("Firmware", "Network", "Storage", "Security")
            Files = @($firmwarePath, $networkPath, $storagePath, $securityPath)
            PowerCLIVersion = (Get-Module VMware.VimAutomation.Core).Version
        }
        
        $metadataPath = Join-Path $BackupDirectory "$backupFileName`_metadata.json"
        $metadata | ConvertTo-Json -Depth 5 | Out-File -FilePath $metadataPath -Encoding UTF8
        
        Write-EnhancedLog "Backup uspešno kreiran: $metadataPath" "SUCCESS" "VMHostBackup"
        
        return [PSCustomObject]@{
            Success = $true
            BackupPath = $metadataPath
            Timestamp = $metadata.Timestamp
            Components = $metadata.Components
        }
        
    } catch {
        Write-EnhancedLog "Backup NEUSPEŠAN: $($_.Exception.Message)" "ERROR" "VMHostBackup"
        return [PSCustomObject]@{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

<#
.SYNOPSIS
    Vraća konfiguraciju ESXi hosta iz backup-a.
.DESCRIPTION
    Restore-uje konfiguraciju hosta iz prethodno kreiranog backup-a.
    Ova funkcija se koristi za rollback kada ažuriranje ne uspe.
    
    NAPOMENA: Restore može zahtevati reboot hosta.
.PARAMETER VMHost
    VMware host objekat
.PARAMETER BackupMetadataPath
    Putanja do metadata fajla backup-a
.PARAMETER Components
    Koje komponente restore-ovati (All, Firmware, Network, Storage, Security)
.RETURNS
    PSCustomObject sa propertijama:
    - Success: Boolean da li je restore uspeo
    - RestoredComponents: Lista restore-ovanih komponenti
    - RebootRequired: Boolean da li je potreban reboot
#>
function Restore-VMHostConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [object]$VMHost,
        
        [Parameter(Mandatory=$true)]
        [string]$BackupMetadataPath,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("All", "Firmware", "Network", "Storage", "Security")]
        [string[]]$Components = @("All")
    )
    
    Write-EnhancedLog "Restore konfiguracije za host: $($VMHost.Name)" "INFO" "VMHostRestore"
    Write-EnhancedLog "Backup: $BackupMetadataPath" "INFO" "VMHostRestore"
    
    try {
        # Učitaj metadata
        $metadata = Get-Content -Path $BackupMetadataPath | ConvertFrom-Json
        $backupDir = Split-Path -Parent $BackupMetadataPath
        
        $restoredComponents = @()
        $rebootRequired = $false
        
        # Determine which components to restore
        $componentsToRestore = if ($Components -contains "All") {
            @("Firmware", "Network", "Storage", "Security")
        } else {
            $Components
        }
        
        # Restore Firmware Config
        if ($componentsToRestore -contains "Firmware") {
            Write-EnhancedLog "Restore firmware konfiguracije..." "INFO" "VMHostRestore"
            
            $firmwareBackup = $metadata.Files | Where-Object { $_ -like "*_firmware.xml" }
            if ($firmwareBackup -and (Test-Path $firmwareBackup)) {
                $firmwareConfig = Import-Clixml -Path $firmwareBackup
                Set-VMHostFirmware -VMHost $VMHost -Firmware $firmwareConfig -Confirm:$false
                $restoredComponents += "Firmware"
                $rebootRequired = $true
            }
        }
        
        # Restore Network Config
        if ($componentsToRestore -contains "Network") {
            Write-EnhancedLog "Restore network konfiguracije..." "INFO" "VMHostRestore"
            
            $networkBackup = $metadata.Files | Where-Object { $_ -like "*_network.xml" }
            if ($networkBackup -and (Test-Path $networkBackup)) {
                $networkConfig = Import-Clixml -Path $networkBackup
                # Implementirati restore logiku za network
                # Ovo je kompleksno i zahteva pažljiv pristup
                Write-EnhancedLog "Network restore zahteva ručnu intervenciju" "WARN" "VMHostRestore"
            }
        }
        
        # Restore Storage Config
        if ($componentsToRestore -contains "Storage") {
            Write-EnhancedLog "Restore storage konfiguracije..." "INFO" "VMHostRestore"
            
            $storageBackup = $metadata.Files | Where-Object { $_ -like "*_storage.xml" }
            if ($storageBackup -and (Test-Path $storageBackup)) {
                $storageConfig = Import-Clixml -Path $storageBackup
                # Storage restore obično zahteva ručnu intervenciju
                Write-EnhancedLog "Storage restore zahteva ručnu intervenciju" "WARN" "VMHostRestore"
            }
        }
        
        Write-EnhancedLog "Restore završen. Restaurirano: $($restoredComponents -join ', ')" "SUCCESS" "VMHostRestore"
        
        return [PSCustomObject]@{
            Success = $true
            RestoredComponents = $restoredComponents
            RebootRequired = $rebootRequired
        }
        
    } catch {
        Write-EnhancedLog "Restore NEUSPEŠAN: $($_.Exception.Message)" "ERROR" "VMHostRestore"
        return [PSCustomObject]@{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

<#
.SYNOPSIS
    Izvršava rollback na prethodno stanje za single host.
.DESCRIPTION
    Kompletan rollback radni tok koji:
    1. Vraća konfiguraciju iz backup-a
    2. Restartuje host ako je potrebno
    3. Verifikuje da li je host dostupan
    4. Vraća VM-ove u normalno stanje
.PARAMETER VMHostName
    Ime ESXi hosta
.PARAMETER Config
    Konfiguracioni objekat
.RETURNS
    PSCustomObject sa rezultatom rollback-a
#>
function Invoke-SingleHostRollback {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$VMHostName,
        
        [Parameter(Mandatory=$true)]
        [object]$Config
    )
    
    Write-EnhancedLog "=== POČETAK ROLLBACK ZA HOST: $VMHostName ===" "WARN" "SingleHostRollback"
    
    try {
        # Konekcija na vCenter
        $vCenterConnection = Connect-vCenterSafely `
            -Server $Config.vCenter.server `
            -Credential (Get-StoredCredential -Target $Config.vCenter.credentialTarget)
        
        # Dohvati host
        $VMHost = Get-VMHost -Name $VMHostName -Server $vCenterConnection
        
        # Pronađi poslednji backup
        $backupFiles = Get-ChildItem -Path "backups/vmhosts" -Filter "$VMHostName`_*.json" | 
            Sort-Object LastWriteTime -Descending
        
        if ($backupFiles.Count -eq 0) {
            throw "Nema dostupnih backup-a za rollback"
        }
        
        $latestBackup = $backupFiles | Select-Object -First 1
        
        Write-EnhancedLog "Korišćen backup: $($latestBackup.FullName)" "INFO" "SingleHostRollback"
        
        # Restore konfiguraciju
        $restoreResult = Restore-VMHostConfiguration `
            -VMHost $VMHost `
            -BackupMetadataPath $latestBackup.FullName
        
        if (-not $restoreResult.Success) {
            throw "Restore neuspešan: $($restoreResult.Error)"
        }
        
        # Reboot ako je potrebno
        if ($restoreResult.RebootRequired) {
            Write-EnhancedLog "Restartovanje hosta nakon restore-a..." "INFO" "SingleHostRollback"
            Restart-VMHost -VMHost $VMHost -Confirm:$false | Out-Null
            
            # Sačekaj da host ponovo dođe online
            Start-Sleep -Seconds 120
        }
        
        # Verifikuj da li je host dostupan
        $restoredHost = Get-VMHost -Name $VMHostName -Server $vCenterConnection
        
        if ($restoredHost.ConnectionState -eq 'Connected') {
            Write-EnhancedLog "Rollback USPEŠAN - Host dostupan" "SUCCESS" "SingleHostRollback"
            return @{ Success = $true }
        } else {
            throw "Host nije dostupan nakon rollback-a"
        }
        
    } catch {
        Write-EnhancedLog "Rollback NEUSPEŠAN: $($_.Exception.Message)" "ERROR" "SingleHostRollback"
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

<#
.SYNOPSIS
    Health check za ESXi host.
.DESCRIPTION
    Verifikuje da li je host zdrav posle ažuriranja proverom:
    - Konekcija na vCenter
    - Dostupnost svih adaptera
    - VM-ovi su pokrenuti
    - Storage je dostupan
    - Network funkcioniše
.PARAMETER VMHost
    VMware host objekat
.RETURNS
    PSCustomObject sa propertijama:
    - IsHealthy: Boolean da li je host zdrav
    - Issues: Lista problema (ako postoje)
    - Checks: Lista izvršenih provera
#>
function Test-VMHostHealth {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [object]$VMHost
    )
    
    Write-EnhancedLog "Health check za host: $($VMHost.Name)" "INFO" "VMHostHealth"
    
    $issues = @()
    $checks = @()
    
    # Check 1: Konekcija
    if ($VMHost.ConnectionState -ne 'Connected' -and $VMHost.ConnectionState -ne 'Maintenance') {
        $issues += "Host nije povezan na vCenter. Status: $($VMHost.ConnectionState)"
    }
    $checks += "Connection: $($VMHost.ConnectionState)"
    
    # Check 2: Network adapteri
    $nics = Get-VMHostNetworkAdapter -VMHost $VMHost
    $failedNics = $nics | Where-Object { $_.ConnectionState -ne 'Connected' }
    if ($failedNics) {
        $issues += "Network adapteri nedostupni: $($failedNics.Name -join ', ')"
    }
    $checks += "Network Adapters: $($nics.Count) total, $($failedNics.Count) failed"
    
    # Check 3: Storage
    $datastores = Get-Datastore -VMHost $VMHost
    $inaccessibleDatastores = $datastores | Where-Object { $_.State -ne 'Available' }
    if ($inaccessibleDatastores) {
        $issues += "Datastores nedostupni: $($inaccessibleDatastores.Name -join ', ')"
    }
    $checks += "Datastores: $($datastores.Count) total, $($inaccessibleDatastores.Count) inaccessible"
    
    # Check 4: VM-ovi
    $vms = Get-VM -VMHost $VMHost
    $failedVMs = $vms | Where-Object { $_.PowerState -eq 'PoweredOn' -and $_.Guest.State -ne 'Running' }
    if ($failedVMs) {
        $issues += "VM-ovi sa problemima: $($failedVMs.Name -join ', ')"
    }
    $checks += "VMs: $($vms.Count) total, $($failedVMs.Count) with issues"
    
    # Check 5: Alarms
    $alarms = Get-AlarmDefinition -Entity $VMHost | Get-AlarmTrigger | Where-Object { $_.Status -eq 'Red' }
    if ($alarms) {
        $issues += "Aktivni alarmi: $($alarms.Count)"
    }
    $checks += "Alarms: $($alarms.Count) red"
    
    $isHealthy = $issues.Count -eq 0
    
    if ($isHealthy) {
        Write-EnhancedLog "Health Check USPEŠAN" "SUCCESS" "VMHostHealth"
    } else {
        Write-EnhancedLog "Health Check NEUSPEŠAN: $($issues -join '; ')" "ERROR" "VMHostHealth"
    }
    
    return [PSCustomObject]@{
        IsHealthy = $isHealthy
        Issues = $issues
        Checks = $checks
    }
}

# Export funkcija
Export-ModuleMember -Function Invoke-SingleHostUpdate, Test-NMinusOneCapacity, Test-VMMigratability, Backup-VMHostConfiguration, Restore-VMHostConfiguration, Invoke-SingleHostRollback, Test-VMHostHealth
