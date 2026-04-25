<#
.SYNOPSIS
    OneView Profile Compliance PowerShell Script
.DESCRIPTION
    Checks and remediates OneView server profile compliance with templates
.AUTHOR
    MCP_HpOneView Extended
.VERSION
    1.0
.NOTES
    Requires OneView PowerShell module and valid credentials
.PARAMETER ProfileName
    The name of the target server profile
.PARAMETER ComplianceType
    The type of compliance check (full, basic, firmware, network)
.PARAMETER Remediate
    Whether to remediate non-compliant profiles
.PARAMETER Timestamp
    Execution timestamp for logging
.EXAMPLE
    .\ProfileCompliance.ps1 -ProfileName "WebServer-01" -ComplianceType "full"
    .\ProfileCompliance.ps1 -ProfileName "WebServer-01" -ComplianceType "firmware" -Remediate $true
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ProfileName,
    
    [Parameter()]
    [ValidateSet("full", "basic", "firmware", "network")]
    [string]$ComplianceType = "full",
    
    [Parameter()]
    [bool]$Remediate = $false,
    
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

$LogFile = "$LogPath\ProfileCompliance_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-Host "OneView Profile Compliance Script" -ForegroundColor Green
Write-Host "Profile: $ProfileName" -ForegroundColor Yellow
Write-Host "Type: $ComplianceType" -ForegroundColor Yellow
Write-Host "Remediate: $Remediate" -ForegroundColor Yellow
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

# Function to get target profile
function Get-TargetProfile {
    param([string]$Name)
    
    try {
        $Profile = Get-OVMgmtServerProfile -Name $Name
        if (-not $Profile) {
            Write-Error "Profile '$Name' not found"
            return $null
        }
        return $Profile
    }
    catch {
        Write-Error "Failed to get profile '$Name': $($_.Exception.Message)"
        return $null
    }
}

# Function to get profile template
function Get-ProfileTemplate {
    param([object]$Profile)
    
    try {
        if ($Profile.templateUri) {
            $Template = Get-OVMgmtServerProfileTemplate -Uri $Profile.templateUri
            return $Template
        } else {
            Write-Warning "Profile has no template"
            return $null
        }
    }
    catch {
        Write-Error "Failed to get profile template: $($_.Exception.Message)"
        return $null
    }
}

# Function to check basic compliance
function Test-BasicCompliance {
    param([object]$Profile)
    
    try {
        Write-Host "`n=== Basic Compliance Check ===" -ForegroundColor Cyan
        Write-Host "Profile Status: $($Profile.status)" -ForegroundColor $(if ($Profile.status -eq "Normal") { "Green" } else { "Yellow" })
        
        # Check consistency
        $Consistency = Get-OVMgmtServerProfileConsistency -ServerProfile $Profile
        Write-Host "Consistency Status: $($Consistency.consistencyStatus)" -ForegroundColor $(if ($Consistency.consistencyStatus -eq "Consistent") { "Green" } else { "Red" })
        Write-Host "Inconsistent Items: $($Consistency.inconsistentItems.Count)" -ForegroundColor $(if ($Consistency.inconsistentItems.Count -eq 0) { "Green" } else { "Red" })
        
        if ($Consistency.message) {
            Write-Host "Message: $($Consistency.message)" -ForegroundColor Gray
        }
        
        return @{
            Status = if ($Profile.status -eq "Normal") { "Compliant" } else { "Non-compliant" }
            Consistency = $Consistency.consistencyStatus
            InconsistentItems = $Consistency.inconsistentItems.Count
            Message = $Consistency.message
        }
    }
    catch {
        Write-Error "Failed to check basic compliance: $($_.Exception.Message)"
        return @{
            Status = "Error"
            Consistency = "Error"
            InconsistentItems = 0
            Message = $_.Exception.Message
        }
    }
}

# Function to check firmware compliance
function Test-FirmwareCompliance {
    param([object]$Profile, [object]$Template)
    
    try {
        Write-Host "`n=== Firmware Compliance Check ===" -ForegroundColor Cyan
        
        if (-not $Template) {
            Write-Warning "No template available for firmware compliance check"
            return @{
                Status = "No Template"
                Message = "No template available"
            }
        }
        
        # Get server hardware firmware
        $ServerHardware = Get-OVMgmtServerHardware -Uri $Profile.serverHardwareUri
        $ServerFirmware = Get-OVMgmtServerFirmware -ServerHardware $ServerHardware
        
        # Get template firmware
        $TemplateFirmware = Get-OVMgmtServerFirmware -Uri $Template.firmware.uri
        
        Write-Host "Server Firmware: $($ServerFirmware.firmwareVersion)" -ForegroundColor Gray
        Write-Host "Template Firmware: $($TemplateFirmware.firmwareVersion)" -ForegroundColor Gray
        
        $Compliant = $ServerFirmware.firmwareVersion -eq $TemplateFirmware.firmwareVersion
        
        Write-Host "Firmware Compliance: $(if ($Compliant) { 'Compliant' } else { 'Non-compliant' })" -ForegroundColor $(if ($Compliant) { "Green" } else { "Red" })
        
        return @{
            Status = if ($Compliant) { "Compliant" } else { "Non-compliant" }
            ServerVersion = $ServerFirmware.firmwareVersion
            TemplateVersion = $TemplateFirmware.firmwareVersion
            Compliant = $Compliant
        }
    }
    catch {
        Write-Error "Failed to check firmware compliance: $($_.Exception.Message)"
        return @{
            Status = "Error"
            Message = $_.Exception.Message
        }
    }
}

# Function to check network compliance
function Test-NetworkCompliance {
    param([object]$Profile, [object]$Template)
    
    try {
        Write-Host "`n=== Network Compliance Check ===" -ForegroundColor Cyan
        
        if (-not $Template) {
            Write-Warning "No template available for network compliance check"
            return @{
                Status = "No Template"
                Message = "No template available"
            }
        }
        
        # Get profile connections
        $ProfileConnections = Get-OVMgmtServerProfileConnections -ServerProfile $Profile
        $TemplateConnections = Get-OVMgmtServerProfileConnections -Uri $Template.connections.uri
        
        Write-Host "Profile Connections: $($ProfileConnections.connections.Count)" -ForegroundColor Gray
        Write-Host "Template Connections: $($TemplateConnections.connections.Count)" -ForegroundColor Gray
        
        # Compare connections (simplified comparison)
        $Compliant = $ProfileConnections.connections.Count -eq $TemplateConnections.connections.Count
        
        Write-Host "Network Compliance: $(if ($Compliant) { 'Compliant' } else { 'Non-compliant' })" -ForegroundColor $(if ($Compliant) { "Green" } else { "Red" })
        
        return @{
            Status = if ($Compliant) { "Compliant" } else { "Non-compliant" }
            ProfileConnections = $ProfileConnections.connections.Count
            TemplateConnections = $TemplateConnections.connections.Count
            Compliant = $Compliant
        }
    }
    catch {
        Write-Error "Failed to check network compliance: $($_.Exception.Message)"
        return @{
            Status = "Error"
            Message = $_.Exception.Message
        }
    }
}

# Function to perform full compliance check
function Test-FullCompliance {
    param([object]$Profile)
    
    Write-Host "`n=== Full Compliance Check ===" -ForegroundColor Cyan
    
    # Get template
    $Template = Get-ProfileTemplate -Profile $Profile
    if (-not $Template) {
        Write-Warning "No template available for full compliance check"
        return @{
            Status = "No Template"
            Message = "No template available"
        }
    }
    
    # Perform all checks
    $BasicResult = Test-BasicCompliance -Profile $Profile
    $FirmwareResult = Test-FirmwareCompliance -Profile $Profile -Template $Template
    $NetworkResult = Test-NetworkCompliance -Profile $Profile -Template $Template
    
    Write-Host "`n=== Full Compliance Results ===" -ForegroundColor Cyan
    Write-Host "Basic Status: $($BasicResult.Status)" -ForegroundColor $(if ($BasicResult.Status -eq "Compliant") { "Green" } else { "Red" })
    Write-Host "Firmware Status: $($FirmwareResult.Status)" -ForegroundColor $(if ($FirmwareResult.Status -eq "Compliant") { "Green" } else { "Red" })
    Write-Host "Network Status: $($NetworkResult.Status)" -ForegroundColor $(if ($NetworkResult.Status -eq "Compliant") { "Green" } else { "Red" })
    
    $OverallCompliant = ($BasicResult.Status -eq "Compliant") -and ($FirmwareResult.Status -eq "Compliant") -and ($NetworkResult.Status -eq "Compliant")
    
    Write-Host "Overall Compliance: $(if ($OverallCompliant) { 'Compliant' } else { 'Non-compliant' })" -ForegroundColor $(if ($OverallCompliant) { "Green" } else { "Red" })
    
    return @{
        Status = if ($OverallCompliant) { "Compliant" } else { "Non-compliant" }
        Basic = $BasicResult
        Firmware = $FirmwareResult
        Network = $NetworkResult
        Overall = $OverallCompliant
    }
}

# Function to remediate profile
function Set-ProfileRemediation {
    param([object]$Profile)
    
    Write-Host "`n=== Profile Remediation ===" -ForegroundColor Yellow
    Write-Host "Profile: $($Profile.name)" -ForegroundColor White
    Write-Host "Template: $($Profile.templateUri)" -ForegroundColor Gray
    Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
    
    try {
        Write-Host "Updating profile from template..." -ForegroundColor Blue
        
        $Result = Set-OVMgmtServerProfile -ServerProfile $Profile -TemplateUri $Profile.templateUri
        
        if ($Result.taskState -eq "Completed") {
            Write-Host "Profile remediation completed successfully!" -ForegroundColor Green
            Write-Host "Task State: $($Result.taskState)" -ForegroundColor Green
            Write-Host "Task Status: $($Result.taskStatus)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Profile remediation failed!" -ForegroundColor Red
            Write-Host "Task State: $($Result.taskState)" -ForegroundColor Red
            Write-Host "Task Status: $($Result.taskStatus)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Error "Profile remediation failed: $($_.Exception.Message)"
        return $false
    }
}

# Function to wait for remediation completion
function Wait-ForRemediationCompletion {
    param([object]$RemediationResult)
    
    Write-Host "Waiting for profile remediation to complete..." -ForegroundColor Blue
    
    try {
        $Timeout = 900  # 15 minutes
        $Interval = 30   # 30 seconds
        $Elapsed = 0
        
        while ($Elapsed -lt $Timeout) {
            Start-Sleep -Seconds $Interval
            $Elapsed += $Interval
            
            try {
                $Status = Get-OVMgmtTask -Task $RemediationResult
                Write-Host "  Status: $($Status.taskState) - Elapsed: $($Elapsed)s" -ForegroundColor Gray
                
                if ($Status.taskState -eq "Completed") {
                    Write-Host "Profile remediation completed successfully!" -ForegroundColor Green
                    return $true
                }
                elseif ($Status.taskState -eq "Error" -or $Status.taskState -eq "Warning") {
                    Write-Host "Profile remediation failed with status: $($Status.taskState)" -ForegroundColor Red
                    return $false
                }
            }
            catch {
                Write-Warning "Failed to check remediation status: $($_.Exception.Message)"
            }
        }
        
        Write-Host "Timeout reached waiting for profile remediation" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Error "Failed to wait for remediation completion: $($_.Exception.Message)"
        return $false
    }
}

# Main execution
try {
    # Get target profile
    $TargetProfile = Get-TargetProfile -Name $ProfileName
    if (-not $TargetProfile) {
        exit 1
    }
    
    # Display profile information
    Write-Host "Profile Name: $($TargetProfile.name)" -ForegroundColor White
    Write-Host "Description: $($TargetProfile.description)" -ForegroundColor Gray
    Write-Host "Template: $($TargetProfile.templateUri)" -ForegroundColor Gray
    Write-Host "Server: $($TargetProfile.serverHardwareUri)" -ForegroundColor Gray
    Write-Host "Status: $($TargetProfile.status)" -ForegroundColor $(if ($TargetProfile.status -eq "Normal") { "Green" } else { "Yellow" })
    
    # Perform compliance check based on type
    switch ($ComplianceType) {
        "full" {
            $ComplianceResult = Test-FullCompliance -Profile $TargetProfile
        }
        "basic" {
            $ComplianceResult = Test-BasicCompliance -Profile $TargetProfile
        }
        "firmware" {
            $Template = Get-ProfileTemplate -Profile $TargetProfile
            if ($Template) {
                $ComplianceResult = Test-FirmwareCompliance -Profile $TargetProfile -Template $Template
            } else {
                Write-Warning "No template available for firmware compliance check"
                $ComplianceResult = @{ Status = "No Template", Message = "No template available" }
            }
        }
        "network" {
            $Template = Get-ProfileTemplate -Profile $TargetProfile
            if ($Template) {
                $ComplianceResult = Test-NetworkCompliance -Profile $TargetProfile -Template $Template
            } else {
                Write-Warning "No template available for network compliance check"
                $ComplianceResult = @{ Status = "No Template", Message = "No template available" }
            }
        }
        default {
            Write-Error "Unknown compliance type: $ComplianceType"
            exit 1
        }
    }
    
    # Display compliance results
    Write-Host "`n=== Compliance Results ===" -ForegroundColor Cyan
    Write-Host "Type: $ComplianceType" -ForegroundColor Gray
    Write-Host "Status: $($ComplianceResult.Status)" -ForegroundColor $(if ($ComplianceResult.Status -eq "Compliant") { "Green" } else { "Red" })
    
    if ($ComplianceResult.Message) {
        Write-Host "Message: $($ComplianceResult.Message)" -ForegroundColor Gray
    }
    
    # Check if remediation is needed
    if ($ComplianceResult.Status -ne "Compliant" -and $Remediate) {
        Write-Host "`n=== Profile Remediation ===" -ForegroundColor Yellow
        Write-Host "Remediation Required: Yes" -ForegroundColor Red
        Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
        
        # Perform remediation
        $RemediationSuccess = Set-ProfileRemediation -Profile $TargetProfile
        
        if ($RemediationSuccess) {
            # Wait for completion
            $CompletionSuccess = Wait-ForRemediationCompletion -RemediationResult $RemediationResult
            
            if ($CompletionSuccess) {
                Write-Host "`n=== Remediation Completed Successfully ===" -ForegroundColor Green
                Write-Host "Profile: $ProfileName" -ForegroundColor Gray
                Write-Host "Type: $ComplianceType" -ForegroundColor Gray
                Write-Host "Remediated: Yes" -ForegroundColor Gray
                Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
            } else {
                Write-Host "`n=== Remediation Failed ===" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "`n=== Remediation Failed ===" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "`n=== No Remediation Required ===" -ForegroundColor Green
        Write-Host "Profile: $ProfileName" -ForegroundColor Gray
        Write-Host "Type: $ComplianceType" -ForegroundColor Gray
        Write-Host "Status: $($ComplianceResult.Status)" -ForegroundColor $(if ($ComplianceResult.Status -eq "Compliant") { "Green" } else { "Yellow" })
        Write-Host "Remediated: No" -ForegroundColor Gray
        Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
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
    $LogEntry = "[$Timestamp] Profile compliance check completed. Profile: $ProfileName, Type: $ComplianceType, Remediated: $Remediate"
    Add-Content -Path $LogFile -Value $LogEntry
}

# End of script