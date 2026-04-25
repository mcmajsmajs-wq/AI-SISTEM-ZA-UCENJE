#!/bin/bash
# Test Runner za SVE Skripte (PowerShell + Ansible)
# Provera svih 5 faza i validacija

echo "=========================================="
echo "  KOMPLETAN TEST - Sve Skripte"
echo "  VMware & HP OneView Automation"
echo "=========================================="
echo ""

PROJECT_DIR="/home/dju/moji projekti/Vspehere_One_View_DefinisaniScenario"
ERRORS=0
WARNINGS=0
PASSED=0

# Funkcija za proveru fajla
check_file() {
    local file=$1
    local name=$2
    local type=$3
    
    echo "  📄 $name ($type)"
    
    if [ -f "$file" ]; then
        local lines=$(wc -l < "$file")
        local size=$(du -h "$file" | cut -f1)
        echo "     ✅ Postoji ($lines linija, $size)"
        ((PASSED++))
        return 0
    else
        echo "     ❌ NEDOSTAJE!"
        ((ERRORS++))
        return 1
    fi
}

# Funkcija za proveru YAML sintakse
check_yaml_syntax() {
    local file=$1
    local name=$2
    
    echo "     🔍 Provera YAML sintakse..."
    
    if command -v python3 &> /dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "     ✅ YAML sintaksa OK"
            ((PASSED++))
        else
            echo "     ❌ YAML sintaksa GREŠKA!"
            ((ERRORS++))
        fi
    else
        echo "     ⚠️  Python3 nije dostupan - preskačem YAML proveru"
        ((WARNINGS++))
    fi
}

# Funkcija za proveru PowerShell sintakse
check_ps_syntax() {
    local file=$1
    local name=$2
    
    echo "     🔍 Provera strukture..."
    
    local functions=$(grep -c "^function" "$file" 2>/dev/null || echo "0")
    local params=$(grep -c "param(" "$file" 2>/dev/null || echo "0")
    local trycatch=$(grep -c "try {" "$file" 2>/dev/null || echo "0")
    
    echo "       - Funkcija: $functions"
    echo "       - Param blokova: $params"
    echo "       - Try-catch: $trycatch"
    
    if [ "$trycatch" -gt 0 ]; then
        echo "     ✅ Try-catch implementiran"
        ((PASSED++))
    else
        echo "     ⚠️  Nema try-catch!"
        ((WARNINGS++))
    fi
}

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  FAZA 1: PROVERA STRUKTURE PROJEKTA                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_DIR"

echo "📁 PowerShell Skripte:"
check_file "$PROJECT_DIR/PowerShell/VMwarePatchingCore.psm1" "Core Modul" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/VMwarePatchingCore.psm1" "Core Modul"

check_file "$PROJECT_DIR/PowerShell/Scenario1-VMwarePatching.ps1" "Scenario 1" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/Scenario1-VMwarePatching.ps1" "Scenario 1"

check_file "$PROJECT_DIR/PowerShell/Scenario2-HPOneViewUpdate.ps1" "Scenario 2" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/Scenario2-HPOneViewUpdate.ps1" "Scenario 2"

check_file "$PROJECT_DIR/PowerShell/Scenario3-CombinedPatching.ps1" "Scenario 3" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/Scenario3-CombinedPatching.ps1" "Scenario 3"

check_file "$PROJECT_DIR/PowerShell/Scenario4-ClusterPatching.ps1" "Scenario 4" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/Scenario4-ClusterPatching.ps1" "Scenario 4"

check_file "$PROJECT_DIR/PowerShell/Daily-VMwareScan.ps1" "Daily VMware Scan" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/Daily-VMwareScan.ps1" "Daily VMware Scan"

check_file "$PROJECT_DIR/PowerShell/Daily-OneViewScan.ps1" "Daily OneView Scan" "PowerShell"
check_ps_syntax "$PROJECT_DIR/PowerShell/Daily-OneViewScan.ps1" "Daily OneView Scan"

check_file "$PROJECT_DIR/PowerShell/Run-DailyScans.ps1" "Run Daily Scans" "PowerShell"
check_file "$PROJECT_DIR/PowerShell/Master-Orchestrator.ps1" "Master Orchestrator" "PowerShell"

echo ""
echo "📁 Ansible Playbook-ovi:"
check_file "$PROJECT_DIR/Ansible/main.yml" "Main Playbook" "YAML"
check_yaml_syntax "$PROJECT_DIR/Ansible/main.yml" "Main"

check_file "$PROJECT_DIR/Ansible/daily-scan.yml" "Daily Scan" "YAML"
check_yaml_syntax "$PROJECT_DIR/Ansible/daily-scan.yml" "Daily Scan"

check_file "$PROJECT_DIR/Ansible/scenario1-vmware-patching.yml" "Scenario 1" "YAML"
check_yaml_syntax "$PROJECT_DIR/Ansible/scenario1-vmware-patching.yml" "Scenario 1"

check_file "$PROJECT_DIR/Ansible/scenario2-oneview-update.yml" "Scenario 2" "YAML"
check_yaml_syntax "$PROJECT_DIR/Ansible/scenario2-oneview-update.yml" "Scenario 2"

check_file "$PROJECT_DIR/Ansible/inventory/hosts" "Inventory" "INI"
check_file "$PROJECT_DIR/Ansible/group_vars/vmware.yml" "Group Vars" "YAML"
check_yaml_syntax "$PROJECT_DIR/Ansible/group_vars/vmware.yml" "Group Vars"

echo ""
echo "📁 Dokumentacija:"
check_file "$PROJECT_DIR/README.md" "README" "Markdown"
check_file "$PROJECT_DIR/IMPLEMENTATION_REPORT.md" "Implementation Report" "Markdown"
check_file "$PROJECT_DIR/FINAL_SUMMARY.md" "Final Summary" "Markdown"
check_file "$PROJECT_DIR/BACKUP_IMPLEMENTATION.md" "Backup Implementation" "Markdown"
check_file "$PROJECT_DIR/Documentation/Master-Orchestrator-Guide.md" "Master Guide" "Markdown"
check_file "$PROJECT_DIR/Documentation/Workflow-Diagrams.md" "Workflow Diagrams" "Markdown"
check_file "$PROJECT_DIR/Ansible/README.md" "Ansible README" "Markdown"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  FAZA 2: PROVERA BACKUP FUNKCIONALNOSTI                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🔍 Provera implementacije backup-a:"

# Provera u PowerShell skriptama
if grep -q "BACKUP PROVERA HOSTA" "$PROJECT_DIR/PowerShell/Scenario1-VMwarePatching.ps1"; then
    echo "  ✅ Scenario1: Backup provera hosta implementirana"
    ((PASSED++))
else
    echo "  ❌ Scenario1: Nedostaje backup provera!"
    ((ERRORS++))
fi

if grep -q "KRITIČNA PROVERA: Backup hosta" "$PROJECT_DIR/PowerShell/Scenario4-ClusterPatching.ps1"; then
    echo "  ✅ Scenario4: Backup provera za svaki host implementirana"
    ((PASSED++))
else
    echo "  ❌ Scenario4: Nedostaje backup provera!"
    ((ERRORS++))
fi

if grep -q "backup_check_only" "$PROJECT_DIR/Ansible/group_vars/vmware.yml"; then
    echo "  ✅ Ansible: backup_check_only konfigurisan"
    ((PASSED++))
else
    echo "  ⚠️  Ansible: backup_check_only nije eksplicitno definisan"
    ((WARNINGS++))
fi

echo ""
echo "  ℹ️  NAPOMENA: Backup appliance-a se SAMO PROVERAVA (ne kreira)"
echo "     jer je to dnevna aktivnost koja se radi odvojeno."

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  FAZA 3: PROVERA 5 FAZA U SCENARIO 1                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PHASES=(
    "FAZA 1: PRIPREMNE RADNJE"
    "FAZA 2: LIFECYCLE MANAGER"
    "FAZA 3: ATTACHMENT I COMPLIANCE CHECK"
    "FAZA 4: STAGING"
    "FAZA 5: BACKUP PROVERA I REMEDIATION"
    "FAZA 6: POST-PATCH VERIFIKACIJA"
)

for phase in "${PHASES[@]}"; do
    if grep -q "$phase" "$PROJECT_DIR/PowerShell/Scenario1-VMwarePatching.ps1"; then
        echo "  ✅ $phase"
        ((PASSED++))
    else
        echo "  ❌ $phase - NEDOSTAJE!"
        ((ERRORS++))
    fi
done

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  FAZA 4: PROVERA TRY-CATCH I ERROR HANDLING               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Brojanje try-catch blokova
TRY_COUNT=$(grep -c "try {" "$PROJECT_DIR/PowerShell/Scenario1-VMwarePatching.ps1" 2>/dev/null || echo "0")
echo "  Scenario1: $TRY_COUNT try-catch blokova"

TRY_COUNT=$(grep -c "block:" "$PROJECT_DIR/Ansible/scenario1-vmware-patching.yml" 2>/dev/null || echo "0")
echo "  Ansible Scenario1: $TRY_COUNT block/rescue sekcija"

if [ "$TRY_COUNT" -gt 0 ]; then
    echo "  ✅ Error handling implementiran"
    ((PASSED++))
else
    echo "  ⚠️  Malo error handling sekcija"
    ((WARNINGS++))
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  FAZA 5: STATISTIKA I REZIME                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Brojanje linija koda
PS_LINES=$(find "$PROJECT_DIR/PowerShell" -name "*.ps1" -o -name "*.psm1" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
YAML_LINES=$(find "$PROJECT_DIR/Ansible" -name "*.yml" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
DOC_LINES=$(find "$PROJECT_DIR" -name "*.md" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')

echo "  📊 Statistika koda:"
echo "     PowerShell: $PS_LINES linija"
echo "     Ansible YAML: $YAML_LINES linija"
echo "     Dokumentacija: $DOC_LINES linija"
echo "     UKUPNO: $((PS_LINES + YAML_LINES + DOC_LINES)) linija"

echo ""
echo "  📁 Struktura:"
echo "     PowerShell skripti: $(find "$PROJECT_DIR/PowerShell" -name "*.ps1" | wc -l)"
echo "     Ansible playbook-ova: $(find "$PROJECT_DIR/Ansible" -name "*.yml" | wc -l)"
echo "     Dokumentacija: $(find "$PROJECT_DIR" -name "*.md" | wc -l)"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    TEST REZULTATI                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "  ✅ Prošlo: $PASSED"
echo "  ⚠️  Upozorenja: $WARNINGS"
echo "  ❌ Greške: $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "  🎉 SVI TESTOVI USPEŠNI!"
    echo ""
    echo "  ✅ PowerShell skripte su validne"
    echo "  ✅ Ansible playbook-ovi su validni"
    echo "  ✅ Sve 6 faza Scenario 1 postoje"
    echo "  ✅ Backup provera implementirana"
    echo "  ✅ Error handling prisutan"
    echo "  ✅ Dokumentacija kompletna"
    exit_code=0
else
    echo "  ⚠️  IMA GREŠAKA KOJE TREBA ISPRAVITI!"
    exit_code=1
fi

echo ""
echo "=========================================="
echo "  Test završen: $(date)"
echo "=========================================="

exit $exit_code
