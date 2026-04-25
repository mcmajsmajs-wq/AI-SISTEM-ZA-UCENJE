<#
.SYNOPSIS
    Scenario 4 - Host-by-Host Patching u VMware Klasteru
    
.DESCRIPTION
    Redovito patching svakog hosta u VMware klasteru po scenariju 1 i 2
    sa svim definisanim koracima kao jedna kompletna celina.
    
.PARAMETER vCenterServer
    vCenter server hostname
    
.PARAMETER OneViewServer
    HP OneView server hostname
    
.PARAMETER ClusterName
    Ime VMware klastera
    
.PARAMETER Mode
    Rezim rada: Simulate, Test, Production
    
.PARAMETER BatchSize
    Broj hostova koji se procesiraju istovremeno (default: 1)
    
.EXAMPLE
    .\Scenario4-ClusterPatching.ps1 -vCenterServer "vc.local" -OneViewServer "ov.local" -ClusterName "Production" -Mode "Simulate"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$vCenterServer,
    
    [Parameter(Mandatory=$true)]
    [string]$OneViewServer,
    
    [Parameter(Mandatory=$true)]
    [string]$ClusterName,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("Simulate", "Test", "Production")]
    [string]$Mode,
    
    [Parameter(Mandatory=$false)]
    [int]$BatchSize = 1
)

# Ucitaj core modul
Import-Module "$PSScriptRoot\VMwarePatchingCore.psm1" -Force

#region INICIJALIZACIJA
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   SCENARIO 4 - Host-by-Host Cluster Patching                ║
║                                                              ║
║   Klaster: $ClusterName
║   Rezim: $Mode
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Set-ExecutionMode -Mode $Mode
Initialize-Logging -SessionName "Scenario4_Cluster_$($ClusterName -replace '[^a-zA-Z0-9]', '_')"

Write-Log "=== POCETAK SCENARIO 4 - CLUSTER PATCHING ===" -Level "INFO"
Write-Log "vCenter: $vCenterServer" -Level "INFO"
Write-Log "OneView: $OneViewServer" -Level "INFO"
Write-Log "Klaster: $ClusterName" -Level "INFO"
Write-Log "Batch Size: $BatchSize" -Level "INFO"
#endregion

#region FAZA 1 - PRIPREMA I PRIKUPLJANJE INFORMACIJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 1: PRIPREMA I PRIKUPLJANJE INFORMACIJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# Povezivanje na vCenter
$connectResult = Invoke-Action -ActionName "Povezivanje na vCenter" `
    -Description "Povezivanje na vCenter server" `
    -Action {
        $Credential = Get-Credential -Message "Unesite vCenter kredencijale"
        Connect-VIServer -Server $vCenterServer -Credential $Credential -ErrorAction Stop
        Write-Log "Uspesno povezan na vCenter" -Level "SUCCESS"
    } `
    -Critical

# Prikupi listu svih hostova u klasteru
$hostsResult = Invoke-Action -ActionName "Prikupljanje liste hostova" `
    -Description "Prikupi sve hostove iz klastera $ClusterName" `
    -Action {
        $cluster = Get-Cluster -Name $ClusterName -ErrorAction Stop
        $hosts = $cluster | Get-VMHost | Where-Object { $_.ConnectionState -eq "Connected" }
        
        Write-Log "Pronadjeno hostova u klasteru: $($hosts.Count)" -Level "INFO"
        
        foreach ($h in $hosts) {
            Write-Log "  - $($h.Name) (Ver: $($h.Version), Build: $($h.Build))" -Level "INFO"
        }
        
        return $hosts
    } `
    -Critical

$hostsToProcess = $hostsResult.Result
$totalHosts = $hostsToProcess.Count
$processedHosts = 0
$successHosts = 0
$failedHosts = 0

Write-Log "✓ FAZA 1 ZAVRSENA - Prikupio listu od $totalHosts hostova" -Level "SUCCESS"
#endregion

#region FAZA 2 - PROCESIRANJE HOSTOVA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 2: PROCESIRANJE HOSTOVA ($totalHosts ukupno)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# Procesiraj hostove po jedan (ili u batch-ovima ako je BatchSize > 1)
for ($i = 0; $i -lt $totalHosts; $i += $BatchSize) {
    $batch = $hostsToProcess[$i..([Math]::Min($i + $BatchSize - 1, $totalHosts - 1))]
    $batchNumber = [Math]::Floor($i / $BatchSize) + 1
    $totalBatches = [Math]::Ceiling($totalHosts / $BatchSize)
    
    Write-Log "`n========================================" -Level "INFO"
    Write-Log "BATCH $batchNumber od $totalBatches" -Level "INFO"
    Write-Log "========================================" -Level "INFO"
    
    foreach ($vmHost in $batch) {
        $processedHosts++
        $hostName = $vmHost.Name
        
        Write-Log "`n" -Level "INFO" -NoConsole
        Write-Log "╔══════════════════════════════════════════════════════════════╗" -Level "INFO"
        Write-Log "║  Host $processedHosts od $totalHosts`: $hostName" -Level "INFO"
        Write-Log "╚══════════════════════════════════════════════════════════════╝" -Level "INFO"
        
        # Pronadji odgovarajuci Server Profile u OneView
        # Pretpostavka: ime hosta u vCenter odgovara imenu u OneView
        $serverProfileName = $hostName
        
        Write-Log "Mapiranje: vCenter Host '$hostName' -> OneView Profile '$serverProfileName'" -Level "INFO"
        
        # KRITIČNO: Provera backup-a hosta pre patching-a
        Write-Log "`n🔄 KRITIČNA PROVERA: Backup hosta $hostName" -Level "WARNING"
        $hostBackupCheck = Invoke-Action -ActionName "Backup provera hosta $hostName" `
            -Description "Provera da li je host backup-ovan pre patching-a" `
            -Action {
                $host = Get-VMHost -Name $hostName -ErrorAction Stop
                $backupPath = "C:\Backups\Hosts\$hostName"
                
                # Proveri recentan backup (poslednjih 24h)
                $recentBackup = Get-ChildItem -Path $backupPath -Filter "*.tgz" -ErrorAction SilentlyContinue | 
                    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
                
                if ($recentBackup) {
                    Write-Log "✓ Host $hostName ima recentan backup: $($recentBackup.Name)" -Level "SUCCESS"
                }
                else {
                    Write-Log "⚠ Host $hostName NEMA recentan backup!" -Level "WARNING"
                    
                    if ($Mode -eq "Production") {
                        Write-Log "🚨 BACKUP JE OBAVEZAN!" -Level "ERROR"
                        $backupChoice = Read-Host "Izaberite: [1] Napravi backup sada  [2] Preskoci ovog hosta  [3] Prekini sve"
                        
                        switch ($backupChoice) {
                            "1" {
                                Write-Log "Kreiram backup za host $hostName..." -Level "INFO"
                                $backupFile = "$backupPath\$hostName`_$(Get-Date -Format 'yyyyMMdd_HHmmss').tgz"
                                if (-not (Test-Path $backupPath)) {
                                    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
                                }
                                $host | Export-VMHostProfile -FilePath $backupFile -ErrorAction Stop
                                Write-Log "✓ Backup kreiran: $backupFile" -Level "SUCCESS"
                            }
                            "2" {
                                Write-Log "Preskacem host $hostName zbog nedostatka backup-a" -Level "WARNING"
                                throw "Host preskočen - nema backup"
                            }
                            default {
                                throw "Prekinuto od strane korisnika"
                            }
                        }
                    }
                }
                
                # Proveri snapshot-e VM-ova
                $vms = $host | Get-VM
                foreach ($vm in $vms) {
                    $snapshot = Get-Snapshot -VM $vm -Name "Pre-Patching-Backup" -ErrorAction SilentlyContinue
                    if (-not $snapshot) {
                        Write-Log "  ⚠ VM $($vm.Name) nema pre-patching snapshot" -Level "WARNING"
                    }
                }
                
                return $true
            }
        
        if (-not $hostBackupCheck.Success) {
            Write-Log "✗ Host $hostName preskočen zbog problema sa backup-om" -Level "WARNING"
            $failedHosts++
            continue
        }
        
        try {
            # Pokreni Scenario 3 (kombinovani patching) za ovaj host
            $scenario3Params = @{
                vCenterServer = $vCenterServer
                OneViewServer = $OneViewServer
                HostName = $hostName
                ServerProfileName = $serverProfileName
                Mode = $Mode
            }
            
            Write-Log "Pokrecem Scenario 3 za host: $hostName" -Level "INFO"
            
            if ($Mode -eq "Simulate") {
                Write-Log "[SIMULACIJA] Scenario 3 bi bio pokrenut sa parametrima:" -Level "WARNING"
                $scenario3Params.GetEnumerator() | ForEach-Object {
                    Write-Log "  $($_.Key) = $($_.Value)" -Level "WARNING"
                }
                $successHosts++
            }
            else {
                & "$PSScriptRoot\Scenario3-CombinedPatching.ps1" @scenario3Params
                $successHosts++
                Write-Log "✓ Host $hostName uspesno procesiran" -Level "SUCCESS"
            }
        }
        catch {
            $failedHosts++
            Write-Log "✗ Host $hostName nije uspeo: $_" -Level "ERROR"
            
            # Pitanje da li nastaviti sa sledecim hostom
            if ($Mode -eq "Production") {
                $continue = Read-Host "Host $hostName nije uspeo. Nastaviti sa sledecim? (da/ne)"
                if ($continue -ne "da") {
                    Write-Log "Prekinuto od strane korisnika." -Level "WARNING"
                    break
                }
            }
        }
    }
    
    # Pauza izmedju batch-eva ako ih ima vise
    if ($batchNumber -lt $totalBatches) {
        Write-Log "`nPauza pre sledeceg batch-a..." -Level "INFO"
        Start-Sleep -Seconds 10
    }
}

Write-Log "✓ FAZA 2 ZAVRSENA - Svi hostovi procesirani" -Level "SUCCESS"
#endregion

#region FAZA 3 - FINALNA PROVERA KLASTER
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 3: FINALNA PROVERA KLASTER STATUSA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

$finalCheckResult = Invoke-Action -ActionName "Finalna provera klastera" `
    -Description "Provera da li je ceo klaster zdrav posle patching-a" `
    -Action {
        $cluster = Get-Cluster -Name $ClusterName -ErrorAction Stop
        $hosts = $cluster | Get-VMHost
        
        Write-Log "Status klastera '$ClusterName' posle patching-a:" -Level "INFO"
        
        foreach ($h in $hosts) {
            $status = if ($h.ConnectionState -eq "Connected") { "✓ OK" } else { "✗ $($h.ConnectionState)" }
            Write-Log "  $status - $($h.Name) (Ver: $($h.Version))" -Level $(if ($h.ConnectionState -eq "Connected") { "SUCCESS" } else { "WARNING" })
        }
        
        # Proveri DRS i HA status
        Write-Log "DRS Status: $(if ($cluster.DrsEnabled) { "Ukljucen" } else { "Iskljucen" })" -Level "INFO"
        Write-Log "HA Status: $(if ($cluster.HAEnabled) { "Ukljucen" } else { "Iskljucen" })" -Level "INFO"
        
        return $cluster
    }

Write-Log "✓ FAZA 3 ZAVRSENA - Finalna provera kompletna" -Level "SUCCESS"
#endregion

#region ZAVRSNA FAZA
Write-Log "`n========================================" -Level "INFO"
Write-Log "ZAVRSNA FAZA - REZIME CLUSTER PATCHING-A" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Write-Log "`nSTATISTIKA:" -Level "INFO"
Write-Log "  Ukupno hostova: $totalHosts" -Level "INFO"
Write-Log "  Uspesno: $successHosts" -Level "SUCCESS"
Write-Log "  Neuspesno: $failedHosts" -Level $(if ($failedHosts -gt 0) { "ERROR" } else { "SUCCESS" })
Write-Log "  Procenat uspeha: $([math]::Round(($successHosts/$totalHosts)*100, 2))%" -Level "INFO"

# Generisi izvestaj
Close-Logging

# Diskonektuj se
Disconnect-VIServer -Server $vCenterServer -Confirm:$false

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     SCENARIO 4 - CLUSTER PATCHING ZAVRSEN! ✅               ║
║                                                              ║
║     Klaster: $ClusterName
║     Ukupno: $totalHosts hostova
║     Uspesno: $successHosts
║     Neuspesno: $failedHosts
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor $(if ($failedHosts -eq 0) { "Green" } else { "Yellow" })
#endregion
