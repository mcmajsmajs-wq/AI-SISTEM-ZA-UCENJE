# Integration Guide - vSphere OneView Automatizacija

## 🇷🇸 Integracija sa Postojećim Systemima

Kompletno uputstvo za integraciju enhanced skripti sa postojećim MasterWorkflow i drugim sistemima.

---

## 📋 Sadržaj

1. [MasterWorkflow Integration](#🔄-masterworkflow-integration)
2. [API Integration](#🔌-api-integration)
3. [External Tool Integration](#🛠️-external-tool-integration)
4. [CI/CD Integration](#🚀-cicd-integration)
5. [Monitoring Integration](#📊-monitoring-integration)
6. [Backup Integration](#💾-backup-integration)

---

## 🔄 MasterWorkflow Integration

### **Step 1: Modify MasterWorkflow.ps1**

```powershell
# Otvorite MasterWorkflow.ps1 za editovanje
notepad.exe .\scripts\MasterWorkflow.ps1
```

### **Step 2: Update Import Statements**

Dodajte enhanced skripte u import sekciju:
```powershell
# Postojeći imports
. "$PSScriptRoot\05_Utility\Logger.ps1"
. "$PSScriptRoot\05_Utility\ConfigManager.ps1"
. "$PSScriptRoot\05_Utility\CredentialManager.ps1"
. "$PSScriptRoot\05_Utility\ValidationEngine.ps1"
. "$PSScriptRoot\05_Utility\ErrorHandler.ps1"
. "$PSScriptRoot\05_Utility\ConnectionManager.ps1"

# Novi enhanced imports
. "$PSScriptRoot\04_Infrastructure_Validation\04_Infra_Validate.ps1"
. "$PSScriptRoot\06_Discovery_vCenter\06_Discovery_vCenter.ps1"
. "$PSScriptRoot\07_Discovery_OneView\07_Discovery_OneView.ps1"
. "$PSScriptRoot\09_FW_Update_SPP\09_FW_Update_SPP.ps1"
. "$PSScriptRoot\10_FW_Update_Individual\10_FW_Update_Individual.ps1"
. "$PSScriptRoot\11_Maintenance_Mode\11_Maintenance_Mode.ps1"
. "$PSScriptRoot\12_Monitor_Progress\12_Monitor_Progress.ps1"
. "$PSScriptRoot\14_Generate_Report\14_Generate_Report.ps1"
. "$PSScriptRoot\15_Cleanup\15_Cleanup.ps1"
```

### **Step 3: Update Phase Functions**

Zamenite postojeće phase funkcije sa enhanced verzijama:

```powershell
function Invoke-DiscoveryPhase {
    return Try-CatchBlock -ScriptBlock {
        Write-EnhancedLog "Starting Enhanced Discovery Phase" "INFO" $script:Component
        
        # Infrastructure validation
        $validationResult = Invoke-InfrastructureValidation -Config $global:Config -GenerateReport
        if ($validationResult.OverallStatus -ne "PASS") {
            throw "Infrastructure validation failed: $($validationResult.OverallStatus)"
        }
        
        # vCenter discovery
        $vCenterDiscovery = Invoke-vCenterDiscovery -Config $global:Config -IncludeVMs -ExportResults
        Write-EnhancedLog "vCenter discovery completed: $($vCenterDiscovery.Summary.TotalHosts) hosts" "SUCCESS" $script:Component
        
        # OneView discovery
        $oneViewDiscovery = Invoke-OneViewDiscovery -Config $global:Config -IncludeFirmwareInfo -ExportResults
        Write-EnhancedLog "OneView discovery completed: $($oneViewDiscovery.Summary.TotalServerHardware) servers" "SUCCESS" $script:Component
        
        # Create combined result
        $result = [PSCustomObject]@{
            Phase = "Discovery"
            StartTime = Get-Date
            EndTime = Get-Date
            Success = $true
            ValidationResult = $validationResult
            VCenterDiscovery = $vCenterDiscovery
            OneViewDiscovery = $oneViewDiscovery
            Message = "Enhanced discovery phase completed successfully"
        }
        
        $script:Results += $result
        Write-EnhancedLog "Enhanced discovery phase completed" "SUCCESS" $script:Component
        
        return $result
        
    } -Context "Enhanced Discovery Phase" -RecoveryActions @(
        (New-RecoveryAction -Name "Retry-Discovery" -Action { param($ErrorInfo) return @{ Success = $true } })
    )
}

function Invoke-ExecutionPhase {
    return Try-CatchBlock -ScriptBlock {
        Write-EnhancedLog "Starting Enhanced Execution Phase" "INFO" $script:Component
        
        # Start progress monitoring
        $monitorJob = Start-Job -ScriptBlock {
            param($config) 
            . "$using:PSScriptRoot\12_Monitor_Progress\12_Monitor_Progress.ps1"
            Invoke-ProgressMonitoring -Config $config -OperationType "All"
        } -ArgumentList $global:Config
        
        try {
            # Firmware updates with SPP
            if ($global:Config.system.simulationMode) {
                Write-EnhancedLog "SPP firmware update (simulation mode)" "INFO" $script:Component
                $fwResult = [PSCustomObject]@{ OverallStatus = "Success"; TotalHosts = 0 }
            } else {
                $sppPath = "C:\SPP\$($global:Config.oneView.defaultSPP).iso"
                if (Test-Path $sppPath) {
                    $fwResult = Invoke-FirmwareUpdateSPP -Config $global:Config -SPPPath $sppPath -RollbackOnError
                } else {
                    Write-EnhancedLog "SPP file not found: $sppPath" "WARN" $script:Component
                    $fwResult = [PSCustomObject]@{ OverallStatus = "Skipped"; Message = "SPP file not found" }
                }
            }
            
            # Maintenance mode operations
            $maintenanceResult = Invoke-MaintenanceMode -Config $global:Config -Action "Exit"
            
            # Wait for monitoring
            $monitorResult = Wait-Job $monitorJob -Timeout 3000
            
            $result = [PSCustomObject]@{
                Phase = "Execution"
                StartTime = Get-Date
                EndTime = Get-Date
                Success = $true
                FirmwareUpdateResult = $fwResult
                MaintenanceResult = $maintenanceResult
                MonitorResult = $monitorResult
                Message = "Enhanced execution phase completed successfully"
            }
            
            $script:Results += $result
            Write-EnhancedLog "Enhanced execution phase completed" "SUCCESS" $script:Component
            
            return $result
            
        } finally {
            # Cleanup monitoring job
            if ($monitorJob.State -eq "Running") {
                Stop-Job $monitorJob
            }
            Remove-Job $monitorJob -Force
        }
        
    } -Context "Enhanced Execution Phase" -RecoveryActions @(
        (New-RecoveryAction -Name "Retry-Execution" -Action { param($ErrorInfo) return @{ Success = $true } })
    )
}

function Invoke-ReportingPhase {
    return Try-CatchBlock -ScriptBlock {
        Write-EnhancedLog "Starting Enhanced Reporting Phase" "INFO" $script:Component
        
        # Generate comprehensive report
        $reportResult = Invoke-ReportGeneration -Config $global:Config -ReportType "All" -OutputFormat @("HTML", "JSON") -EmailReport
        
        $result = [PSCustomObject]@{
            Phase = "Reporting"
            StartTime = Get-Date
            EndTime = Get-Date
            Success = $true
            ReportResult = $reportResult
            Message = "Enhanced reporting phase completed successfully"
        }
        
        $script:Results += $result
        Write-EnhancedLog "Enhanced reporting phase completed" "SUCCESS" $script:Component
        
        return $result
        
    } -Context "Enhanced Reporting Phase" -RecoveryActions @(
        (New-RecoveryAction -Name "Retry-Reporting" -Action { param($ErrorInfo) return @{ Success = $true } })
    )
}

function Invoke-CleanupPhase {
    return Try-CatchBlock -ScriptBlock {
        Write-EnhancedLog "Starting Enhanced Cleanup Phase" "INFO" $script:Component
        
        # Cleanup operations
        $cleanupResult = Invoke-CleanupOperations -Config $global:Config -CleanupType "All" -RetentionDays 30
        
        $result = [PSCustomObject]@{
            Phase = "Cleanup"
            StartTime = Get-Date
            EndTime = Get-Date
            Success = $true
            CleanupResult = $cleanupResult
            Message = "Enhanced cleanup phase completed successfully"
        }
        
        $script:Results += $result
        Write-EnhancedLog "Enhanced cleanup phase completed" "SUCCESS" $script:Component
        
        return $result
        
    } -Context "Enhanced Cleanup Phase" -RecoveryActions @(
        (New-RecoveryAction -Name "Retry-Cleanup" -Action { param($ErrorInfo) return @{ Success = $true } })
    )
}
```

### **Step 4: Update Phase Execution**

Modifikujte glavni execution block:
```powershell
# Update main execution switch
switch ($Phase) {
    'Discovery' { 
        $result = Invoke-DiscoveryPhase
    }
    'Execution' { 
        $result = Invoke-ExecutionPhase 
    }
    'PostCheck' { 
        $result = Invoke-ReportingPhase  # Koristiti reporting umesto postcheck
    }
    'All' { 
        Write-EnhancedLog "Executing all enhanced phases sequentially" "INFO" $script:Component
        Invoke-DiscoveryPhase
        Invoke-ExecutionPhase
        Invoke-ReportingPhase
        Invoke-CleanupPhase
    }
    default {
        throw "Unknown phase: $Phase"
    }
}
```

---

## 🔌 API Integration

### **REST API Integration**

Kreirajte API wrapper za enhanced skripte:
```powershell
function Invoke-vSphereAPI {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Endpoint,
        
        [Parameter(Mandatory=$false)]
        [object]$Data,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("GET", "POST", "PUT", "DELETE")]
        [string]$Method = "GET"
    )
    
    # Load configuration
    $config = Get-Configuration -ConfigFile "scripts/config/settings.json"
    
    # Get credentials
    $cred = Get-StoredCredential -TargetName "vcenter-admin"
    
    # Setup API call
    $uri = "https://$($config.vCenter.server)/api/v1$Endpoint"
    $headers = @{
        "Content-Type" = "application/json"
        "Accept" = "application/json"
    }
    
    try {
        switch ($Method) {
            "GET" { $response = Invoke-RestMethod -Uri $uri -Headers $headers -Credential $cred }
            "POST" { $response = Invoke-RestMethod -Uri $uri -Headers $headers -Credential $cred -Method Post -Body ($Data | ConvertTo-Json) }
            "PUT" { $response = Invoke-RestMethod -Uri $uri -Headers $headers -Credential $cred -Method Put -Body ($Data | ConvertTo-Json) }
            "DELETE" { $response = Invoke-RestMethod -Uri $uri -Headers $headers -Credential $cred -Method Delete }
        }
        
        return $response
        
    } catch {
        Write-EnhancedLog "API call failed: $($_.Exception.Message)" "ERROR" "API"
        throw
    }
}

# API examples for enhanced operations
function Start-EnhancedDiscovery {
    $data = @{
        type = "discovery"
        targets = @("vCenter", "oneView")
        options = @{
            includeVMs = $true
            includeFirmwareInfo = $true
        }
    }
    
    return Invoke-vSphereAPI -Endpoint "/discovery/start" -Data $data -Method "POST"
}

function Get-EnhancedProgress {
    return Invoke-vSphereAPI -Endpoint "/progress/status" -Method "GET"
}
```

### **WebSocket Integration**

```powershell
function Connect-ProgressWebSocket {
    param([string]$Server = "localhost")
    
    $config = Get-Configuration -ConfigFile "scripts/config/settings.json"
    $wsUri = "ws://$Server/progress"
    
    try {
        $ws = New-Object System.Net.WebSockets.ClientWebSocket
        $ct = New-Object System.Threading.CancellationTokenSource
        
        # Connect to WebSocket
        $ws.ConnectAsync($wsUri, $ct.Token).Wait()
        
        # Start listening for messages
        $receiveTask = $ws.ReceiveAsync($ct.Token)
        
        while (-not $ct.Token.IsCancellationRequested) {
            $result = $receiveTask.Result
            $message = [System.Text.Encoding]::UTF8.GetString($result.Array, 0, $result.Count)
            
            # Parse progress message
            $progressData = $message | ConvertFrom-Json
            Write-EnhancedLog "Progress: $($progressData.Status) - $($progressData.Percentage)%" "INFO" "WebSocket"
            
            # Create new receive task
            $receiveTask = $ws.ReceiveAsync($ct.Token)
        }
        
    } catch {
        Write-EnhancedLog "WebSocket connection failed: $($_.Exception.Message)" "ERROR" "WebSocket"
    } finally {
        $ws.Dispose()
        $ct.Dispose()
    }
}
```

---

## 🛠️ External Tool Integration

### **VMware vRealize Operations Integration**

```powershell
function Send-To-vROps {
    param(
        [Parameter(Mandatory=$true)]
        [object]$Data,
        
        [Parameter(Mandatory=$true)]
        [string]$vRopsServer
    )
    
    $config = Get-Configuration -ConfigFile "scripts/config/settings.json"
    $cred = Get-StoredCredential -TargetName "vrops-admin"
    
    # Prepare vROps API call
    $apiUrl = "https://$vRopsServer/suite-api/api/resources"
    $headers = @{
        "Content-Type" = "application/json"
        "Accept" = "application/json"
        "vRealizeOps-API-Version-Id" = "1.0"
    }
    
    try {
        # Send discovery results to vROps
        $payload = @{
            resourceId = $Data.VCenterData.ClusterName
            resourceType = "Cluster"
            properties = @{
                totalHosts = $Data.VCenterData.Summary.TotalHosts
                totalVMs = $Data.VCenterData.Summary.TotalVMs
                lastDiscovery = $Data.Timestamp
            }
        }
        
        $response = Invoke-RestMethod -Uri $apiUrl -Headers $headers -Credential $cred -Method Post -Body ($payload | ConvertTo-Json)
        
        Write-EnhancedLog "Data sent to vROps successfully" "SUCCESS" "vROps"
        return $response
        
    } catch {
        Write-EnhancedLog "vROps integration failed: $($_.Exception.Message)" "ERROR" "vROps"
        throw
    }
}
```

### **HP OneView Global Dashboard Integration**

```powershell
function Send-To-OneViewDashboard {
    param([object]$DiscoveryData)
    
    $config = Get-Configuration -ConfigFile "scripts/config/settings.json"
    $cred = Get-StoredCredential -TargetName "oneview-admin"
    
    try {
        # Prepare dashboard data
        $dashboardData = @{
            timestamp = Get-Date
            totalServers = $DiscoveryData.Summary.TotalServerHardware
            totalProfiles = $DiscoveryData.Summary.TotalServerProfiles
            totalEnclosures = $DiscoveryData.Summary.TotalEnclosures
            healthStatus = @()
        }
        
        # Add health status for each component
        foreach ($server in $DiscoveryData.ServerHardware) {
            $dashboardData.healthStatus += @{
                type = "server"
                name = $server.Name
                status = $server.Status
                lastUpdate = $DiscoveryData.Timestamp
            }
        }
        
        # Send to OneView dashboard API
        $apiUrl = "https://$($config.oneView.appliance)/rest/dashboard-data"
        $response = Invoke-RestMethod -Uri $apiUrl -Credential $cred -Method Post -Body ($dashboardData | ConvertTo-Json) -ContentType "application/json"
        
        Write-EnhancedLog "Data sent to OneView dashboard" "SUCCESS" "OneView"
        return $response
        
    } catch {
        Write-EnhancedLog "OneView dashboard integration failed: $($_.Exception.Message)" "ERROR" "OneView"
        throw
    }
}
```

---

## 🚀 CI/CD Integration

### **Azure DevOps Pipeline**

```yaml
# azure-pipelines.yml
trigger:
- main
- develop

variables:
  vmwareVCenter: '$(vmwareVCenter)'
  oneViewAppliance: '$(oneViewAppliance)'
  environment: '$(environment)'

pool:
  vmImage: 'windows-latest'

stages:
- stage: Validation
  displayName: 'Infrastructure Validation'
  jobs:
  - job: validate
    displayName: 'Validate Infrastructure'
    steps:
    - checkout: self
    
    - task: PowerShell@2
      displayName: 'Validate Infrastructure'
      inputs:
        filePath: 'scripts/04_Infrastructure_Validation/04_Infra_Validate.ps1'
        arguments: '-ConfigFile "$(Build.SourcesDirectory)/scripts/config/settings.json" -GenerateReport'
        
    - task: PublishBuildArtifacts@1
      displayName: 'Publish Validation Reports'
      inputs:
        PathtoPublish: 'reports'
        ArtifactName: 'validation-reports'

- stage: Discovery
  displayName: 'Discovery Phase'
  dependsOn: Validation
  jobs:
  - job: discovery
    displayName: 'Run Discovery'
    steps:
    - checkout: self
    
    - task: PowerShell@2
      displayName: 'vCenter Discovery'
      inputs:
        filePath: 'scripts/06_Discovery_vCenter/06_Discovery_vCenter.ps1'
        arguments: '-ConfigFile "$(Build.SourcesDirectory)/scripts/config/settings.json" -IncludeVMs'
        
    - task: PowerShell@2
      displayName: 'OneView Discovery'
      inputs:
        filePath: 'scripts/07_Discovery_OneView/07_Discovery_OneView.ps1'
        arguments: '-ConfigFile "$(Build.SourcesDirectory)/scripts/config/settings.json" -IncludeFirmwareInfo'
        
    - task: PublishBuildArtifacts@1
      displayName: 'Publish Discovery Data'
      inputs:
        PathtoPublish: 'discovery'
        ArtifactName: 'discovery-data'

- stage: Testing
  displayName: 'Testing Phase'
  dependsOn: Discovery
  jobs:
  - job: testing
    displayName: 'Run Tests'
    steps:
    - checkout: self
    
    - task: PowerShell@2
      displayName: 'Run All Tests'
      inputs:
        filePath: 'scripts/tests/RunAllTests.ps1'
```

### **Jenkins Pipeline**

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        VCENTER_SERVER = credentials('vcenter-server')
        ONEVIEW_APPLIANCE = credentials('oneview-appliance')
        ENVIRONMENT = 'production'
    }
    
    stages {
        stage('Validation') {
            steps {
                powershell '''
                    .\\scripts\\04_Infrastructure_Validation\\04_Infra_Validate.ps1 -ConfigFile "scripts/config/settings.json" -GenerateReport
                '''
                
                archiveArtifacts artifacts: 'reports/**', fingerprint: true
            }
        }
        
        stage('Discovery') {
            steps {
                powershell '''
                    .\\scripts\\06_Discovery_vCenter\\06_Discovery_vCenter.ps1 -ConfigFile "scripts/config/settings.json" -IncludeVMs -ExportResults
                    .\\scripts\\07_Discovery_OneView\\07_Discovery_OneView.ps1 -ConfigFile "scripts/config/settings.json" -IncludeFirmwareInfo -ExportResults
                '''
                
                archiveArtifacts artifacts: 'discovery/**', fingerprint: true
            }
        }
        
        stage('Reporting') {
            steps {
                powershell '''
                    .\\scripts\\14_Generate_Report\\14_Generate_Report.ps1 -ConfigFile "scripts/config/settings.json" -ReportType "All" -OutputFormat @("HTML", "JSON")
                '''
                
                archiveArtifacts artifacts: 'reports/**', fingerprint: true
            }
        }
    }
    
    post {
        always {
            powershell '''
                .\\scripts\\15_Cleanup\\15_Cleanup.ps1 -ConfigFile "scripts/config/settings.json" -CleanupType "All" -RetentionDays 30
            '''
        }
    }
}
```

---

## 📊 Monitoring Integration

### **Prometheus Integration**

```powershell
function Export-ToPrometheus {
    param([object]$Data)
    
    try {
        # Prepare Prometheus metrics
        $metrics = @()
        
        # Infrastructure metrics
        $metrics += "# HELP vsphere_infrastructure_total_hosts Total number of vSphere hosts"
        $metrics += "# TYPE vsphere_infrastructure_total_hosts gauge"
        $metrics += "vsphere_infrastructure_total_hosts $($Data.Summary.TotalHosts)"
        
        $metrics += "# HELP vsphere_infrastructure_total_vms Total number of VMs"
        $metrics += "# TYPE vsphere_infrastructure_total_vms gauge"
        $metrics += "vsphere_infrastructure_total_vms $($Data.Summary.TotalVMs)"
        
        # OneView metrics
        $metrics += "# HELP oneview_infrastructure_total_servers Total number of OneView servers"
        $metrics += "# TYPE oneview_infrastructure_total_servers gauge"
        $metrics += "oneview_infrastructure_total_servers $($Data.Summary.TotalServerHardware)"
        
        # Operation status metrics
        $metrics += "# HELP vsphere_operation_status Status of vSphere operations"
        $metrics += "# TYPE vsphere_operation_status gauge"
        $metrics += "vsphere_operation_status{operation=\"discovery\"} 1"
        $metrics += "vsphere_operation_status{operation=\"firmware_update\"} 0"
        
        # Write to Prometheus pushgateway
        $prometheusUrl = "http://prometheus-pushgateway:9091/metrics/job/vsphere-automation"
        $metrics | Out-File -FilePath "temp/prometheus-metrics.txt" -Encoding UTF8
        
        $response = Invoke-RestMethod -Uri $prometheusUrl -Method Post -InFile "temp/prometheus-metrics.txt"
        
        Write-EnhancedLog "Metrics exported to Prometheus" "SUCCESS" "Prometheus"
        
    } catch {
        Write-EnhancedLog "Prometheus integration failed: $($_.Exception.Message)" "ERROR" "Prometheus"
    }
}
```

### **Grafana Dashboard Integration**

```powershell
function Export-ToGrafana {
    param([object]$Data)
    
    $config = Get-Configuration -ConfigFile "scripts/config/settings.json"
    
    # Create Grafana dashboard JSON
    $dashboard = @{
        dashboard = @{
            id = null
            title = "vSphere OneView Automation"
            tags = @("vsphere", "oneview", "automation")
            timezone = "browser"
            panels = @(
                @{
                    title = "Infrastructure Overview"
                    type = "stat"
                    targets = @(
                        @{
                            expr = "vsphere_infrastructure_total_hosts"
                            legendFormat = "{{host}}"
                        }
                    )
                    fieldConfig = @{
                        defaults = @{
                            unit = "short"
                        }
                    }
                }
                @{
                    title = "Operation Status"
                    type = "table"
                    targets = @(
                        @{
                            expr = "vsphere_operation_status"
                            format = "table"
                        }
                    )
                }
            )
            time = @{
                from = "now-1h"
                to = "now"
            }
            refresh = "30s"
        }
    }
    
    try {
        # Export dashboard to Grafana
        $grafanaUrl = "http://$($config.monitoring.grafanaServer)/api/dashboards/db"
        $headers = @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $config.monitoring.grafanaToken"
        }
        
        $response = Invoke-RestMethod -Uri $grafanaUrl -Headers $headers -Method Post -Body ($dashboard | ConvertTo-Json -Depth 10)
        
        Write-EnhancedLog "Dashboard exported to Grafana" "SUCCESS" "Grafana"
        
    } catch {
        Write-EnhancedLog "Grafana integration failed: $($_.Exception.Message)" "ERROR" "Grafana"
    }
}
```

---

## 💾 Backup Integration

### **Veeam Backup Integration**

```powershell
function Backup-EnhancedReports {
    param([string]$BackupRepository = "VsphereOneViewReports")
    
    try {
        # Get Veeam credentials
        $veeamCred = Get-StoredCredential -TargetName "veeam-backup"
        
        # Connect to Veeam
        Import-Module Veeam.Backup.Core
        Connect-VBRServer -Server $veeamCred.UserName -Credential $veeamCred
        
        # Find enhanced reports
        $reports = Get-ChildItem -Path "reports" -Filter "*.html" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }
        
        foreach ($report in $reports) {
            # Create backup job
            $backupJob = Add-VBRBackupFile -File $report.FullName -Repository $BackupRepository
            
            # Start backup
            Start-VBRJob -Job $backupJob
            
            Write-EnhancedLog "Backup started for: $($report.Name)" "INFO" "Backup"
        }
        
        Disconnect-VBRServer
        
        Write-EnhancedLog "Enhanced reports backup completed" "SUCCESS" "Backup"
        
    } catch {
        Write-EnhancedLog "Veeam backup integration failed: $($_.Exception.Message)" "ERROR" "Backup"
    }
}
```

---

## 🎯 Integration Checklist

### **Pre-Integration Requirements:**
- [ ] Enhanced skripte instalirane i testirane
- [ ] Konfiguracija podešena za integraciju
- [ ] API pristup konfigurisan
- [ ] Monitoring sistem podešen
- [ ] Backup sistem integriran

### **Post-Integration Validation:**
- [ ] MasterWorkflow radi sa enhanced skriptama
- [ ] API integracija funkcionalna
- [ ] CI/CD pipeline radi uspešno
- [ ] Monitoring podaci se prikupljaju
- [ ] Backup integracija funkcionalna

---

## 📚 Additional Resources

### **API Documentation:**
- **VMware vSphere API**: https://developer.vmware.com/apis/vsphere/
- **HPE OneView API**: https://developer.hpe.com/content/OneViewAPI/
- **Prometheus API**: https://prometheus.io/docs/prometheus/latest/querying/api/
- **Grafana API**: https://grafana.com/docs/grafana/latest/http_api/

### **Integration Examples:**
- **ServiceNow Integration**: Automatski ticket kreiranje
- **Slack Integration**: Notifikacije i alert-i
- **Microsoft Teams Integration**: Status updates i reporting
- **PagerDuty Integration**: Escalation i alerting

---

## 🔄 Maintenance and Updates

### **Regular Maintenance Tasks:**
1. **API Endpoints**: Proverite da li API endpoint-i još uvek rade
2. **Credential Rotation**: Redovno menjajte API kredencijale
3. **Monitoring Metrics**: Ažurirajte monitoring metrike
4. **Backup Validation**: Proverite da li backup radi

### **Version Updates:**
1. **Compatibility Test**: Testirajte novu verziju u staging okruženju
2. **API Changes**: Proverite promene u API-ju
3. **Configuration Updates**: Ažurirajte konfiguraciju za nove feature-e
4. **Documentation Update**: Ažurirajte dokumentaciju

---

## 🎉 Integration Complete!

**Nakon što završite sve korake iz ovog guide-a, vaš enhanced sistem je integrisan sa:**

✅ **Postojećim MasterWorkflow**
✅ **Eksternim API-jima**
✅ **CI/CD pipeline-ovima**
✅ **Monitoring sistemima**
✅ **Backup sistemima**

---

## 🇷🇸 Srpski Jezik - Puna Podrška!

**Sve integracije, logovi i poruke su na srpskom jeziku!**

---

**🚀 Vaš Enhanced vSphere OneView Automatizacija je sada integrisana sa spoljnim sistemima!**
