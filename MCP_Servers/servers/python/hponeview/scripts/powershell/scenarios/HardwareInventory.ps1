<#
.SYNOPSIS
    OneView Hardware Inventory PowerShell Script
.DESCRIPTION
    Retrieves detailed hardware inventory information from OneView servers
.AUTHOR
    MCP_HpOneView Extended
.VERSION
    1.0
.NOTES
    Requires OneView PowerShell module and valid credentials
.PARAMETER ServerName
    The name of the target server (optional, defaults to all servers)
.PARAMETER Detailed
    Whether to include detailed hardware information
.PARAMETER Timestamp
    Execution timestamp for logging
.EXAMPLE
    .\HardwareInventory.ps1 -ServerName "Server01" -Detailed $true
    .\HardwareInventory.ps1 -Detailed $true
#>

param(
    [Parameter()]
    [string]$ServerName = "all",
    
    [Parameter()]
    [bool]$Detailed = $false,
    
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

$LogFile = "$LogPath\HardwareInventory_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-Host "OneView Hardware Inventory Script" -ForegroundColor Green
Write-Host "Server: $ServerName" -ForegroundColor Yellow
Write-Host "Detailed: $Detailed" -ForegroundColor Yellow
Write-Host "Timestamp: $Timestamp" -ForegroundColor Yellow
Write-Host "Log file: $LogFile" -ForegroundColor Cyan

# Connect to OneView
try {
    Write-Host "Connecting to OneView..." -ForegroundColor Blue
    $OneViewConnection = Connect-OVMgmt -Server $OneViewServer -Credential $OneViewCredential
    Write-Host "Successfully connected to OneView" -ForegroundColor Green
}
catch {
    Write-Error "  Failed to connect to OneView: $($_.Exception.Message)"
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
        Write-Error "  Failed to get servers: $($_.Exception.Message)"
        return @()
    }
}

# Function to get specific server
function Get-SpecificServer {
    param([string]$Name)
    
    try {
        $Server = Get-OVMgmtServerHardware -Name $Name
        if (-not $Server) {
            Write-Warning "  Server '$Name' not found"
            return $null
        }
        return $Server
    }
    catch {
        Write-Error "  Failed to get server '$Name': $($_.Exception.Message)"
        return $null
    }
}

# Function to display basic server information
function Show-BasicServerInfo {
    param([array]$Servers)
    
    Write-Host "`n=== Hardware Inventory ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    Write-Host "Servers: $($Servers.Count)" -ForegroundColor Gray
    
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

# Function to display detailed server information
function Show-DetailedServerInfo {
    param([array]$Servers)
    
    Write-Host "`n=== Detailed Hardware Inventory ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    Write-Host "Servers: $($Servers.Count)" -ForegroundColor Gray
    
    foreach ($Server in $Servers) {
        Write-Host "`nServer: $($Server.name)" -ForegroundColor White
        Write-Host "  Model: $($Server.model)" -ForegroundColor Gray
        Write-Host "  Serial: $($Server.serialNumber)" -ForegroundColor Gray
        Write-Host "  State: $($Server.state)" -ForegroundColor $(if ($Server.state -eq "Configured") { "Green" } else { "Yellow" })
        Write-Host "  Power: $($Server.powerState)" -ForegroundColor $(if ($Server.powerState -eq "On") { "Green" } else { "Red" })
        Write-Host "  Status: $($Server.status)" -ForegroundColor $(if ($Server.status -eq "OK") { "Green" } else { "Yellow" })
        Write-Host "  IP: $($Server.ipAddress)" -ForegroundColor Gray
        Write-Host "  URI: $($Server.uri)" -ForegroundColor Gray
        
        # Basic hardware information
        Write-Host "  CPU: $($Server.processorCoreCount) cores" -ForegroundColor Gray
        Write-Host "  Memory: $($Server.memoryMb)MB" -ForegroundColor Gray
        Write-Host "  Storage: $($Server.storageControllerCount) controllers" -ForegroundColor Gray
        Write-Host "  NICs: $($Server.portCount) ports" -ForegroundColor Gray
        Write-Host "  Firmware: $($Server.firmware)" -ForegroundColor Gray
        
        if ($Detailed) {
            # Detailed hardware information
            try {
                # Get additional details
                $Details = Get-OVMgmtServerHardware -ServerHardware $Server
                
                Write-Host "  Temperature: $($Details.temperature)°C" -ForegroundColor Gray
                Write-Host "  Power: $($Details.powerState)" -ForegroundColor $(if ($Details.powerState -eq "On") { "Green" } else { "Red" })
                Write-Host "  Health: $($Details.status)" -ForegroundColor $(if ($Details.status -eq "OK") { "Green" } else { "Yellow" })
                
                # Get port information
                $Ports = Get-OVMgmtServerPort -ServerHardware $Server
                Write-Host "  Ports: $($Ports.Count)" -ForegroundColor Gray
                foreach ($Port in $Ports) {
                    Write-Host "    Port $($Port.portNumber): $($Port.type) - $($Port.status)" -ForegroundColor Gray
                }
                
                # Get storage information
                $Storage = Get-OVMgmtServerStorage -ServerHardware $Server
                Write-Host "  Storage Controllers: $($Storage.Count)" -ForegroundColor Gray
                foreach ($Controller in $Storage) {
                    Write-Host "    Controller $($Controller.model): $($Controller.status)" -ForegroundColor Gray
                }
                
                # Get PCIe information
                $PCIe = Get-OVMgmtServerPcieDevice -ServerHardware $Server
                Write-Host "  PCIe Devices: $($PCIe.Count)" -ForegroundColor Gray
                foreach ($Device in $PCIe) {
                    Write-Host "    PCIe $($Device.deviceName): $($Device.deviceType) - $($Device.status)" -ForegroundColor Gray
                }
                
                # Get enclosure information
                $Enclosure = Get-OVMgmtEnclosure -ServerHardware $Server
                if ($Enclosure) {
                    Write-Host "  Enclosure: $($Enclosure.name)" -ForegroundColor Gray
                    Write-Host "  Bay: $($Enclosure.bayNumber)" -ForegroundColor Gray
                    Write-Host "  Status: $($Enclosure.status)" -ForegroundColor Gray
                }
                
                # Get interconnect information
                $Interconnects = Get-OVMgmtLogicalInterconnect -ServerHardware $Server
                Write-Host "  Interconnects: $($Interconnects.Count)" -ForegroundColor Gray
                foreach ($Interconnect in $Interconnects) {
                    Write-Host "    Interconnect $($Interconnect.name): $($Interconnect.status)" -ForegroundColor Gray
                }
                
                # Get management processor information
                $MP = Get-OVMgmtMp -ServerHardware $Server
                if ($MP) {
                    Write-Host "  Management Processor: $($MP.mpModel)" -ForegroundColor Gray
                    Write-Host "  MP IP: $($MP.mpIpAddress)" -ForegroundColor Gray
                    Write-Host "  MP Status: $($MP.mpStatus)" -ForegroundColor Gray
                }
                
                # Get BIOS information
                $BIOS = Get-OVMgmtBios -ServerHardware $Server
                if ($BIOS) {
                    Write-Host "  BIOS: $($BIOS.biosVersion)" -ForegroundColor Gray
                    Write-Host "  BIOS Date: $($BIOS.biosDate)" -ForegroundColor Gray
                    Write-Host "  BIOS State: $($BIOS.biosState)" -ForegroundColor Gray
                }
                
                # Get iLO information
                $ILO = Get-OVMgmtIloInfo -ServerHardware $Server
                if ($ILO) {
                    Write-Host "  iLO: $($ILO.iloIpAddress)" -ForegroundColor Gray
                    Write-Host "  iLO Version: $($ILO.iloFirmwareVersion)" -ForegroundColor Gray
                    Write-Host "  iLO State: $($ILO.iloState)" -ForegroundColor Gray
                }
                
            }
            catch {
                Write-Warning "  Failed to get detailed information: $($_.Exception.Message)"
            }
        }
    }
}

# Function to create inventory report
function New-InventoryReport {
    param([array]$Servers)
    
    $ReportPath = "C:\Temp\OneView_Scripts\reports"
    if (-not (Test-Path $ReportPath)) {
        New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
    }
    
    $ReportFile = "$ReportPath\HardwareInventory_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    
    $Report = @"
Hardware Inventory Report
=====================
Generated: $Timestamp
Servers: $($Servers.Count)
Detailed: $Detailed

Server List:
"@
    
    foreach ($Server in $Servers) {
        $Report += @"
$($Server.name)
  Model: $($Server.model)
  Serial: $($Server.serialNumber)
  State: $($Server.state)
  Power: $($Server.powerState)
  Status: $($Server.status)
  IP: $($Server.ipAddress)
  URI: $($Server.uri)
"@
        
        if ($Detailed) {
            $Report += @"
  CPU: $($Server.processorCoreCount) cores
  Memory: $($Server.memoryMb)MB
  Storage: $($Server.storageControllerCount) controllers
  NICs: $($Server.portCount) ports
  Firmware: $($Server.firmware)
"@
        }
    }
    
    $Report += @"

End of Report
"@
    
    # Write report to file
    Set-Content -Path $ReportFile -Value $Report
    Write-Host "Inventory report saved to: $ReportFile" -ForegroundColor Green
    
    return $ReportFile
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
    
    # Display server information
    if ($Detailed) {
        Show-DetailedServerInfo -Servers $TargetServers
    } else {
        Show-BasicServerInfo -Servers $TargetServers
    }
    
    # Create inventory report
    $ReportFile = New-InventoryReport -Servers $TargetServers
    
    Write-Host "`n=== Hardware Inventory Completed ===" -ForegroundColor Green
    Write-Host "Servers processed: $($TargetServers.Count)" -ForegroundColor Gray
    Write-Host "Detailed: $Detailed" -ForegroundColor Gray
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    Write-Host "Report file: $ReportFile" -ForegroundColor Cyan
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
    $LogEntry = "[$Timestamp] Hardware inventory completed. Servers: $($TargetServers.Count), Detailed: $Detailed"
    Add-Content -Path $LogFile -Value $LogEntry
}

# End of script