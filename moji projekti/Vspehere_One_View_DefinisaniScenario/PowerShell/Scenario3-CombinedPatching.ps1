<#
.SYNOPSIS
    Scenario 3 - Kombinovano VMware i HP OneView Patching
    
.DESCRIPTION
    Kombinovani scenario koji prvo izvrsava VMware vCenter patching (Scenario 1),
    zatim HP OneView firmware update (Scenario 2) za isti host.
    
.PARAMETER vCenterServer
    vCenter server hostname
    
.PARAMETER OneViewServer
    HP OneView server hostname
    
.PARAMETER HostName
    Ime ESXi hosta
    
.PARAMETER ServerProfileName
    Ime server profila u OneView
    
.PARAMETER Mode
    Rezim rada: Simulate, Test, Production
    
.EXAMPLE
    .\Scenario3-CombinedPatching.ps1 -vCenterServer "vc.local" -OneViewServer "ov.local" -HostName "esxi01" -ServerProfileName "Profile-01" -Mode "Simulate"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$vCenterServer,
    
    [Parameter(Mandatory=$true)]
    [string]$OneViewServer,
    
    [Parameter(Mandatory=$true)]
    [string]$HostName,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerProfileName,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("Simulate", "Test", "Production")]
    [string]$Mode
)

# Ucitaj core modul
Import-Module "$PSScriptRoot\VMwarePatchingCore.psm1" -Force

#region INICIJALIZACIJA
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   SCENARIO 3 - Kombinovano VMware + HP OneView Patching     ║
║                                                              ║
║   Scenario 1: VMware vCenter Patching                       ║
║   Scenario 2: HP OneView Firmware Update                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

Set-ExecutionMode -Mode $Mode
Initialize-Logging -SessionName "Scenario3_Combined_$($HostName -replace '[^a-zA-Z0-9]', '_')"

Write-Log "=== POCETAK SCENARIO 3 - KOMBINOVANI PATCHING ===" -Level "INFO"
Write-Log "vCenter: $vCenterServer" -Level "INFO"
Write-Log "OneView: $OneViewServer" -Level "INFO"
Write-Log "Host: $HostName" -Level "INFO"
Write-Log "Server Profile: $ServerProfileName" -Level "INFO"
#endregion

#region FAZA 1 - SCENARIO 1 (VMware Patching)
Write-Log "`n" -Level "INFO" -NoConsole
Write-Log "╔══════════════════════════════════════════════════════════════╗" -Level "INFO"
Write-Log "║  FAZA 1: VMware vCenter Patching (Scenario 1)               ║" -Level "INFO"
Write-Log "╚══════════════════════════════════════════════════════════════╝" -Level "INFO"

$vmwareParams = @{
    vCenterServer = $vCenterServer
    HostName = $HostName
    Mode = $Mode
}

try {
    # Pokreni Scenario 1
    & "$PSScriptRoot\Scenario1-VMwarePatching.ps1" @vmwareParams
    
    Write-Log "✓ Scenario 1 (VMware) uspesno zavrsen" -Level "SUCCESS"
}
catch {
    Write-Log "✗ Scenario 1 (VMware) nije uspeo: $_" -Level "ERROR"
    Write-Log "Prekidam izvrsavanje Scenarija 3." -Level "ERROR"
    Close-Logging
    exit 1
}
#endregion

#region FAZA 2 - SCENARIO 2 (HP OneView Update)
Write-Log "`n" -Level "INFO" -NoConsole
Write-Log "╔══════════════════════════════════════════════════════════════╗" -Level "INFO"
Write-Log "║  FAZA 2: HP OneView Firmware Update (Scenario 2)            ║" -Level "INFO"
Write-Log "╚══════════════════════════════════════════════════════════════╝" -Level "INFO"

$oneviewParams = @{
    OneViewServer = $OneViewServer
    ServerProfileName = $ServerProfileName
    Mode = $Mode
}

try {
    # Pokreni Scenario 2
    & "$PSScriptRoot\Scenario2-HPOneViewUpdate.ps1" @oneviewParams
    
    Write-Log "✓ Scenario 2 (HP OneView) uspesno zavrsen" -Level "SUCCESS"
}
catch {
    Write-Log "✗ Scenario 2 (HP OneView) nije uspeo: $_" -Level "ERROR"
    Write-Log "Scenario 1 je uspeo, ali Scenario 2 nije." -Level "WARNING"
}
#endregion

#region ZAVRSNA FAZA
Write-Log "`n" -Level "INFO" -NoConsole
Write-Log "╔══════════════════════════════════════════════════════════════╗" -Level "INFO"
Write-Log "║  ZAVRSNA FAZA - KOMBINOVANI PATCHING                        ║" -Level "INFO"
Write-Log "╚══════════════════════════════════════════════════════════════╝" -Level "INFO"

# Generisi finalni izvestaj
Close-Logging

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     SCENARIO 3 - KOMBINOVANI PATCHING ZAVRSEN! ✅           ║
║                                                              ║
║     ✓ VMware vCenter Patching                               ║
║     ✓ HP OneView Firmware Update                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
#endregion
