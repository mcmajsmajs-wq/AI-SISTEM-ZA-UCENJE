<#
.SYNOPSIS
    OneView Server Management PowerShell Script
.DESCRIPTION
    Manages OneView server hardware operations including status, power control, and information gathering
.AUTHOR
    MCP_HpOneView Extended
.VERSION
    1.0
.NOTES
    Requires OneView PowerShell module and valid credentials
.PARAMETER Action
    The action to perform (status, power_on, power_off, reset, info, health)
.PARAMETER ServerName
    The name of the target server (optional, defaults to all servers)
.PARAMETER Timestamp
    Execution timestamp for logging
.EXAMPLE
    .\ServerManagement.ps1 -Action status -ServerName "Server01"
    .\ServerManagement.ps1 -Action power_on -ServerName "Server01"
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "power_on", "power_off", "reset", "info", "health")]
    [string]$Action,
    
    [Parameter()]
    [string]$ServerName = "all",
    
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

$LogFile = "$LogPath\ServerManagement_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-Host "OneView Server Management Script" -ForegroundColor Green
Write-Host "Action: $Action" -ForegroundColor Yellow
Write-Host "Server: $ServerName" -ForegroundColor Yellow
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

# Function to get all servers
function Get-AllServers {
    try {
        $Servers = Get-OVMgmtServerHardware
        Write-Host "Found $($Servers.Count) servers" -ForegroundColor Green
        return $Servers
    }
    catch {
        Write-Error "Failed to get servers: $($_.Exception.Message)"
        return @()
    }
}

# Function to get specific server
function Get-SpecificServer {
    param([string]$Name)
    
    try {
        $Server = Get-OVMgmtServerHardware -Name $Name
        if (-not $Server) {
            Write-Warning "Server '$Name' not found"
            return $null
        }
        return $Server
    }
    catch {
        Write-Error "Failed to get server '$Name': $($_.Exception.Message)"
        return $null
    }
}

# Function to display server status
function Show-ServerStatus {
    param([array]$Servers)
    
    Write-Host "`n=== Server Status ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    foreach ($Server in $Servers) {
        Write-Host "`nServer: $($Server.name)" -ForegroundColor White
        Write-Host "  Model: $($Server.model)" -ForegroundColor Gray
        Write-Host "  Serial: $($Server.serialNumber)" -ForegroundColor Gray
        Write-Host "  State: $($Server.state)" -ForegroundColor $(if ($Server.state -eq "Configured") { "Green" } else { "Yellow" })
        Write-Host "  Power: $($Server.powerState)" -ForegroundColor $(if ($Server.powerState -eq "On") { "Green" } else { "Red" })
        Write-Host "  Status: $($Server.status)" -ForegroundColor $(if ($Server.status -eq "OK") { "Green" } else { "Yellow" })
        Write-Host "  IP: $($Server.ipAddress)" -ForegroundColor Gray
        Write-Host "  URI: $($Server.uri)" -ForegroundColor Gray
    }
}

# Function to power on server
function Set-ServerPowerOn {
    param([array]$Servers)
    
    Write-Host "`n=== Power On Servers ===" -ForegroundColor Yellow
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    foreach ($Server in $Servers) {
        Write-Host "Powering on server: $($Server.name)" -ForegroundColor Yellow
        
        try {
            $Result = Set-OVMgmtServerPowerState -ServerHardware $Server -PowerState On
            if ($Result.taskState -eq "Completed") {
                Write-Host "  Successfully powered on $($Server.name)" -ForegroundColor Green
            } else {
                Write-Host "  Failed to power on $($Server.name): $($Result.taskState)" -ForegroundColor Red
            }
        }
        catch {
            Write-Error "  Failed to power on $($Server.name): $($_.Exception.Message)"
        }
    }
}

# Function to power off server
function Set-ServerPowerOff {
    param([array]$Servers)
    
    Write-Host "`n=== Power Off Servers ===" -ForegroundColor Yellow
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    foreach ($Server in $Servers) {
        Write-Host "Powering off server: $($Server.name)" -ForegroundColor Yellow
        
        try {
            $Result = Set-OVMgmtServerPowerState -ServerHardware $Server -PowerState Off
            if ($Result.taskState -eq "Completed") {
                Write-Host "  Successfully powered off $($Server.name)" -ForegroundColor Green
            } else {
                Write-Host "  Failed to power off $($Server.name): $($Result.taskState)" -ForegroundColor Red
            }
        }
        catch {
            Write-Error "  Failed to power off $($Server.name): $($_.Exception.Message)"
        }
    }
}

# Function to reset server
function Reset-Server {
    param([array]$Servers)
    
    Write-Host "`n=== Reset Servers ===" -ForegroundColor Red
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    Write-Host "WARNING: This will force reset the servers!" -ForegroundColor Red
    
    foreach ($Server in $Servers) {
        Write-Host "Resetting server: $($Server.name)" -ForegroundColor Red
        
        try {
            $Result = Send-OVMgmtServerHardware -ServerHardware $Server -ResetType Force
            if ($Result.taskState -eq "Completed") {
                Write-Host "  Successfully reset $($Server.name)" -ForegroundColor Green
            } else {
                Write-Host "  Failed to reset $($Server.name): $($Result.taskState)" -ForegroundColor Red
            }
        }
        catch {
            Write-Error "  Failed to reset $($Server.name): $($_.Exception.Message)"
        }
    }
}

# Function to get detailed server information
function Show-ServerInfo {
    param([array]$Servers)
    
    Write-Host "`n=== Server Information ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    foreach ($Server in $Servers) {
        Write-Host "`nServer: $($Server.name)" -ForegroundColor White
        Write-Host "  Model: $($Server.model)" -ForegroundColor Gray
        Write-Host "  Serial: $($Server.serialNumber)" -ForegroundColor Gray
        Write-Host "  CPU: $($Server.processorCoreCount) cores" -ForegroundColor Gray
        Write-Host "  Memory: $($Server.memoryMb)MB" -ForegroundColor Gray
        Write-Host "  Storage: $($Server.storageControllerCount) controllers" -ForegroundColor Gray
        Write-Host "  NICs: $($Server.portCount) ports" -ForegroundColor Gray
        Write-Host "  Firmware: $($Server.firmware)" -ForegroundColor Gray
        Write-Host "  State: $($Server.state)" -ForegroundColor $(if ($Server.state -eq "Configured") { "Green" } else { "Yellow" })
        Write-Host "  Status: $($Server.status)" -ForegroundColor $(if ($Server.status -eq "OK") { "Green" } else { "Yellow" })
        
        # Get additional details
        try {
            $Details = Get-OVMgmtServerHardware -ServerHardware $Server
            Write-Host "  Temperature: $($Details.temperature)°C" -ForegroundColor Gray
            Write-Host "  Power: $($Details.powerState)" -ForegroundColor $(if ($Details.powerState -eq "On") { "Green" } else { "Red" })
            Write-Host "  Health: $($Details.status)" -ForegroundColor $(if ($Details.status -eq "OK") { "Green" } else { "Yellow" })
        }
        catch {
            Write-Host "  Additional details: Not available" -ForegroundColor Gray
        }
    }
}

# Function to check server health
function Show-ServerHealth {
    param([array]$Servers)
    
    Write-Host "`n=== Server Health Check ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    foreach ($Server in $Servers) {
        Write-Host "`nServer: $($Server.name)" -ForegroundColor White
        
        try {
            $Health = Get-OVMgmtServerHealthStatus -ServerHardware $Server
            Write-Host "  Health: $($Health.status)" -ForegroundColor $(if ($Health.status -eq "OK") { "Green" } else { "Red" })
            Write-Host "  State: $($Health.state)" -ForegroundColor $(if ($Health.state -eq "OK") { "Green" } else { "Yellow" })
            Write-Host "  Message: $($Health.message)" -ForegroundColor Gray
            
            # Check specific health indicators
            if ($Health.indicators) {
                foreach ($Indicator in $Health.indicators) {
                    $Status = if ($Indicator.status -eq "OK") { "Green" } else { "Red" }
                    Write-Host "  $($Indicator.name): $($Indicator.status)" -ForegroundColor $Status
                }
            }
        }
        catch {
            Write-Host "  Health: Not available" -ForegroundColor Red
        }
    }
}

# Main execution
try {
    # Get target servers
    if ($ServerName -eq "all") {
        $TargetServers = Get-AllServers
    }
    else {
        $TargetServer = Get-SpecificServer -Name $ServerName
        if ($TargetServer) {
            $TargetServers = @($TargetServer)
        } else {
            Write-Error "Server '$ServerName' not found"
            exit 1
        }
    }
    
    if (-not $TargetServers -or $TargetServers.Count -eq 0) {
        Write-Error "No servers found"
        exit 1
    }
    
    # Execute action
    switch ($Action) {
        "status" {
            Show-ServerStatus -Servers $TargetServers
        }
        "power_on" {
            Set-ServerPowerOn -Servers $TargetServers
        }
        "power_off" {
            Set-ServerPowerOff -Servers $TargetServers
        }
        "reset" {
            Reset-Server -Servers $TargetServers
        }
        "info" {
            Show-ServerInfo -Servers $TargetServers
        }
        "health" {
            Show-ServerHealth -Servers $TargetServers
        }
        default {
            Write-Error "Unknown action: $Action"
            exit 1
        }
    
    Write-Host "`n=== Script Completed ===" -ForegroundColor Green
    Write-Host "Action: $Action" -ForegroundColor Gray
    Write-Host "Servers processed: $($TargetServers.Count)" -ForegroundColor Gray
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
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
    $LogEntry = "[$Timestamp] Script completed. Action: $Action, Servers: $($TargetServers.Count)"
    Add-Content -Path $LogFile -Value $LogEntry
}

# End of script