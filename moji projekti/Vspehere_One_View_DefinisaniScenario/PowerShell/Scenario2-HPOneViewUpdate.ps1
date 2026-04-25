<#
.SYNOPSIS
    Scenario 2 - HP OneView Firmware Update
    
.DESCRIPTION
    Automatizacija firmware update procesa na HP OneView appliance
    za server profile i server profile templates.
    
.PARAMETER OneViewServer
    HP OneView server hostname ili IP adresa
    
.PARAMETER ServerProfileName
    Ime server profila koji se azurira
    
.PARAMETER SPPVersion
    Verzija HPE Service Pack for ProLiant (npr. "2023.09.0")
    
.PARAMETER UpdatePolicy
    Politika azuriranja: "FirmwareOnly" ili "FirmwareAndDrivers"
    
.PARAMETER Mode
    Rezim rada: Simulate, Test, Production
    
.EXAMPLE
    .\Scenario2-HPOneViewUpdate.ps1 -OneViewServer "oneview.local" -ServerProfileName "ESXi-Host-01" -Mode "Simulate"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$OneViewServer,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerProfileName,
    
    [Parameter(Mandatory=$false)]
    [string]$SPPVersion = "2023.09.0",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("FirmwareOnly", "FirmwareAndDrivers")]
    [string]$UpdatePolicy = "FirmwareOnly",
    
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
║        SCENARIO 2 - HP OneView Firmware Update              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Postavi rezim rada
Set-ExecutionMode -Mode $Mode

# Inicijalizuj logovanje
Initialize-Logging -SessionName "Scenario2_HPOneView_$($ServerProfileName -replace '[^a-zA-Z0-9]', '_')"

Write-Log "=== POCETAK SCENARIO 2 - HP OneView Firmware Update ===" -Level "INFO"
Write-Log "OneView Server: $OneViewServer" -Level "INFO"
Write-Log "Server Profile: $ServerProfileName" -Level "INFO"
Write-Log "SPP Version: $SPPVersion" -Level "INFO"
Write-Log "Update Policy: $UpdatePolicy" -Level "INFO"
#endregion

#region FAZA 1 - POVEZIVANJE I PROVERA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 1: POVEZIVANJE I INICIJALNA PROVERA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 1.1 Povezivanje na OneView
$connectResult = Invoke-Action -ActionName "Povezivanje na OneView" `
    -Description "Povezivanje na HP OneView appliance" `
    -Action {
        if (-not $Credential) {
            $Credential = Get-Credential -Message "Unesite OneView kredencijale"
        }
        
        # Ucitaj HPE OneView modul ako nije ucitan
        if (-not (Get-Module -Name HPEOneView.660 -ErrorAction SilentlyContinue)) {
            Import-Module HPEOneView.660 -ErrorAction Stop
        }
        
        Connect-OVMgmt -Hostname $OneViewServer -Credential $Credential -ErrorAction Stop
        Write-Log "Uspesno povezan na OneView: $OneViewServer" -Level "SUCCESS"
    } `
    -Critical

if (-not $connectResult.Success) {
    Write-Log "Ne mogu se povezati na OneView. Prekidam." -Level "ERROR"
    exit 1
}

# 1.2 Provera Server Profila
$profileResult = Invoke-Action -ActionName "Provera Server Profila" `
    -Description "Provera da li server profil postoji i njegovog statusa" `
    -Action {
        $profile = Get-OVServerProfile -Name $ServerProfileName -ErrorAction Stop
        
        if (-not $profile) {
            throw "Server profil '$ServerProfileName' nije pronadjen!"
        }
        
        Write-Log "✓ Server profil pronadjen: $($profile.name)" -Level "SUCCESS"
        Write-Log "  Status: $($profile.status)" -Level "INFO"
        Write-Log "  Compliance: $($profile.templateCompliance)" -Level "INFO"
        Write-Log "  Associated Server: $($profile.serverHardwareUri)" -Level "INFO"
        
        return $profile
    } `
    -Critical

# 1.3 Provera da li je server u Maintenance Mode
$maintenanceResult = Invoke-Action -ActionName "Provera Maintenance Mode" `
    -Description "Provera da li je fizicki server u maintenance modu" `
    -Action {
        $server = Get-OVServer -Name $ServerProfileName -ErrorAction SilentlyContinue
        
        if ($server) {
            $powerState = $server.powerState
            Write-Log "Server Power State: $powerState" -Level "INFO"
            
            if ($powerState -eq "On") {
                Write-Log "⚠ Server je ukljucen. Preporucuje se iskljuciti pre firmware update-a" -Level "WARNING"
                
                if ($Mode -eq "Production") {
                    $confirmation = Read-Host "Server je ukljucen. Da li zelite iskljuciti server pre nastavka? (da/ne)"
                    if ($confirmation -eq "da") {
                        Write-Log "Iskljucujem server..." -Level "INFO"
                        Stop-OVServer -Server $server -Force -ErrorAction Stop
                        Write-Log "✓ Server iskljucen" -Level "SUCCESS"
                    }
                }
            }
        }
        
        return $server
    }

Write-Log "✓ FAZA 1 ZAVRSENA - Povezivanje i provera uspesna" -Level "SUCCESS"
#endregion

#region FAZA 2 - FIRMWARE REPOSITORY PROVERA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 2: FIRMWARE REPOSITORY PROVERA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 2.1 Provera Firmware Bundles
$firmwareResult = Invoke-Action -ActionName "Provera Firmware Bundles" `
    -Description "Provera da li je SPP vec upload-ovan u OneView" `
    -Action {
        $firmwareBundles = Get-OVFirmwareBundle -ErrorAction Stop
        $targetSPP = $firmwareBundles | Where-Object { $_.version -like "*$SPPVersion*" }
        
        if ($targetSPP) {
            Write-Log "✓ SPP verzija $SPPVersion pronadjena u repository-ju" -Level "SUCCESS"
            Write-Log "  Bundle Name: $($targetSPP.name)" -Level "INFO"
            Write-Log "  Version: $($targetSPP.version)" -Level "INFO"
        }
        else {
            Write-Log "⚠ SPP verzija $SPPVersion NIJE pronadjena u repository-ju!" -Level "WARNING"
            Write-Log "  Dostupne verzije:" -Level "INFO"
            $firmwareBundles | ForEach-Object { Write-Log "    - $($_.version)" -Level "INFO" }
            
            throw "SPP $SPPVersion nije dostupan. Molim upload-ujte ga u Settings -> Firmware Bundles"
        }
        
        return $targetSPP
    } `
    -Critical

Write-Log "✓ FAZA 2 ZAVRSENA - Firmware provera kompletna" -Level "SUCCESS"
#endregion

#region FAZA 3 - SERVER PROFILE TEMPLATE AZURIRANJE
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 3: SERVER PROFILE TEMPLATE AZURIRANJE" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 3.1 Pronalazenje Server Profile Template-a
$templateResult = Invoke-Action -ActionName "Pronalazenje Server Profile Template-a" `
    -Description "Pronalazenje SPT-a povezanog sa server profilom" `
    -Action {
        $profile = $profileResult.Result
        
        if ($profile.serverProfileTemplateUri) {
            $templateUri = $profile.serverProfileTemplateUri
            $templateName = ($templateUri -split '/')[-1]
            
            $template = Get-OVServerProfileTemplate -Name $templateName -ErrorAction Stop
            Write-Log "✓ Server Profile Template pronadjen: $($template.name)" -Level "SUCCESS"
        }
        else {
            Write-Log "⚠ Server profil nema povezan template. Koristicemo direktno profil." -Level "WARNING"
            $template = $null
        }
        
        return $template
    }

# 3.2 Azuriranje Template-a sa novim Firmware-om
if ($templateResult.Result) {
    $updateTemplateResult = Invoke-Action -ActionName "Azuriranje Server Profile Template-a" `
        -Description "Postavljanje novog firmware baseline-a na template" `
        -Action {
            $template = $templateResult.Result
            $firmwareBundle = $firmwareResult.Result
            
            # Azuriraj firmware na template-u
            $template.firmware = @{
                firmwareBaselineUri = $firmwareBundle.uri
                manageFirmware = $true
                firmwareInstallType = if ($UpdatePolicy -eq "FirmwareAndDrivers") { "FirmwareAndSoftware" } else { "FirmwareOnly" }
                forceInstallFirmware = $false
            }
            
            if ($Mode -ne "Simulate") {
                Save-OVServerProfileTemplate -InputObject $template -ErrorAction Stop
                Write-Log "✓ Server Profile Template azuriran sa novim firmware-om" -Level "SUCCESS"
            }
            else {
                Write-Log "[SIMULACIJA] Template bi bio azuriran sa: $($firmwareBundle.version)" -Level "WARNING"
            }
            
            return $template
        }
}

Write-Log "✓ FAZA 3 ZAVRSENA - Template azuriranje kompletno" -Level "SUCCESS"
#endregion

#region FAZA 4 - UPDATE FROM TEMPLATE
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 4: UPDATE FROM TEMPLATE" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 4.1 Provera Consistency Status-a
$consistencyResult = Invoke-Action -ActionName "Provera Consistency Status-a" `
    -Description "Provera da li profil odstupa od template-a" `
    -Action {
        $profile = Get-OVServerProfile -Name $ServerProfileName -ErrorAction Stop
        
        if ($profile.templateCompliance -eq "Compliant") {
            Write-Log "✓ Server profil je compliant sa template-om" -Level "SUCCESS"
            Write-Log "Nema potrebe za update-om." -Level "INFO"
            return @{ NeedsUpdate = $false; Profile = $profile }
        }
        else {
            Write-Log "⚠ Server profil NIJE compliant sa template-om" -Level "WARNING"
            Write-Log "Status: $($profile.templateCompliance)" -Level "WARNING"
            return @{ NeedsUpdate = $true; Profile = $profile }
        }
    }

# 4.2 Update from Template
if ($consistencyResult.Result.NeedsUpdate -or $Mode -eq "Simulate") {
    $updateResult = Invoke-Action -ActionName "Update from Template" `
        -Description "Azuriranje server profila iz template-a" `
        -Action {
            $profile = Get-OVServerProfile -Name $ServerProfileName -ErrorAction Stop
            
            # Priprema monitoringa
            Write-Log "Pokrecem update proces..." -Level "INFO"
            Write-Log "Ova faza moze potrajati 15-30 minuta." -Level "WARNING"
            
            if ($Mode -ne "Simulate") {
                # Pokreni update
                $task = Update-OVServerProfile -InputObject $profile -ErrorAction Stop
                
                # Monitoring progresa
                $maxWaitTime = 1800 # 30 minuta
                $elapsed = 0
                $checkInterval = 30
                
                do {
                    Start-Sleep -Seconds $checkInterval
                    $elapsed += $checkInterval
                    
                    # Proveri status task-a
                    $currentTask = Get-OVTask -Resource $profile.name | Where-Object { $_.taskState -eq "Running" } | Select-Object -First 1
                    
                    if ($currentTask) {
                        $percentComplete = $currentTask.percentComplete
                        Write-Log "Progress: $percentComplete% - $($currentTask.taskStatus)" -Level "DEBUG"
                    }
                    
                    # Proveri da li je potreban cold restart
                    $server = Get-OVServer -Name $ServerProfileName -ErrorAction SilentlyContinue
                    if ($server -and $server.powerState -eq "Off" -and $elapsed -gt 300) {
                        Write-Log "⚠ Server je iskljucen. Verovatno je potreban cold restart." -Level "WARNING"
                        
                        if ($Mode -eq "Production") {
                            $restartConfirmation = Read-Host "Server zahteva restart da bi se firmware primenio. Ukljuciti server? (da/ne)"
                            if ($restartConfirmation -eq "da") {
                                Write-Log "Ukljucujem server..." -Level "INFO"
                                Start-OVServer -Server $server -ErrorAction Stop
                                Write-Log "✓ Server ukljucen. Cekam da se podigne..." -Level "SUCCESS"
                            }
                        }
                    }
                    
                } while ($currentTask -and $elapsed -lt $maxWaitTime)
                
                if ($elapsed -ge $maxWaitTime) {
                    throw "Update timeout! Proces nije zavrsen za 30 minuta. Proverite manualno."
                }
                
                Write-Log "✓ Update from Template zavrsen" -Level "SUCCESS"
            }
            else {
                Write-Log "[SIMULACIJA] Update from Template bi bio pokrenut" -Level "WARNING"
            }
            
            return $true
        } `
        -Critical
}

Write-Log "✓ FAZA 4 ZAVRSENA - Update from Template kompletan" -Level "SUCCESS"
#endregion

#region FAZA 5 - POST-UPDATE VERIFIKACIJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "FAZA 5: POST-UPDATE VERIFIKACIJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# 5.1 Verifikacija Firmware Verzije
$firmwareVerifyResult = Invoke-Action -ActionName "Verifikacija Firmware Verzije" `
    -Description "Provera da li je novi firmware primenjen" `
    -Action {
        Start-Sleep -Seconds 10 # Sacekaj da se sve stabilizuje
        
        $server = Get-OVServer -Name $ServerProfileName -ErrorAction Stop
        $currentFirmware = $server.romVersion
        
        Write-Log "Trenutni Firmware: $currentFirmware" -Level "INFO"
        Write-Log "Ocekivani SPP: $SPPVersion" -Level "INFO"
        
        # Proveri da li firmware odgovara ocekivanoj verziji
        if ($currentFirmware -like "*$SPPVersion*" -or $Mode -eq "Simulate") {
            Write-Log "✓ Firmware verzija verifikovana" -Level "SUCCESS"
        }
        else {
            Write-Log "⚠ Firmware verzija se ne poklapa!" -Level "WARNING"
            Write-Log "  Trenutni: $currentFirmware" -Level "WARNING"
            Write-Log "  Ocekivani: $SPPVersion" -Level "WARNING"
        }
        
        return @{ CurrentFirmware = $currentFirmware; ExpectedFirmware = $SPPVersion }
    }

# 5.2 Provera Server Status-a
$serverStatusResult = Invoke-Action -ActionName "Provera Server Status-a" `
    -Description "Finalna provera statusa servera" `
    -Action {
        $server = Get-OVServer -Name $ServerProfileName -ErrorAction Stop
        $profile = Get-OVServerProfile -Name $ServerProfileName -ErrorAction Stop
        
        Write-Log "Server Status: $($server.status)" -Level "INFO"
        Write-Log "Server Power State: $($server.powerState)" -Level "INFO"
        Write-Log "Profile Status: $($profile.status)" -Level "INFO"
        Write-Log "Profile Compliance: $($profile.templateCompliance)" -Level "INFO"
        
        if ($server.status -eq "OK" -and $profile.status -eq "OK") {
            Write-Log "✓ Svi statusi su OK" -Level "SUCCESS"
        }
        else {
            Write-Log "⚠ Postoje problemi sa statusom!" -Level "WARNING"
        }
        
        return @{ Server = $server; Profile = $profile }
    }

Write-Log "✓ FAZA 5 ZAVRSENA - Post-update verifikacija kompletna" -Level "SUCCESS"
#endregion

#region ZAVRSNA FAZA
Write-Log "`n========================================" -Level "INFO"
Write-Log "ZAVRSNA FAZA - REZIME" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# Generisi izvestaj
Close-Logging

# Diskonektuj se sa OneView-a
Disconnect-OVMgmt -ErrorAction SilentlyContinue

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        SCENARIO 2 - ZAVRSEN USPESNO! ✅                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
#endregion
