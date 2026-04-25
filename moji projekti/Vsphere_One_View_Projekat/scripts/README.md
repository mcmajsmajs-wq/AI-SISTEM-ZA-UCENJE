# vSphere OneView Automation Suite - Scripts

## Overview
This directory contains the complete automation suite for HPE Synergy and VMware vSphere infrastructure patching and management.

## Directory Structure

```
scripts/
├── 01_Discovery/       # Discovery and inventory mapping scripts
├── 02_Staging/         # Staging and preparation scripts  
├── 03_Execution/       # Execution and remediation scripts
├── 04_PostCheck/       # Post-execution validation scripts
├── 05_Utility/         # Shared utility functions
├── docs/              # Documentation
├── config/            # Configuration files
├── tests/             # Testing framework
├── backups/           # Backup directory structure
└── tools/             # Additional tools
```

## Quick Start

### 1. Prerequisites
- PowerShell 5.1 or later
- VMware PowerCLI 12+
- HPE OneView PowerShell Library
- Windows Credential Manager (for secure credential storage)

### 2. Installation
```powershell
# Install prerequisites
.\05_Utility\Install-Prerequisites.ps1

# Configure settings (copy templates and modify)
Copy-Item config\settings.template.json config\settings.json
Copy-Item config\credentials.template.json config\credentials.json

# Set up secure credentials
.\05_Utility\CredentialManager.ps1 -Action Store

# Test installation
.\tests\RunAllTests.ps1 -TestType All
```

### 3. Basic Usage
```powershell
# Run master workflow (all phases in simulation)
.\MasterWorkflow.ps1 -Phase All -Simulation

# Run specific phase
.\MasterWorkflow.ps1 -Phase Discovery -Simulation
.\MasterWorkflow.ps1 -Phase Execution -Simulation:$false

# Run with environment-specific configuration
.\MasterWorkflow.ps1 -Phase All -Environment production
```

## Script Categories

### 01_Discovery/
Discovery and inventory mapping scripts:
- `01_Inventory_Check.ps1` - Basic inventory checking
- `01_Inventory_Check_Robust.ps1` - Enhanced inventory with error handling
- `01_Cluster_Synergy_Mapping.ps1` - Map vSphere clusters to Synergy frames
- `RunDiscovery.ps1` - Orchestrator for discovery phase

### 02_Staging/
Staging and preparation scripts:
- `02_Staging.ps1` - Firmware bundle staging
- `02_Check_Staging_Status.ps1` - Check staging status
- `02_SingleHost_Staging_Audit.ps1` - Audit staging for single host
- `02_Ensure_Staged_Status.ps1` - Ensure staging is complete
- `RunStaging.ps1` - Orchestrator for staging phase

### 03_Execution/
Execution and remediation scripts:
- `03_Execution.ps1` - Enhanced execution skeleton
- `03_Remediation_With_Monitoring.ps1` - Remediation with monitoring
- `Synergy_VMware_Master_Patch.ps1` - Master patching workflow
- `RunExecution.ps1` - Orchestrator for execution phase

### 04_PostCheck/
Post-execution validation scripts:
- `04_PostCheck.ps1` - Post-execution verification
- `RunPostCheck.ps1` - Orchestrator for post-check phase

### 05_Utility/
Shared utility functions:
- `Logger.ps1` - Centralized logging framework
- `ConnectionManager.ps1` - Safe connection handling
- `CredentialManager.ps1` - Secure credential management
- `ConfigManager.ps1` - Configuration management
- `ValidationEngine.ps1` - Input validation
- `ErrorHandler.ps1` - Error handling and recovery
- `Install-Prerequisites.ps1` - Prerequisites installer

## Configuration

### Configuration Files
- `config/settings.json` - Main configuration settings
- `config/credentials.json` - Encrypted credential storage
- `config/environments/` - Environment-specific configurations
- `config/schemas/` - JSON validation schemas

### Configuration Structure
See `settings.template.json` for complete configuration options.

## Testing

### Running Tests
```powershell
# Run all tests
.\tests\RunAllTests.ps1 -TestType All -Verbose

# Run specific test types
.\tests\RunAllTests.ps1 -TestType Unit
.\tests\RunAllTests.ps1 -TestType Integration
.\tests\RunAllTests.ps1 -TestType Mock
```

### Test Categories
- **Unit Tests**: Test individual functions and modules
- **Integration Tests**: Test component integration
- **Mock Tests**: Test with mock APIs

## Security Features

- **No Hardcoded Credentials**: All credentials stored securely
- **Encrypted Storage**: Passwords encrypted at rest
- **Connection Validation**: Health checks for all connections
- **Input Validation**: Comprehensive parameter validation
- **Error Handling**: Robust error handling and recovery

## Workflow Phases

### 1. Discovery
- Inventory collection and mapping
- Cluster to Synergy frame mapping
- Health checks and validation

### 2. Staging
- Firmware bundle preparation
- OneView configuration staging
- vSphere patch staging

### 3. Execution
- Sequential host patching
- Maintenance mode management
- Firmware updates and reboots

### 4. PostCheck
- Validation of completed work
- Health and compliance checks
- Report generation

## Troubleshooting

### Common Issues
1. **Connection Failures**: Check network connectivity and credentials
2. **Module Missing**: Run `Install-Prerequisites.ps1`
3. **Configuration Errors**: Validate JSON syntax and required fields
4. **Permission Issues**: Ensure proper vSphere and OneView permissions

### Debug Mode
Enable debug mode in configuration:
```json
{
    "system": {
        "debugMode": true,
        "logLevel": "DEBUG"
    }
}
```

### Log Analysis
Check log files in `logs/` directory:
- `logs/master/` - Master workflow logs
- `logs/discovery/` - Discovery phase logs
- `logs/staging/` - Staging phase logs
- `logs/execution/` - Execution phase logs
- `logs/postcheck/` - Post-check phase logs

## Best Practices

1. **Always Test in Simulation Mode**: Use `-Simulation` parameter first
2. **Backup Configuration**: Maintain version control of configurations
3. **Monitor Logs**: Regularly check logs for issues and trends
4. **Validate Prerequisites**: Ensure all requirements are met before execution
5. **Use Rollback**: Ensure rollback procedures are in place

## Support

For additional help:
1. Check phase-specific documentation in `docs/` directory
2. Run troubleshooting tools in `tools/` directory
3. Review test results for common issues
4. Check error logs for detailed error information

---
**Version:** 1.0.0  
**Last Updated:** 2026-02-01
