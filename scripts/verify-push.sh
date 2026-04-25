#!/bin/bash
#
# Post-Push Verification Script
# Verifies everything is correct after git push
#
# Usage:
#   ./verify-push.sh
#

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Post-Push Verification"
echo "=========================================="
echo ""

ERRORS=0

# 1. Check git status
echo "1. Checking git status..."
if [[ -n "$(git status --porcelain)" ]]; then
    echo -e "${RED}✗ Uncommitted changes found${NC}"
    git status --short
    ((ERRORS++))
else
    echo -e "${GREEN}✓ No uncommitted changes${NC}"
fi
echo ""

# 2. Check remote sync
echo "2. Checking remote sync..."
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [[ "$LOCAL" == "$REMOTE" ]]; then
    echo -e "${GREEN}✓ Local and remote in sync${NC}"
else
    echo -e "${RED}✗ Local and remote out of sync${NC}"
    echo "  Local:  $LOCAL"
    echo "  Remote: $REMOTE"
    ((ERRORS++))
fi
echo ""

# 3. Check last commit
echo "3. Last commit:"
git log -1 --oneline
echo ""

# 4. Run syntax checks
echo "4. Syntax checks..."

# Bash scripts
echo -n "  Backup script: "
if bash -n /home/dju/mojAiProjekat/New\ folder/scripts/backup.sh 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ERROR${NC}"
    ((ERRORS++))
fi

echo -n "  Restore script: "
if bash -n /home/dju/mojAiProjekat/New\ folder/scripts/restore.sh 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ERROR${NC}"
    ((ERRORS++))
fi

echo -n "  Backup cron: "
if bash -n /home/dju/mojAiProjekat/New\ folder/scripts/backup-cron.sh 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ERROR${NC}"
    ((ERRORS++))
fi
echo ""

# 5. Run unit tests
echo "5. Running unit tests..."
cd /home/dju/mojAiProjekat/New\ folder/backend
if python3 -m pytest app/tests/unit/test_backup.py -v --tb=line 2>&1 | tail -3 | grep -q "passed"; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    ((ERRORS++))
fi
echo ""

# 6. Summary
echo "=========================================="
if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo ""
    echo "Push verified successfully!"
    exit 0
else
    echo -e "${RED}✗ $ERRORS ERRORS FOUND${NC}"
    echo ""
    echo "Please fix errors before next push!"
    exit 1
fi