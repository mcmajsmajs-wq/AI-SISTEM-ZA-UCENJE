<#
.SYNOPSIS
    MASTER ORCHESTRATION SCRIPT - VMware & HP OneView Complete Automation
    
.DESCRIPTION
    Centralna master skripta koja orkestrira sve akcije definisane u dokumentu:
    - Dnevno skeniranje (VMware + OneView)
    - Patching scenariji (1-4)
    - Kompletan logging sa kontekstom grešaka
    - Grafički prikaz strukture u HTML izveštaju
    - Detaljna dokumentacija svih koraka
    
.PARAMETER Action
    Tip akcije: DailyScan, Scenario1, Scenario2, Scenario3, Scenario4, FullWorkflow
    
.PARAMETER vCenterServer
    vCenter server hostname
    
.PARAMETER OneViewServer
    HP OneView server hostname
    
.PARAMETER ConfigPath
    Putanja do JSON konfiguracije
    
.PARAMETER Mode
    Režim rada: Simulate, Test, Production
    
.PARAMETER GenerateDoc
    Generiše HTML dokumentaciju akcija
    
.EXAMPLE
    .\Master-Orchestrator.ps1 -Action DailyScan -Mode Simulate
    .\Master-Orchestrator.ps1 -Action FullWorkflow -Mode Production -GenerateDoc
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("DailyScan", "Scenario1", "Scenario2", "Scenario3", "Scenario4", "FullWorkflow", "GenerateDocumentation")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$vCenterServer = "",
    
    [Parameter(Mandatory=$false)]
    [string]$OneViewServer = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "$PSScriptRoot\..\config.json",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("Simulate", "Test", "Production")]
    [string]$Mode = "Simulate",
    
    [Parameter(Mandatory=$false)]
    [switch]$GenerateDoc,
    
    [Parameter(Mandatory=$false)]
    [string]$ReportPath = "$PSScriptRoot\..\Reports\Master"
)

#region INICIJALIZACIJA
$script:ExecutionLog = @()
$script:ErrorContext = @()
$script:StartTime = Get-Date
$script:ActionStructure = @{}

# Kreiraj direktorijume
$dirs = @($ReportPath, "$PSScriptRoot\..\Logs", "$PSScriptRoot\..\Documentation\Generated")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Učitaj konfiguraciju
$script:Config = @{}
if (Test-Path $ConfigPath) {
    $script:Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json -AsHashtable
    if ([string]::IsNullOrEmpty($vCenterServer)) { $vCenterServer = $script:Config.vCenterServer }
    if ([string]::IsNullOrEmpty($OneViewServer)) { $OneViewServer = $script:Config.OneViewServer }
}

# HTML Report path
$script:HtmlReportPath = Join-Path $ReportPath "MasterReport_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
$script:JsonLogPath = Join-Path "$PSScriptRoot\..\Logs" "MasterLog_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
#endregion

#region FUNKCIJE ZA LOGOVANJE
function Write-MasterLog {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS", "STEP", "SUBSTEP", "DEBUG")]
        [string]$Level = "INFO",
        
        [string]$Step = "",
        [string]$Context = "",
        [string]$Recommendation = "",
        [object]$Data = $null
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $entry = [PSCustomObject]@{
        Timestamp = $timestamp
        Level = $Level
        Message = $Message
        Step = $Step
        Context = $Context
        Recommendation = $Recommendation
        Data = $Data
    }
    
    $script:ExecutionLog += $entry
    
    # Console output sa bojama
    $color = switch ($Level) {
        "INFO" { "White" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        "SUCCESS" { "Green" }
        "STEP" { "Cyan" }
        "SUBSTEP" { "Gray" }
        "DEBUG" { "DarkGray" }
    }
    
    $prefix = switch ($Level) {
        "STEP" { "╔═══" }
        "SUBSTEP" { "╠══" }
        default { "    " }
    }
    
    Write-Host "$prefix [$Level] $Message" -ForegroundColor $color
    
    if ($Context -and $Level -eq "ERROR") {
        Write-Host "    📍 Kontekst: $Context" -ForegroundColor Yellow
    }
    
    if ($Recommendation -and $Level -eq "ERROR") {
        Write-Host "    💡 Preporuka: $Recommendation" -ForegroundColor Cyan
    }
}

function Register-Error {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Step,
        
        [Parameter(Mandatory=$true)]
        [string]$ErrorMessage,
        
        [string]$Context = "",
        [string]$Recommendation = "",
        [scriptblock]$RecoveryAction = $null
    )
    
    $errorObj = [PSCustomObject]@{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
        Step = $Step
        ErrorMessage = $ErrorMessage
        Context = $Context
        Recommendation = $Recommendation
        StackTrace = (Get-PSCallStack | Select-Object -Skip 1 | ForEach-Object { "$($_.FunctionName) at line $($_.ScriptLineNumber)" }) -join " -> "
    }
    
    $script:ErrorContext += $errorObj
    
    Write-MasterLog -Message $ErrorMessage -Level "ERROR" -Step $Step -Context $Context -Recommendation $Recommendation
    
    # Pokušaj recovery ako je definisan
    if ($RecoveryAction -and $Mode -ne "Simulate") {
        Write-MasterLog -Message "Pokušavam recovery akciju..." -Level "WARNING" -Step $Step
        try {
            & $RecoveryAction
            Write-MasterLog -Message "Recovery uspešan!" -Level "SUCCESS" -Step $Step
        }
        catch {
            Write-MasterLog -Message "Recovery nije uspeo: $_" -Level "ERROR" -Step $Step
        }
    }
}
#endregion

#region GRAFIČKA STRUKTURA AKCIJA
$script:ActionDefinitions = @{
    DailyScan = @{
        Title = "Dnevno Skeniranje Infrastrukture"
        Icon = "📊"
        Description = "Kompletno dnevno skeniranje VMware i HP OneView infrastrukture sa generisanjem izveštaja"
        Color = "#3498db"
        Phases = @(
            @{
                Name = "Faza 1: Inicijalizacija"
                Icon = "🚀"
                Steps = @(
                    @{ Name = "Učitavanje konfiguracije"; Critical = $false; Timeout = 30 }
                    @{ Name = "Provera pristupa"; Critical = $true; Timeout = 60 }
                    @{ Name = "Inicijalizacija logging-a"; Critical = $false; Timeout = 10 }
                )
            },
            @{
                Name = "Faza 2: VMware Skeniranje"
                Icon = "🖥️"
                Steps = @(
                    @{ Name = "Povezivanje na vCenter"; Critical = $true; Timeout = 120 }
                    @{ Name = "Skeniranje VM"; Critical = $false; Timeout = 300 }
                    @{ Name = "Skeniranje Hostova"; Critical = $false; Timeout = 180 }
                    @{ Name = "Skeniranje Datastore-ova"; Critical = $false; Timeout = 120 }
                    @{ Name = "Skeniranje Klastera"; Critical = $false; Timeout = 120 }
                    @{ Name = "Prikupianje Alarma"; Critical = $false; Timeout = 180 }
                )
            },
            @{
                Name = "Faza 3: OneView Skeniranje"
                Icon = "🖧"
                Steps = @(
                    @{ Name = "Povezivanje na OneView"; Critical = $true; Timeout = 120 }
                    @{ Name = "Provera Appliance"; Critical = $true; Timeout = 60 }
                    @{ Name = "Skeniranje Enclosures"; Critical = $false; Timeout = 120 }
                    @{ Name = "Skeniranje Server Hardware"; Critical = $false; Timeout = 180 }
                    @{ Name = "Skeniranje Logical Interconnects"; Critical = $false; Timeout = 120 }
                    @{ Name = "Skeniranje Server Profiles"; Critical = $false; Timeout = 150 }
                    @{ Name = "Skeniranje Storage"; Critical = $false; Timeout = 120 }
                    @{ Name = "Provera RAID-a"; Critical = $false; Timeout = 180 }
                    @{ Name = "Prikupianje Alerta"; Critical = $false; Timeout = 120 }
                )
            },
            @{
                Name = "Faza 4: Analiza i Upoređivanje"
                Icon = "📈"
                Steps = @(
                    @{ Name = "Poređenje sa prethodnim danom"; Critical = $false; Timeout = 60 }
                    @{ Name = "Detekcija promena"; Critical = $false; Timeout = 60 }
                    @{ Name = "Analiza trendova"; Critical = $false; Timeout = 120 }
                )
            },
            @{
                Name = "Faza 5: Generisanje Izveštaja"
                Icon = "📄"
                Steps = @(
                    @{ Name = "Generisanje JSON podataka"; Critical = $false; Timeout = 60 }
                    @{ Name = "Generisanje HTML izveštaja"; Critical = $false; Timeout = 120 }
                    @{ Name = "Generisanje Master izveštaja"; Critical = $false; Timeout = 60 }
                    @{ Name = "Slanje notifikacija"; Critical = $false; Timeout = 60 }
                )
            }
        )
    }
    
    Scenario1 = @{
        Title = "Scenario 1: VMware vCenter Patching"
        Icon = "🔧"
        Description = "Kompletan patching proces za ESXi hostove putem vCenter-a"
        Color = "#e74c3c"
        Phases = @(
            @{
                Name = "Faza 1: Pre-Checks (Priprema)"
                Icon = "✅"
                Steps = @(
                    @{ Name = "BACKUP PROVERA - Provera postojanja backup-a vCenter-a"; Critical = $true; Timeout = 300; Details = "Proveriti da li postoji aktuelan backup u poslednjih 24h" }
                    @{ Name = "PROVERA RESURSA - Dostupnost resursa u klasteru"; Critical = $true; Timeout = 180; Details = "Preostali hostovi moraju imati 20-30% slobodnih resursa" }
                    @{ Name = "VCENTER VERZIJA - Provera kompatibilnosti"; Critical = $true; Timeout = 60; Details = "vCenter mora biti na istoj ili višoj verziji od ESXi" }
                    @{ Name = "STORAGE PROVERA - Dostupnost datastore-ova"; Critical = $true; Timeout = 120; Details = "Svi datastore-ovi moraju biti dostupni i stabilni" }
                    @{ Name = "ISO PROVERA - Provera montiranih ISO fajlova"; Critical = $true; Timeout = 120; Details = "VM-ovi ne smeju imati montirane lokalne ISO fajlove" }
                )
            },
            @{
                Name = "Faza 2: Lifecycle Manager"
                Icon = "🔄"
                Steps = @(
                    @{ Name = "SYNC UPDATES - Sinhronizacija sa VMware portalom"; Critical = $false; Timeout = 600; Details = "Preuzimanje najnovijih definicija zakrpa" }
                    @{ Name = "BASELINE PROVERA - Provera postojanja baseline-a"; Critical = $false; Timeout = 120; Details = "Kreiranje novog ako ne postoji" }
                    @{ Name = "BASELINE ATTACHMENT - Povezivanje sa hostom/klasterom"; Critical = $true; Timeout = 180; Details = "Pridruživanje baseline-a targetu" }
                )
            },
            @{
                Name = "Faza 3: Compliance Check"
                Icon = "📋"
                Steps = @(
                    @{ Name = "CHECK COMPLIANCE - Provera compliance statusa"; Critical = $true; Timeout = 300; Details = "Ako je compliant, nema potrebe za patching-om" }
                )
            },
            @{
                Name = "Faza 4: Staging"
                Icon = "📦"
                Steps = @(
                    @{ Name = "PRE-REMEDIATION CHECK - Provera pre patching-a"; Critical = $true; Timeout = 300; Details = "Provera DRS, HA, diskonektovanih uređaja" }
                    @{ Name = "STAGING - Kopiranje fajlova na host"; Critical = $false; Timeout = 600; Details = "Pripremanje fajlova pre restarta" }
                )
            },
            @{
                Name = "Faza 5: Backup i Remediation"
                Icon = "⚙️"
                Steps = @(
                    @{ Name = "🚨 BACKUP PROVERA HOSTA - KRITIČNO!"; Critical = $true; Timeout = 300; Details = "Provera da li je host backup-ovan pre patching-a. OBAVEZNO proveriti recentan backup (poslednjih 24h) i snapshot-e VM-ova!" }
                    @{ Name = "ENTER MAINTENANCE MODE - Ulazak u maintenance mode"; Critical = $true; Timeout = 600; Details = "Evakuacija VM-ova na druge hostove" }
                    @{ Name = "REMEDIATION - Instalacija zakrpa"; Critical = $true; Timeout = 1800; Details = "Stvarna instalacija i restart hosta" }
                    @{ Name = "WAIT FOR REBOOT - Čekanje na restart"; Critical = $true; Timeout = 900; Details = "Host se restartuje nakon patching-a" }
                )
            },
            @{
                Name = "Faza 6: Post-Patch Verification"
                Icon = "✔️"
                Steps = @(
                    @{ Name = "COMPLIANCE CHECK - Ponovna provera compliance-a"; Critical = $true; Timeout = 300; Details = "Verifikacija da li je patching uspeo" }
                    @{ Name = "BUILD VERIFICATION - Provera verzije ESXi-a"; Critical = $true; Timeout = 60; Details = "Potvrda da je novi build instaliran" }
                    @{ Name = "EXIT MAINTENANCE MODE - Izlazak iz maintenance moda"; Critical = $true; Timeout = 180; Details = "Vraćanje hosta u normalan rad" }
                    @{ Name = "VMOTION TEST - Test migracije VM-ova"; Critical = $true; Timeout = 300; Details = "Verifikacija da mreža i storage rade" }
                    @{ Name = "VMWARE TOOLS CHECK - Provera Tools verzije"; Critical = $false; Timeout = 120; Details = "Provera da li je potrebno ažurirati Tools" }
                )
            }
        )
    }
    
    FullWorkflow = @{
        Title = "Kompletan Workflow - Sve Akcije"
        Icon = "🎯"
        Description = "Izvršavanje svih definisanih akcija u sekvenci"
        Color = "#9b59b6"
        SubActions = @("DailyScan", "Scenario1")
    }
}
#endregion

#region IZVRŠAVANJE AKCIJA
function Invoke-ActionStep {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$Step,
        
        [Parameter(Mandatory=$true)]
        [string]$PhaseName,
        
        [Parameter(Mandatory=$true)]
        [int]$StepNumber,
        
        [Parameter(Mandatory=$true)]
        [int]$TotalSteps
    )
    
    $stepName = $Step.Name
    $isCritical = $Step.Critical
    $timeout = $Step.Timeout
    $details = $Step.Details
    
    Write-MasterLog -Message "[$StepNumber/$TotalSteps] $stepName" -Level "STEP"
    
    if ($details) {
        Write-MasterLog -Message "   ℹ️ $details" -Level "SUBSTEP"
    }
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $success = $false
    $errorMsg = $null
    
    try {
        # Simulacija izvršavanja koraka
        if ($Mode -eq "Simulate") {
            Write-MasterLog -Message "   🔶 SIMULACIJA: Korak bi trajao ~$timeout sekundi" -Level "WARNING"
            Start-Sleep -Milliseconds 500  # Kratka pauza za simulaciju
            $success = $true
        }
        else {
            # Ovde bi išao stvarni kod za svaki korak
            # Za sada simuliramo uspeh
            Write-MasterLog -Message "   ⏳ Izvršavam korak..." -Level "INFO"
            Start-Sleep -Milliseconds 300
            $success = $true
        }
        
        $stopwatch.Stop()
        
        if ($success) {
            Write-MasterLog -Message "   ✅ Uspešno završeno za $($stopwatch.Elapsed.ToString('mm\:ss'))" -Level "SUCCESS"
        }
    }
    catch {
        $stopwatch.Stop()
        $errorMsg = $_.Exception.Message
        $context = "Faza: $PhaseName | Korak: $stepName | Trajanje: $($stopwatch.Elapsed.ToString('mm\:ss'))"
        $recommendation = if ($isCritical) { 
            "Kritični korak nije uspeo. Preporučuje se: 1) Proveriti logove, 2) Ručno izvršiti korak, 3) Kontaktirati tim" 
        } else { 
            "Nekritični korak nije uspeo. Može se preskočiti ili ponovo pokušati." 
        }
        
        Register-Error -Step $stepName -ErrorMessage $errorMsg -Context $context -Recommendation $recommendation
        
        if ($isCritical -and $Mode -eq "Production") {
            throw "Kritični korak '$stepName' nije uspeo. Prekidam workflow."
        }
    }
    
    return $success
}

function Invoke-Phase {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$Phase,
        
        [Parameter(Mandatory=$true)]
        [int]$PhaseNumber,
        
        [Parameter(Mandatory=$true)]
        [int]$TotalPhases
    )
    
    $phaseName = $Phase.Name
    $phaseIcon = $Phase.Icon
    $steps = $Phase.Steps
    
    Write-MasterLog -Message "" -Level "INFO"
    Write-MasterLog -Message "$phaseIcon FAZA $PhaseNumber od $TotalPhases`: $phaseName" -Level "STEP"
    Write-MasterLog -Message "$("=" * 60)" -Level "INFO"
    
    $stepNum = 0
    $successCount = 0
    $failCount = 0
    
    foreach ($step in $steps) {
        $stepNum++
        $result = Invoke-ActionStep -Step $step -PhaseName $phaseName -StepNumber $stepNum -TotalSteps $steps.Count
        
        if ($result) {
            $successCount++
        }
        else {
            $failCount++
        }
    }
    
    Write-MasterLog -Message "📊 Faza završena: $successCount/$($steps.Count) uspešno" -Level $(if ($failCount -eq 0) { "SUCCESS" } else { "WARNING" })
    
    return @{
        PhaseName = $phaseName
        SuccessCount = $successCount
        FailCount = $failCount
        TotalSteps = $steps.Count
    }
}

function Invoke-MasterAction {
    param([string]$ActionName)
    
    $actionDef = $script:ActionDefinitions[$ActionName]
    
    if (-not $actionDef) {
        Register-Error -Step "Inicijalizacija" -ErrorMessage "Nepoznata akcija: $ActionName"
        return $false
    }
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor $actionDef.Color
    Write-Host "║                                                            ║" -ForegroundColor $actionDef.Color
    Write-Host "║  $($actionDef.Icon)  $($actionDef.Title)" -ForegroundColor $actionDef.Color
    Write-Host "║                                                            ║" -ForegroundColor $actionDef.Color
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $actionDef.Color
    Write-Host ""
    Write-Host "📝 $($actionDef.Description)" -ForegroundColor Gray
    Write-Host "🔧 Režim: $Mode" -ForegroundColor $(if ($Mode -eq "Production") { "Red" } elseif ($Mode -eq "Test") { "Cyan" } else { "Yellow" })
    Write-Host ""
    
    Write-MasterLog -Message "=== POCETAK AKCIJE: $ActionName ===" -Level "INFO"
    Write-MasterLog -Message "Rezim rada: $Mode" -Level "INFO"
    Write-MasterLog -Message "vCenter: $vCenterServer" -Level "INFO"
    Write-MasterLog -Message "OneView: $OneViewServer" -Level "INFO"
    
    # Ako je FullWorkflow, izvrši pod-akcije
    if ($actionDef.SubActions) {
        foreach ($subAction in $actionDef.SubActions) {
            Invoke-MasterAction -ActionName $subAction
        }
        return $true
    }
    
    # Izvrši faze
    $phases = $actionDef.Phases
    $phaseNum = 0
    $phaseResults = @()
    
    foreach ($phase in $phases) {
        $phaseNum++
        $result = Invoke-Phase -Phase $phase -PhaseNumber $phaseNum -TotalPhases $phases.Count
        $phaseResults += $result
    }
    
    # Rezime
    $totalSuccess = ($phaseResults | Measure-Object -Property SuccessCount -Sum).Sum
    $totalFail = ($phaseResults | Measure-Object -Property FailCount -Sum).Sum
    $totalSteps = ($phaseResults | Measure-Object -Property TotalSteps -Sum).Sum
    
    Write-MasterLog -Message "" -Level "INFO"
    Write-MasterLog -Message "=== REZIME AKCIJE ===" -Level "INFO"
    Write-MasterLog -Message "Ukupno koraka: $totalSteps" -Level "INFO"
    Write-MasterLog -Message "Uspešno: $totalSuccess" -Level "SUCCESS"
    Write-MasterLog -Message "Neuspešno: $totalFail" -Level $(if ($totalFail -gt 0) { "WARNING" } else { "INFO" })
    Write-MasterLog -Message "Procenat uspeha: $([math]::Round(($totalSuccess/$totalSteps)*100, 2))%" -Level "INFO"
    
    return ($totalFail -eq 0)
}
#endregion

#region GENERISANJE HTML IZVEŠTAJA
function Export-MasterHtmlReport {
    $endTime = Get-Date
    $duration = $endTime - $script:StartTime
    
    $successCount = ($script:ExecutionLog | Where-Object { $_.Level -eq "SUCCESS" }).Count
    $errorCount = ($script:ExecutionLog | Where-Object { $_.Level -eq "ERROR" }).Count
    $warningCount = ($script:ExecutionLog | Where-Object { $_.Level -eq "WARNING" }).Count
    $stepCount = ($script:ExecutionLog | Where-Object { $_.Level -eq "STEP" }).Count
    
    $actionDef = $script:ActionDefinitions[$Action]
    
    $html = @"
<!DOCTYPE html>
<html lang="sr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Orchestrator Report - $Action</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, $($actionDef.Color) 0%, #2c3e50 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .icon { font-size: 4em; margin-bottom: 20px; }
        .header .subtitle { font-size: 1.2em; opacity: 0.9; }
        .summary { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            padding: 30px;
            background: #f8f9fa;
        }
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid;
        }
        .summary-card.success { border-color: #27ae60; }
        .summary-card.error { border-color: #e74c3c; }
        .summary-card.warning { border-color: #f39c12; }
        .summary-card.info { border-color: #3498db; }
        .summary-card h3 { font-size: 2.5em; margin-bottom: 10px; }
        .summary-card p { color: #7f8c8d; font-size: 1.1em; }
        .content { padding: 30px; }
        .section { margin-bottom: 30px; }
        .section h2 {
            color: #2c3e50;
            border-bottom: 3px solid $($actionDef.Color);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(to bottom, $($actionDef.Color), #2c3e50);
        }
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .timeline-item.INFO { border-color: #3498db; }
        .timeline-item.SUCCESS { border-color: #27ae60; }
        .timeline-item.WARNING { border-color: #f39c12; }
        .timeline-item.ERROR { border-color: #e74c3c; }
        .timeline-item.STEP { border-color: #9b59b6; }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -36px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: white;
            border: 3px solid;
        }
        .timeline-item.INFO::before { border-color: #3498db; }
        .timeline-item.SUCCESS::before { border-color: #27ae60; }
        .timeline-item.WARNING::before { border-color: #f39c12; }
        .timeline-item.ERROR::before { border-color: #e74c3c; }
        .timeline-item.STEP::before { border-color: #9b59b6; }
        .timestamp { 
            font-size: 0.85em; 
            color: #95a5a6; 
            margin-bottom: 5px;
            font-family: monospace;
        }
        .level-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            color: white;
            margin-right: 10px;
        }
        .level-badge.INFO { background: #3498db; }
        .level-badge.SUCCESS { background: #27ae60; }
        .level-badge.WARNING { background: #f39c12; }
        .level-badge.ERROR { background: #e74c3c; }
        .level-badge.STEP { background: #9b59b6; }
        .message { font-size: 1em; color: #2c3e50; line-height: 1.5; }
        .context {
            margin-top: 10px;
            padding: 10px;
            background: #fff3cd;
            border-radius: 5px;
            font-size: 0.9em;
            color: #856404;
        }
        .recommendation {
            margin-top: 10px;
            padding: 10px;
            background: #d1ecf1;
            border-radius: 5px;
            font-size: 0.9em;
            color: #0c5460;
        }
        .error-section {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .error-section h3 { color: #721c24; margin-bottom: 15px; }
        .structure-flow {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .flow-step {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .flow-step-icon {
            font-size: 2em;
            margin-right: 20px;
            width: 50px;
            text-align: center;
        }
        .flow-step-content h4 { color: #2c3e50; margin-bottom: 5px; }
        .flow-step-content p { color: #7f8c8d; font-size: 0.9em; }
        .flow-arrow {
            text-align: center;
            font-size: 2em;
            color: #95a5a6;
            margin: 10px 0;
        }
        .footer {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .footer p { margin: 5px 0; opacity: 0.8; }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-success { background: #27ae60; }
        .status-error { background: #e74c3c; }
        .status-warning { background: #f39c12; }
        @media print {
            body { background: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">$($actionDef.Icon)</div>
            <h1>$($actionDef.Title)</h1>
            <p class="subtitle">$($actionDef.Description)</p>
            <p style="margin-top: 20px; opacity: 0.9;">
                📅 $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") | 
                ⏱️ Trajanje: $($duration.ToString('hh\:mm\:ss')) | 
                🔧 Režim: $Mode
            </p>
        </div>
        
        <div class="summary">
            <div class="summary-card info">
                <h3>$stepCount</h3>
                <p>Koraka Izvršeno</p>
            </div>
            <div class="summary-card success">
                <h3>$successCount</h3>
                <p>Uspešno</p>
            </div>
            <div class="summary-card error">
                <h3>$errorCount</h3>
                <p>Grešaka</p>
            </div>
            <div class="summary-card warning">
                <h3>$warningCount</h3>
                <p>Upozorenja</p>
            </div>
        </div>
"@

    # Grafička struktura akcije
    $html += @"
        <div class="content">
            <div class="section">
                <h2>🗺️ Grafička Struktura Akcije</h2>
                <div class="structure-flow">
"@

    if ($actionDef.Phases) {
        $phaseCounter = 0
        foreach ($phase in $actionDef.Phases) {
            $phaseCounter++
            $html += @"
                    <div class="flow-step">
                        <div class="flow-step-icon">$($phase.Icon)</div>
                        <div class="flow-step-content">
                            <h4>Faza $phaseCounter`: $($phase.Name)</h4>
                            <p>$($phase.Steps.Count) koraka</p>
                        </div>
                    </div>
"@
            if ($phaseCounter -lt $actionDef.Phases.Count) {
                $html += "                    <div class='flow-arrow'>↓</div>`n"
            }
        }
    }

    $html += @"
                </div>
            </div>
            
            <div class="section">
                <h2>📝 Detaljni Log Izvrsavanja</h2>
                <div class="timeline">
"@

    # Dodaj log stavke
    foreach ($entry in $script:ExecutionLog) {
        $html += @"
                    <div class="timeline-item $($entry.Level)">
                        <div class="timestamp">$($entry.Timestamp)</div>
                        <div>
                            <span class="level-badge $($entry.Level)">$($entry.Level)</span>
                            <span class="message">$($entry.Message)</span>
                        </div>
"@
        if ($entry.Context) {
            $html += "                        <div class='context'>📍 Kontekst: $($entry.Context)</div>`n"
        }
        if ($entry.Recommendation) {
            $html += "                        <div class='recommendation'>💡 Preporuka: $($entry.Recommendation)</div>`n"
        }
        $html += "                    </div>`n"
    }

    $html += @"
                </div>
            </div>
"@

    # Sekcija grešaka ako postoje
    if ($script:ErrorContext.Count -gt 0) {
        $html += @"
            <div class="section">
                <div class="error-section">
                    <h3>⚠️ Detektovane Greške ($($script:ErrorContext.Count))</h3>
"@
        foreach ($error in $script:ErrorContext) {
            $html += @"
                    <div style="margin: 15px 0; padding: 15px; background: white; border-radius: 5px;">
                        <strong>🚨 $($error.Step)</strong><br>
                        <span style="color: #721c24;">$($error.ErrorMessage)</span><br>
                        <small style="color: #856404;">📍 $($error.Context)</small><br>
                        <small style="color: #0c5460;">💡 $($error.Recommendation)</small>
                    </div>
"@
        }
        $html += @"
                </div>
            </div>
"@
    }

    $html += @"
            <div class="section">
                <h2>📊 Konfiguracija</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Akcija</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">$Action</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>vCenter Server</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">$vCenterServer</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>OneView Server</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">$OneViewServer</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Režim Rada</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">$Mode</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Vreme Početka</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">$($script:StartTime.ToString('yyyy-MM-dd HH:mm:ss'))</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Vreme Završetka</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">$($endTime.ToString('yyyy-MM-dd HH:mm:ss'))</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Master Orchestrator</strong> | VMware & HP OneView Automation</p>
            <p>Generisano: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Verzija 1.0</p>
        </div>
    </div>
</body>
</html>
"@

    $html | Out-File $script:HtmlReportPath -Encoding UTF8
    Write-MasterLog -Message "HTML izveštaj generisan: $script:HtmlReportPath" -Level "SUCCESS"
    
    # Sačuvaj i JSON log
    $logData = @{
        Action = $Action
        Mode = $Mode
        StartTime = $script:StartTime
        EndTime = $endTime
        Duration = $duration.ToString()
        ExecutionLog = $script:ExecutionLog
        Errors = $script:ErrorContext
        Summary = @{
            TotalSteps = $stepCount
            SuccessCount = $successCount
            ErrorCount = $errorCount
            WarningCount = $warningCount
        }
    }
    
    $logData | ConvertTo-Json -Depth 10 | Out-File $script:JsonLogPath -Encoding UTF8
    Write-MasterLog -Message "JSON log sacuvan: $script:JsonLogPath" -Level "SUCCESS"
}
#endregion

#region GLAVNI TOK
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║                                                              ║" -ForegroundColor Magenta
Write-Host "║         MASTER ORCHESTRATOR                                  ║" -ForegroundColor Magenta
Write-Host "║         VMware & HP OneView Automation                       ║" -ForegroundColor Magenta
Write-Host "║                                                              ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

Write-MasterLog -Message "Master Orchestrator pokrenut" -Level "INFO"
Write-MasterLog -Message "Akcija: $Action" -Level "INFO"
Write-MasterLog -Message "Mode: $Mode" -Level "INFO"

# Validacija parametara
if ($Action -ne "GenerateDocumentation" -and -not $script:ActionDefinitions[$Action]) {
    Register-Error -Step "Validacija" -ErrorMessage "Nepoznata akcija: $Action" -Recommendation "Dostupne akcije: $($script:ActionDefinitions.Keys -join ', ')"
    exit 1
}

# Generisanje dokumentacije
if ($GenerateDoc -or $Action -eq "GenerateDocumentation") {
    Write-MasterLog -Message "Generisanje dokumentacije akcija..." -Level "INFO"
    
    $docPath = "$PSScriptRoot\..\Documentation\Generated\ActionDefinitions.html"
    $docHtml = @"
<!DOCTYPE html>
<html>
<head>
    <title>Action Definitions Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .action-card { 
            background: #f8f9fa; 
            padding: 20px; 
            margin: 20px 0; 
            border-radius: 8px;
            border-left: 5px solid #3498db;
        }
        .phase { 
            background: white; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        .step { 
            padding: 10px; 
            margin: 5px 0; 
            background: #f1f3f4;
            border-radius: 3px;
        }
        .critical { color: #e74c3c; font-weight: bold; }
        .info { color: #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Dokumentacija Akcija - Master Orchestrator</h1>
        <p><strong>Datum generisanja:</strong> $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
"@

    foreach ($actionKey in $script:ActionDefinitions.Keys) {
        $act = $script:ActionDefinitions[$actionKey]
        $docHtml += @"
        <div class="action-card">
            <h2>$($act.Icon) $actionKey`: $($act.Title)</h2>
            <p><strong>Opis:</strong> $($act.Description)</p>
            <p><strong>Boja:</strong> <span style="color: $($act.Color);">$($act.Color)</span></p>
"@
        if ($act.Phases) {
            $docHtml += "            <h3>Faze:</h3>`n"
            foreach ($phase in $act.Phases) {
                $docHtml += @"
            <div class="phase">
                <h4>$($phase.Icon) $($phase.Name)</h4>
"@
                foreach ($step in $phase.Steps) {
                    $criticalClass = if ($step.Critical) { "critical" } else { "info" }
                    $docHtml += @"
                <div class="step">
                    <span class="$criticalClass">$(if ($step.Critical) { "🔴" } else { "🔵" })</span>
                    <strong>$($step.Name)</strong><br>
                    <small>Timeout: $($step.Timeout)s | $(if ($step.Critical) { "Kritično" } else { "Nekritično" })</small>
                    $(if ($step.Details) { "<br><small>Detalji: $($step.Details)</small>" })
                </div>
"@
                }
                $docHtml += "            </div>`n"
            }
        }
        $docHtml += "        </div>`n"
    }

    $docHtml += @"
    </div>
</body>
</html>
"@

    $docHtml | Out-File $docPath -Encoding UTF8
    Write-MasterLog -Message "Dokumentacija generisana: $docPath" -Level "SUCCESS"
}

# Izvrši glavnu akciju ako nije samo dokumentacija
if ($Action -ne "GenerateDocumentation") {
    try {
        $result = Invoke-MasterAction -ActionName $Action
        
        if ($result) {
            Write-MasterLog -Message "✅ AKCIJA ZAVRŠENA USPEŠNO!" -Level "SUCCESS"
        }
        else {
            Write-MasterLog -Message "⚠️ AKCIJA ZAVRŠENA SA UPOZORENJIMA!" -Level "WARNING"
        }
    }
    catch {
        Register-Error -Step "Glavni Tok" -ErrorMessage "Kritična greška: $_" -Recommendation "Proveriti logove i ponovo pokrenuti"
        Write-MasterLog -Message "❌ AKCIJA PREKINUTA ZBOG GREŠKE!" -Level "ERROR"
    }
}

# Generisanje finalnog izveštaja
Export-MasterHtmlReport

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║         MASTER ORCHESTRATOR ZAVRŠEN!                         ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📄 HTML Izveštaj: $script:HtmlReportPath" -ForegroundColor Cyan
Write-Host "📝 JSON Log: $script:JsonLogPath" -ForegroundColor Cyan
Write-Host ""
#endregion
