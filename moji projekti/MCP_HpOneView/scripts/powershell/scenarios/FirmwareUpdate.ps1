<#
.SYNOPSIS
    OneView Firmware Update PowerShell Script
.DESCRIPTION
    Updates firmware on OneView server hardware using SPP bundles
.AUTHOR
    MCP_HpOneView Extended
.VERSION
    1.0
.NOTES
    Requires OneView PowerShell module and valid credentials
.PARAMETER ServerName
    The name of the target server
.PARAMETER SppVersion
    The SPP bundle version to install
.PARAMETER UpdateMode
    The update mode (FirmwareOnly, FirmwareAndDrivers)
.PARAMETER ForceUpdate
    Whether to force the update even if not needed
.PARAMETER Timestamp
    Execution timestamp for logging
.EXAMPLE
    .\FirmwareUpdate.ps1 -ServerName "Server01" -SppVersion "2023.09.0"
    .\FirmwareUpdate.ps1 -ServerName "Server01" -SppVersion "2023.09.0" -UpdateMode "FirmwareAndDrivers" -ForceUpdate $true
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerName,
    
    [Parameter(Mandatory=$true)]
    [string]$SppVersion,
    
    [Parameter()]
    [ValidateSet("FirmwareOnly", "FirmwareAndDrivers")]
    [string]$UpdateMode = "FirmwareOnly",
    
    [Parameter()]
    [bool]$ForceUpdate = $false,
    
    [Parameter()]
    [string]$Timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
)

# Import OneView module
try {
    Import-Module OneView -ErrorAction Stop
}
catch {
    Write-Error "OneView PowerShell module is not installed. Please install it first."
    exit 1
}

# Initialize logging
$LogPath = "C:\Temp\OneView_Scripts\logs"
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

$LogFile = "$LogPath\FirmwareUpdate_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-Host "OneView Firmware Update Script" -ForegroundColor Green
Write-Host "Server: $ServerName" -ForegroundColor Yellow
Write-Host "SPP Version: $SppVersion" -ForegroundColor Yellow
Write-Host "Update Mode: $UpdateMode" -ForegroundColor Yellow
Write-Host "Force Update: $ForceUpdate" -ForegroundColor Yellow
Write-Host "Timestamp: $Timestamp" -ForegroundColor Yellow
Write-Host "Log file: $LogFile" -ForegroundColor Cyan

# Connect to OneView
try {
    Write-Host "Connecting to OneView..." -ForegroundColor Blue
    $OneViewConnection = Connect-OVMgmt -Server $OneViewServer -Credential $OneViewCredential
    Write-Host "Successfully connected to OneView" -ForegroundColor Green
}
catch {
    Write-Error "Failed to connect to OneView: $($_.Exception.Message)"
    exit 1
}

# Function to get target server
function Get-TargetServer {
    param([string]$Name)
    
    try {
        $Server = Get-OVMgmtServerHardware -Name $Name
        if (-not $Server) {
            Write-Error "Server '$Name' not found"
            return $null
        }
        return $Server
    }
    catch {
        Write-Error "Failed to get server '$Name': $($_.Exception.Message)"
        return $null
    }
}

# Function to get available SPP bundles
function Get-SPPBundles {
    try {
        $Bundles = Get-OVMgmtFirmwareBundle
        Write-Host "Found $($Bundles.Count) firmware bundles" -ForegroundColor Green
        return $Bundles
    }
    catch {
        Write-Error "Failed to get firmware bundles: $($_.Exception.Message)"
        return @()
    }
}

# Function to find target SPP bundle
function Find-TargetSPP {
    param([string]$Version)
    
    try {
        $Bundles = Get-SPPBundles
        $TargetSPP = $Bundles | Where-Object { $_.name -like "*$Version*" } | Select-Object -First
        
        if (-not $TargetSPP) {
            Write-Error "SPP bundle version '$Version' not found"
            return $null
        }
        
        Write-Host "Found target SPP: $($TargetSPP.name)" -ForegroundColor Green
        return $TargetSPP
    }
    catch {
        Write-Error "Failed to find SPP bundle: $($_.Exception.Message)"
        return $null
    }
}

# Function to check current firmware
function Get-CurrentFirmware {
    param([object]$Server)
    
    try {
        $Firmware = Get-OVMgmtServerFirmware -ServerHardware $Server
        Write-Host "Current firmware: $($Firmware.firmwareVersion)" -ForegroundColor Gray
        return $Firmware
    }
    catch {
        Write-Error "Failed to get current firmware: $($_.Exception.Message)"
        return $null
    }
}

# Function to update firmware
function Update-ServerFirmware {
    param(
        [object]$Server,
        [object]$SPPBundle,
        [string]$Mode,
        [bool]$Force
    )
    
    Write-Host "`n=== Firmware Update ===" -ForegroundColor Yellow
    Write-Host "Server: $($Server.name)" -ForegroundColor White
    Write-Host "SPP Bundle: $($SPPBundle.name)" -ForegroundColor Gray
    Write-Host "Update Mode: $Mode" -ForegroundColor Gray
    Write-Host "Force Update: $Force" -ForegroundColor Gray
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    try {
        # Check if update is needed
        if (-not $Force) {
            $CurrentFirmware = Get-CurrentFirmware -Server $Server
            if ($CurrentFirmware -and $CurrentFirmware.firmwareVersion -eq $SPPBundle.version) {
                Write-Host "Firmware is already up to date. Skipping update." -ForegroundColor Green
                return $true
            }
        }
        
        # Prepare firmware update request
        $FirmwareRequest = @{
            firmware = @{
                bundleUri = $SPPBundle.uri
                updateMode = $Mode
                forceUpdate = $Force.ToString().ToLower()
            }
        }
        
        Write-Host "Starting firmware update..." -ForegroundColor Blue
        
        # Execute firmware update
        $Result = Set-OVMgmtServerFirmware -ServerHardware $Server -Firmware $FirmwareRequest
        
        if ($Result.taskState -eq "Completed") {
            Write-Host "Firmware update completed successfully!" -ForegroundColor Green
            Write-Host "Task State: $($Result.taskState)" -ForegroundColor Green
            Write-Host "Task Status: $($Result.taskStatus)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Firmware update failed!" -ForegroundColor Red
            Write-Host "Task State: $($Result.taskState)" -ForegroundColor Red
            Write-Host "Task Status: $($Result.taskStatus)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Error "Firmware update failed: $($_.Exception.Message)"
        return $false
    }
}

# Function to wait for update completion
function Wait-ForUpdateCompletion {
    param([object]$UpdateResult)
    
    Write-Host "Waiting for firmware update to complete..." -ForegroundColor Blue
    
    try {
        $Timeout = 1800  # 30 minutes
        $Interval = 30   # 30 seconds
        $Elapsed = 0
        
        while ($Elapsed -lt $Timeout) {
            Start-Sleep -Seconds $Interval
            $Elapsed += $Interval
            
            try {
                $Status = Get-OVMgmtTask -Task $UpdateResult
                Write-Host "  Status: $($Status.taskState) - Elapsed: $($Elapsed)s" -ForegroundColor Gray
                
                if ($Status.taskState -eq "Completed") {
                    Write-Host "Firmware update completed successfully!" -ForegroundColor Green
                    return $true
                }
                elseif ($Status.taskState -eq "Error" -or $Status.taskState -eq "Warning") {
                    Write-Host "Firmware update failed with status: $($Status.taskState)" -ForegroundColor Red
                    return $false
                }
            }
            catch {
                Write-Warning "Failed to check update status: $($_.Exception.Message)"
            }
        }
        
        Write-Host "Timeout reached waiting for firmware update" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Error "Failed to wait for update completion: $($_.Exception.Message)"
        return $false
    }
}

# Function to verify firmware update
function Verify-FirmwareUpdate {
    param([object]$Server, [object]$TargetSPP)
    
    Write-Host "`n=== Firmware Verification ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    try {
        $UpdatedFirmware = Get-OVMgmtServerFirmware -ServerHardware $Server
        
        if ($UpdatedFirmware.firmwareVersion -eq $TargetSPP.version) {
            Write-Host "Firmware update verified successfully!" -ForegroundColor Green
            Write-Host "Updated Version: $($UpdatedFirmware.firmwareVersion)" -ForegroundColor Green
            Write-Host "Bundle Name: $($UpdatedFirmware.firmware.bundleName)" -ForegroundColor Green
            Write-Host "Update Status: $($UpdatedFirmware.firmware.updateStatus)" -ForegroundColor Green
            Write-Host "Last Updated: $($UpdatedFirmware.firmware.lastUpdated)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Firmware update verification failed!" -ForegroundColor Red
            Write-Host "Expected Version: $($TargetSPP.version)" -ForegroundColor Red
            Write-Host "Actual Version: $($UpdatedFirmware.firmwareVersion)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Error "Failed to verify firmware update: $($_.Exception.Message)"
        return $false
    }
}

# Main execution
try {
    # Get target server
    $TargetServer = Get-TargetServer -Name $ServerName
    if (-not $TargetServer) {
        exit 1
    }
    
    # Check server state
    Write-Host "Server State: $($TargetServer.state)" -ForegroundColor Gray
    if ($TargetServer.state -ne "Configured") {
        Write-Warning "Server is not in Configured state. Firmware update may fail."
    }
    
    # Check power state
    Write-Host "Power State: $($TargetServer.powerState)" -ForegroundColor Gray
    if ($TargetServer.powerState -ne "On") {
        Write-Warning "Server is not powered on. Firmware update will fail."
    }
    
    # Get target SPP bundle
    $TargetSPP = Find-TargetSPP -Version $SppVersion
    if (-not $TargetSPP) {
        exit 1
    }
    
    # Display SPP information
    Write-Host "SPP Bundle: $($TargetSPP.name)" -ForegroundColor Gray
    Write-Host "Version: $($TargetSPP.version)" -ForegroundColor Gray
    Write-Host "Size: $($TargetSPP.size | ConvertTo-HumanReadableSize)" -ForegroundColor Gray
    Write-Host "Status: $($TargetSPP.status)" -ForegroundColor Gray
    
    # Get current firmware
    $CurrentFirmware = Get-CurrentFirmware -Server $TargetServer
    if ($CurrentFirmware) {
        Write-Host "Current Firmware: $($CurrentFirmware.firmwareVersion)" -ForegroundColor Gray
    }
    
    # Check if update is needed
    if (-not $ForceUpdate -and $CurrentFirmware -and $CurrentFirmware.firmwareVersion -eq $TargetSPP.version) {
        Write-Host "Firmware is already up to date. Skipping update." -ForegroundColor Green
        exit 0
    }
    
    # Perform firmware update
    $UpdateSuccess = Update-ServerFirmware -Server $TargetServer -SPPBundle $TargetSPP -Mode $UpdateMode -Force $ForceUpdate
    
    if ($UpdateSuccess) {
        # Wait for completion
        $CompletionSuccess = Wait-ForUpdateCompletion -UpdateResult $UpdateResult
        
        if ($CompletionSuccess) {
            # Verify firmware update
            $VerificationSuccess = Verify-FirmwareUpdate -Server $TargetServer -TargetSPP $TargetSPP
            
            if ($VerificationSuccess) {
                Write-Host "`n=== Firmware Update Completed Successfully ===" -ForegroundColor Green
                Write-Host "Server: $ServerName" -ForegroundColor Gray
                Write-Host "SPP Version: $SppVersion" -ForegroundColor Gray
                Write-Host "Update Mode: $UpdateMode" -ForegroundColor Gray
                Write-Host "Force Update: $ForceUpdate" -ForegroundColor Gray
                Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
            } else {
                Write-Host "`n=== Firmware Update Completed (Verification Failed) ===" -ForegroundColor Yellow
                exit 1
            }
        } else {
            Write-Host "`n=== Firmware Update Failed ===" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "`n=== Firmware Update Failed ===" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    exit 1
}
finally {
    # Disconnect from OneView
    try {
        Disconnect-OVMgmt -Server $OneViewConnection
        Write-Host "Disconnected from OneView" -ForegroundColor Green
    }
    catch {
        Write-Warning "Failed to disconnect from OneView: $($_.Exception.Message)"
    }
    
    # Log completion
    $LogEntry = "[$Timestamp] Firmware update completed. Server: $ServerName, SPP: $SppVersion, Mode: $UpdateMode, Force: $ForceUpdate"
    Add-Content -Path $LogFile -Value $LogEntry
}

# End of script