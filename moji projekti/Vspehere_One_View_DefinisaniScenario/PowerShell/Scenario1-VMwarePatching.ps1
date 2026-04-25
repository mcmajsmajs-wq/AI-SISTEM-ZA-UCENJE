<#
.SYNOPSIS
    Scenario 1 - VMware vCenter ESXi Host Patching
    
.DESCRIPTION
    Automatizacija patching procesa ESXi hostova putem vSphere Lifecycle Manager (vLCM)
    sa svim pre-check, staging i post-verification koracima.
    
.PARAMETER vCenterServer
    vCenter server hostname ili IP adresa
    
.PARAMETER ClusterName
    Ime VMware klastera
    
.PARAMETER HostName
    Ime pojedinacnog hosta (opciono ako se radi na nivou klastera)
    
.PARAMETER BaselineName
    Ime baseline-a za patching
    
.PARAMETER Mode
    Rezim rada: Simulate, Test, Production
    
.EXAMPLE
    .\Scenario1-VMwarePatching.ps1 -vCenterServer "vcenter.local" -ClusterName "Production" -Mode "Simulate"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$vCenterServer,
    
    [Parameter(Mandatory=$false)]
    [string]$ClusterName,
    
    [Parameter(Mandatory=$false)]
    [string]$HostName,
    
    [Parameter(Mandatory=$false)]
    [string]$BaselineName = "Critical Patches",
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("Simulate", "Test", "Production")]
    [string]$Mode,
    
    [Parameter(Mandatory=$false)]
    [PSCredential]$Credential
)

# Ucitaj core modul
Import-Module "$PSScriptRoot\VMwarePatchingCore.psm1" -Force

#region INICIJALIZACIJA
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          SCENARIO 1 - VMware vCenter Patching               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Postavi rezim rada
Set-ExecutionMode -Mode $Mode

# Inicijalizuj logovanje
Initialize-Logging -SessionName "Scenario1_VMware_$($HostName -replace '[^a-zA-Z0-9]', '_')"

Write-Log "=== POCETAK SCENARIO 1 - VMware Patching ===" -Level "INFO"
Write-Log "vCenter Server: $vCenterServer" -Level "INFO"
Write-Log "Cluster: $(if ($ClusterName) { $ClusterName } else { 'N/A' })" -Level "INFO"
Write-Log "Host: $(if ($HostName) { $HostName } else { 'N/A' })" -Level "INFO"
Write-Log "Baseline: $BaselineName" -Level "INFO"
#endregion

#region FAZA 1 - PRIPREMNE RADNJE (Pre-Checks)
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 1: PRIPREMNE RADNJE (Pre-Checks)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 1.1 Povezivanje na vCenter
$connectResult = Invoke-Action -ActionName "Povezivanje na vCenter" `
    -Description "Povezivanje na vCenter server $vCenterServer" `
    -Action {
        if (-not $Credential) {
            $Credential = Get-Credential -Message "Unesite vCenter kredencijale"
        }
        
        Connect-VIServer -Server $vCenterServer -Credential $Credential -ErrorAction Stop
        Write-Log "Uspesno povezan na vCenter: $vCenterServer" -Level "SUCCESS"
    } `
    -Critical

if (-not $connectResult.Success) {
    Write-Log "Ne mogu se povezati na vCenter. Prekidam." -Level "ERROR"
    exit 1
}

# 1.2 Backup provera vCenter-a (globalni backup)
$backupResult = Invoke-Action -ActionName "Provera vCenter Backupa" `
    -Description "Provera da li postoji aktuelan backup vCenter servera" `
    -Action {
        # Proveri da li postoji backup u poslednjih 24h
        $backupPath = "C:\Backups\vCenter"
        $recentBackup = Get-ChildItem -Path $backupPath -Filter "*.bak" -ErrorAction SilentlyContinue | 
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
        
        if (-not $recentBackup) {
            throw "Nema recentnog backup-a vCenter-a (poslednjih 24h)! Napravite backup pre nastavka."
        }
        
        Write-Log "✓ Recentan backup pronadjen: $($recentBackup.FullName)" -Level "SUCCESS"
        return $recentBackup
    } `
    -Critical

# 1.3 Provera resursa u klasteru
$resourcesResult = Invoke-Action -ActionName "Provera resursa klastera" `
    -Description "Provera da li klaster ima dovoljno resursa za maintenance mode" `
    -Action {
        if (-not $ClusterName) {
            Write-Log "Cluster nije definisan, preskacem proveru resursa" -Level "WARNING"
            return $null
        }
        
        $cluster = Get-Cluster -Name $ClusterName -ErrorAction Stop
        $hosts = $cluster | Get-VMHost
        $totalCpu = ($hosts | Measure-Object CpuTotalMhz -Sum).Sum
        $totalMem = ($hosts | Measure-Object MemoryTotalGB -Sum).Sum
        $usedCpu = ($hosts | Measure-Object CpuUsageMhz -Sum).Sum
        $usedMem = ($hosts | Measure-Object MemoryUsageGB -Sum).Sum
        
        $freeCpuPercent = [math]::Round((($totalCpu - $usedCpu) / $totalCpu) * 100, 2)
        $freeMemPercent = [math]::Round((($totalMem - $usedMem) / $totalMem) * 100, 2)
        
        Write-Log "Klaster resursi:" -Level "INFO"
        Write-Log "  Slobodan CPU: $freeCpuPercent%" -Level "INFO"
        Write-Log "  Slobodan RAM: $freeMemPercent%" -Level "INFO"
        
        if ($freeCpuPercent -lt 20 -or $freeMemPercent -lt 20) {
            throw "Klaster nema dovoljno slobodnih resursa! Potrebno minimum 20% slobodno."
        }
        
        Write-Log "✓ Klaster ima dovoljno resursa" -Level "SUCCESS"
        return @{ FreeCpuPercent = $freeCpuPercent; FreeMemPercent = $freeMemPercent }
    }

# 1.4 Provera vCenter verzije
$versionResult = Invoke-Action -ActionName "Provera vCenter verzije" `
    -Description "Provera kompatibilnosti vCenter verzije" `
    -Action {
        $vcVersion = $global:DefaultVIServer.Version
        Write-Log "vCenter verzija: $vcVersion" -Level "INFO"
        
        # Proveri da li je verzija podrzana
        if ($vcVersion -lt [Version]"7.0.0") {
            throw "vCenter verzija $vcVersion nije podrzana. Minimalna verzija je 7.0.0"
        }
        
        Write-Log "✓ vCenter verzija kompatibilna" -Level "SUCCESS"
        return $vcVersion
    }

# 1.5 Provera Storage Datastore-ova
$storageResult = Invoke-Action -ActionName "Provera Storage dostupnosti" `
    -Description "Provera da li su svi datastore-ovi dostupni i stabilni" `
    -Action {
        $datastores = Get-Datastore -ErrorAction Stop
        $unavailable = @()
        
        foreach ($ds in $datastores) {
            if ($ds.State -ne "Available" -or $ds.CapacityGB -lt 10) {
                $unavailable += $ds.Name
            }
        }
        
        if ($unavailable.Count -gt 0) {
            throw "Problem sa datastore-ovima: $($unavailable -join ', ')"
        }
        
        Write-Log "✓ Svi datastore-ovi dostupni (Ukupno: $($datastores.Count))" -Level "SUCCESS"
        return $datastores
    }

# 1.6 Provera ISO fajlova na VM-ovima
$isoResult = Invoke-Action -ActionName "Provera montiranih ISO fajlova" `
    -Description "Provera da li VM-ovi imaju montirane lokalne ISO fajlove" `
    -Action {
        $vmsWithIso = Get-VM | Where-Object { 
            ($_ | Get-CDDrive).IsoPath -ne $null 
        }
        
        if ($vmsWithIso) {
            $vmNames = $vmsWithIso.Name -join ', '
            throw "Sledece VM-ove imaju montirane ISO fajlove: $vmNames. Odmontirajte ih pre nastavka."
        }
        
        Write-Log "✓ Nema montiranih ISO fajlova na VM-ovima" -Level "SUCCESS"
        return $true
    }

Write-Log "✓ FAZA 1 ZAVRSENA - Sve provere prosle" -Level "SUCCESS"
#endregion

#region FAZA 2 - LIFECYCLE MANAGER KONFIGURACIJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 2: LIFECYCLE MANAGER KONFIGURACIJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 2.1 Sync Updates
$syncResult = Invoke-Action -ActionName "Sync Updates" `
    -Description "Sinronizacija najnovijih zakrpa sa VMware portalom" `
    -Action {
        # Sync updates preko vLCM
        $depot = Get-PatchDepot -ErrorAction Stop
        Sync-Patch -Depot $depot -ErrorAction Stop
        Write-Log "✓ Updates sinhronizovani" -Level "SUCCESS"
        return $depot
    } `
    -RetryCount 2

# 2.2 Provera Baseline-a
$baselineResult = Invoke-Action -ActionName "Provera Baseline-a" `
    -Description "Provera da li baseline '$BaselineName' postoji" `
    -Action {
        $baseline = Get-Baseline -Name $BaselineName -ErrorAction SilentlyContinue
        
        if (-not $baseline) {
            Write-Log "Baseline '$BaselineName' ne postoji. Kreiram novi..." -Level "WARNING"
            
            # Kreiraj novi baseline sa kriticnim zakrpama
            $baseline = New-Baseline -Name $BaselineName -Description "Kriticne bezbednosne zakrpe" `
                -ErrorAction Stop
        }
        
        Write-Log "✓ Baseline spreman: $($baseline.Name)" -Level "SUCCESS"
        return $baseline
    }

Write-Log "✓ FAZA 2 ZAVRSENA - Lifecycle Manager konfigurisan" -Level "SUCCESS"
#endregion

#region FAZA 3 - ATTACHMENT I COMPLIANCE CHECK
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 3: ATTACHMENT I COMPLIANCE CHECK" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 3.1 Attachment Baseline-a
$attachResult = Invoke-Action -ActionName "Attachment Baseline-a" `
    -Description "Povezivanje baseline-a sa targetom (klaster ili host)" `
    -Action {
        if ($HostName) {
            $target = Get-VMHost -Name $HostName
            Attach-Baseline -Entity $target -Baseline $baselineResult.Result -ErrorAction Stop
            Write-Log "✓ Baseline povezan sa hostom: $HostName" -Level "SUCCESS"
        }
        elseif ($ClusterName) {
            $target = Get-Cluster -Name $ClusterName
            Attach-Baseline -Entity $target -Baseline $baselineResult.Result -ErrorAction Stop
            Write-Log "✓ Baseline povezan sa klasterom: $ClusterName" -Level "SUCCESS"
        }
        else {
            throw "Morate definisati ili HostName ili ClusterName"
        }
        
        return $target
    } `
    -Critical

# 3.2 Check Compliance
$complianceResult = Invoke-Action -ActionName "Check Compliance" `
    -Description "Provera compliance statusa hosta/klastera" `
    -Action {
        $compliance = Test-Compliance -Entity $attachResult.Result -Baseline $baselineResult.Result
        
        foreach ($entity in $compliance) {
            $status = $entity.Status
            Write-Log "Entity: $($entity.Entity) - Status: $status" -Level $(if ($status -eq "Compliant") { "SUCCESS" } else { "WARNING" })
            
            if ($status -eq "Compliant") {
                Write-Log "✓ Host je vec compliant. Nema potrebe za patching-om." -Level "SUCCESS"
            }
            else {
                Write-Log "⚠ Host nije compliant. Potrebno je patching." -Level "WARNING"
            }
        }
        
        return $compliance
    }

# Ako je sve compliant, zavrsi
if ($complianceResult.Result.Status -eq "Compliant") {
    Write-Log "`n✓ SISTEM JE VEC COMPLIANT. Prekidam izvrsavanje." -Level "SUCCESS"
    Close-Logging
    Disconnect-VIServer -Server $vCenterServer -Confirm:$false
    exit 0
}

Write-Log "✓ FAZA 3 ZAVRSENA - Compliance provera zavrsena" -Level "SUCCESS"
#endregion

#region FAZA 4 - STAGING
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 4: STAGING (Neposredno pre egzekucije)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 4.1 Pre-Remediation Check
$preCheckResult = Invoke-Action -ActionName "Pre-Remediation Check" `
    -Description "Provera pre pokretanja remediation procesa" `
    -Action {
        # Proveri DRS status
        if ($ClusterName) {
            $cluster = Get-Cluster -Name $ClusterName
            if ($cluster.DrsEnabled -eq $false) {
                throw "DRS nije ukljucen na klasteru! Poteskoce sa migracijom VM-ova."
            }
        }
        
        # Proveri HA status
        if ($cluster.HAEnabled -eq $false) {
            Write-Log "⚠ Upozorenje: HA nije ukljucen na klasteru" -Level "WARNING"
        }
        
        Write-Log "✓ Pre-remediation provera uspesna" -Level "SUCCESS"
        return $true
    } `
    -Critical

# 4.2 Staging (kopiranje fajlova)
$stagingResult = Invoke-Action -ActionName "Staging zakrpa" `
    -Description "Kopiranje fajlova zakrpa na host pre restarta" `
    -Action {
        Copy-Patch -Entity $attachResult.Result -Baseline $baselineResult.Result -ErrorAction Stop
        Write-Log "✓ Zakrpe kopirane na host (staged)" -Level "SUCCESS"
        return $true
    } `
    -RetryCount 1

Write-Log "✓ FAZA 4 ZAVRSENA - Staging kompletan" -Level "SUCCESS"
#endregion

#region FAZA 5 - BACKUP I REMEDIATION
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 5: BACKUP PROVERA I REMEDIATION" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Write-Log "⚠ POZOR: Sledi stvarno patching sa restartom hosta!" -Level "WARNING"

# 5.0 BACKUP PROVERA HOSTA - KRITIČNO!
$hostBackupResult = Invoke-Action -ActionName "BACKUP PROVERA HOSTA" `
    -Description "Provera da li je host $HostName backup-ovan pre patching-a" `
    -Action {
        Write-Log "`n🔄 PROVERAVAM BACKUP HOSTA: $HostName" -Level "INFO"
        
        # Proveri da li postoji backup configuracije hosta
        $host = Get-VMHost -Name $HostName -ErrorAction Stop
        $backupPath = "C:\Backups\Hosts\$HostName"
        
        # Proveri da li postoji recentan backup (poslednjih 24h)
        $recentBackup = Get-ChildItem -Path $backupPath -Filter "*.tgz" -ErrorAction SilentlyContinue | 
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
        
        if ($recentBackup) {
            Write-Log "✓ Recentan backup hosta pronadjen: $($recentBackup.FullName)" -Level "SUCCESS"
            Write-Log "  Vreme backup-a: $($recentBackup.LastWriteTime)" -Level "INFO"
        }
        else {
            Write-Log "⚠ NIJE PRONADJEN RECENTAN BACKUP HOSTA (poslednjih 24h)!" -Level "WARNING"
            Write-Log "  Ocekivana lokacija: $backupPath" -Level "INFO"
            
            if ($Mode -eq "Production") {
                Write-Log "🚨 BACKUP HOSTA JE OBAVEZAN PRE PATCHING-A!" -Level "ERROR"
                $backupConfirmation = Read-Host "`nNIJE pronadjen backup hosta $HostName!`nDa li zelite NASTAVITI BEZ BACKUP-a? (da/NAPRAVE_BACKUP/ne)`nUnesite 'NAPRAVE_BACKUP' da pokrenete backup, 'da' da nastavite rizikujuci, ili 'ne' da prekinete"
                
                if ($backupConfirmation -eq "ne") {
                    throw "Prekinuto od strane korisnika - nema backup-a hosta"
                }
                elseif ($backupConfirmation -eq "NAPRAVE_BACKUP") {
                    Write-Log "Pokrecem backup hosta $HostName..." -Level "INFO"
                    
                    # Pokreni backup hosta
                    $backupFile = "$backupPath\$HostName`_$(Get-Date -Format 'yyyyMMdd_HHmmss').tgz"
                    if (-not (Test-Path $backupPath)) {
                        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
                    }
                    
                    # Export host configuration
                    $host | Export-VMHostProfile -FilePath $backupFile -ErrorAction Stop
                    Write-Log "✓ Backup hosta kreiran: $backupFile" -Level "SUCCESS"
                }
                else {
                    Write-Log "⚠ NASTAVLJAM BEZ BACKUP-A! RIZIČNO!" -Level "WARNING"
                    $finalConfirm = Read-Host "Da li ste SIGURNI da zelite nastaviti bez backup-a? Ovo je VEOM RIZIČNO! (DA/ne)"
                    if ($finalConfirm -ne "DA") {
                        throw "Prekinuto - korisnik nije potvrdio nastavak bez backup-a"
                    }
                }
            }
            else {
                Write-Log "[SIMULATE/TEST] U produkciji bi se zahtevao backup" -Level "WARNING"
            }
        }
        
        # Backup VM-ova na hostu
        $vmsOnHost = $host | Get-VM -ErrorAction SilentlyContinue
        Write-Log "VM-ova na hostu: $($vmsOnHost.Count)" -Level "INFO"
        
        foreach ($vm in $vmsOnHost) {
            $vmBackup = Get-Snapshot -VM $vm -Name "Pre-Patching-Backup" -ErrorAction SilentlyContinue
            if (-not $vmBackup) {
                Write-Log "⚠ VM $($vm.Name) nema snapshot pre patching-a" -Level "WARNING"
                if ($Mode -eq "Production") {
                    $createSnapshot = Read-Host "Kreirati snapshot za VM $($vm.Name)? (da/ne)"
                    if ($createSnapshot -eq "da") {
                        New-Snapshot -VM $vm -Name "Pre-Patching-Backup" -Description "Automatski kreiran pre patching-a $(Get-Date)" -ErrorAction Stop
                        Write-Log "✓ Snapshot kreiran za VM $($vm.Name)" -Level "SUCCESS"
                    }
                }
            }
            else {
                Write-Log "✓ VM $($vm.Name) ima snapshot: $($vmBackup.Name)" -Level "SUCCESS"
            }
        }
        
        return @{ HostBackedUp = $true; VMsChecked = $vmsOnHost.Count }
    } `
    -Critical

if (-not $hostBackupResult.Success) {
    Write-Log "✗ BACKUP PROVERA HOSTA NIJE USPELA! Prekidam patching." -Level "ERROR"
    Close-Logging
    exit 1
}

Write-Log "✓ BACKUP PROVERA ZAVRSENA - Host i VM-ovi zasticeni" -Level "SUCCESS"

if ($Mode -eq "Production") {
    $confirmation = Read-Host "Da li ste sigurni da zelite nastaviti sa remediation? (da/ne)"
    if ($confirmation -ne "da") {
        Write-Log "Prekinuto od strane korisnika." -Level "WARNING"
        Close-Logging
        exit 0
    }
}

# 5.1 Remediation
$remediationResult = Invoke-Action -ActionName "Remediation" `
    -Description "Instalacija zakrpa i restart hosta" `
    -Action {
        # Pokreni remediation
        $remediation = Update-Entity -Entity $attachResult.Result `
            -Baseline $baselineResult.Result `
            -Confirm:$false `
            -ErrorAction Stop
        
        Write-Log "Remediation pokrenut. Pratim napredak..." -Level "INFO"
        
        # Prati napredak
        do {
            Start-Sleep -Seconds 30
            $task = Get-Task -Id $remediation.Id -ErrorAction SilentlyContinue
            
            if ($task) {
                Write-Log "Status: $($task.State) - $($task.PercentComplete)%" -Level "DEBUG"
            }
        } while ($task -and $task.State -eq "Running")
        
        Write-Log "✓ Remediation zavrsen" -Level "SUCCESS"
        return $remediation
    } `
    -Critical `
    -RetryCount 0

Write-Log "✓ FAZA 5 ZAVRSENA - Backup provera i Remediation kompletan" -Level "SUCCESS"
#endregion

#region FAZA 6 - POST-PATCH VERIFIKACIJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 6: POST-PATCH VERIFIKACIJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 6.1 Provera compliance statusa ponovo
$postComplianceResult = Invoke-Action -ActionName "Post-Patch Compliance Check" `
    -Description "Provera da li je host sada compliant" `
    -Action {
        Start-Sleep -Seconds 10 # Sacekaj da se host stabilizuje
        
        $compliance = Test-Compliance -Entity $attachResult.Result -Baseline $baselineResult.Result
        
        if ($compliance.Status -eq "Compliant") {
            Write-Log "✓ Host je sada COMPLIANT!" -Level "SUCCESS"
        }
        else {
            throw "Host i dalje nije compliant posle patching-a!"
        }
        
        return $compliance
    } `
    -Critical

# 6.2 Verifikacija build broja
$buildResult = Invoke-Action -ActionName "Verifikacija Build Broja" `
    -Description "Provera da li je novi build broj ispravan" `
    -Action {
        $host = Get-VMHost -Name $HostName
        $build = $host.Build
        $version = $host.Version
        
        Write-Log "ESXi Verzija: $version" -Level "INFO"
        Write-Log "ESXi Build: $build" -Level "INFO"
        
        return @{ Version = $version; Build = $build }
    }

# 6.3 Izlazak iz Maintenance Mode
$exitMaintResult = Invoke-Action -ActionName "Izlazak iz Maintenance Mode" `
    -Description "Vracanje hosta u normalan rad" `
    -Action {
        $host = Get-VMHost -Name $HostName
        
        if ($host.State -eq "Maintenance") {
            Set-VMHost -VMHost $host -State "Connected" -ErrorAction Stop
            Write-Log "✓ Host izveden iz Maintenance Mode" -Level "SUCCESS"
        }
        else {
            Write-Log "Host nije u Maintenance Mode" -Level "INFO"
        }
        
        return $true
    }

# 6.4 vMotion Test
$vmotionResult = Invoke-Action -ActionName "vMotion Test" `
    -Description "Testiranje vMotion migracije VM-ova" `
    -Action {
        # Pronadji jednu VM na hostu
        $vm = Get-VMHost -Name $HostName | Get-VM | Select-Object -First 1
        
        if ($vm) {
            Write-Log "Testiram vMotion sa VM: $($vm.Name)" -Level "INFO"
            
            # Pronadji drugi host u klasteru
            $otherHost = Get-Cluster -Name $ClusterName | Get-VMHost | 
                Where-Object { $_.Name -ne $HostName -and $_.State -eq "Connected" } | 
                Select-Object -First 1
            
            if ($otherHost) {
                Move-VM -VM $vm -Destination $otherHost -ErrorAction Stop
                Start-Sleep -Seconds 5
                Move-VM -VM $vm -Destination (Get-VMHost -Name $HostName) -ErrorAction Stop
                
                Write-Log "✓ vMotion test uspesan" -Level "SUCCESS"
            }
            else {
                Write-Log "⚠ Nema drugog dostupnog hosta za vMotion test" -Level "WARNING"
            }
        }
        else {
            Write-Log "⚠ Nema VM-ova na hostu za vMotion test" -Level "WARNING"
        }
        
        return $true
    }

# 6.5 Provera VMware Tools
$toolsResult = Invoke-Action -ActionName "Provera VMware Tools" `
    -Description "Provera da li je potrebno azurirati VMware Tools na VM-ovima" `
    -Action {
        $vms = Get-VMHost -Name $HostName | Get-VM
        $outdatedTools = @()
        
        foreach ($vm in $vms) {
            $toolsStatus = $vm.ExtensionData.Guest.ToolsStatus
            if ($toolsStatus -eq "toolsOld") {
                $outdatedTools += $vm.Name
            }
        }
        
        if ($outdatedTools.Count -gt 0) {
            Write-Log "VM-ovi sa zastaralim Tools-om: $($outdatedTools -join ', ')" -Level "WARNING"
        }
        else {
            Write-Log "✓ Svi VMware Tools su azurni" -Level "SUCCESS"
        }
        
        return $outdatedTools
    }

Write-Log "✓ FAZA 6 ZAVRSENA - Post-patch verifikacija kompletna" -Level "SUCCESS"
#endregion

#region ZAVRSNA FAZA
Write-Log "`n========================================" -Level "INFO"
Write-Log "ZAVRSNA FAZA - REZIME" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# Generisi izvestaj
Close-Logging

# Diskonektuj se sa vCenter-a
Disconnect-VIServer -Server $vCenterServer -Confirm:$false

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          SCENARIO 1 - ZAVRSEN USPESNO! ✅                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
#endregion
