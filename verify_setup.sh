#!/bin/bash
# Verification script to check all configurations before deployment
# Run this script to verify everything is correctly set up

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}=== Project Configuration Verification ===${NC}\n"

# Check 1: Git branch
echo -e "${BOLD}1. Checking Git configuration...${NC}"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "fix/dbt-dag-and-credentials" ]; then
    echo -e "${YELLOW}⚠ Warning: You are on branch '$CURRENT_BRANCH'${NC}"
fi
echo -e "${GREEN}✓ Git check passed${NC}\n"

# Check 2: Environment files
echo -e "${BOLD}2. Checking environment files...${NC}"
MISSING_ENV=0
for dir in app dwh airflow elementary; do
    if [ ! -f "$dir/.env" ]; then
        echo -e "${RED}✗ Missing: $dir/.env${NC}"
        MISSING_ENV=1
    else
        echo -e "${GREEN}✓ Found: $dir/.env${NC}"
    fi
done

if [ $MISSING_ENV -eq 1 ]; then
    echo -e "${YELLOW}Run: cp <dir>/.env.example <dir>/.env for missing files${NC}"
else
    echo -e "${GREEN}✓ All environment files present${NC}"
fi
echo ""

# Check 3: dbt configuration conflicts
echo -e "${BOLD}3. Checking dbt configuration...${NC}"

# Check for config in profiles.yml (should NOT exist)
if grep -q "^config:" dbt_project/profiles.yml 2>/dev/null; then
    echo -e "${RED}✗ ERROR: 'config:' found in profiles.yml - this will cause conflicts!${NC}"
    echo -e "${YELLOW}  Remove the config section from profiles.yml${NC}"
    exit 1
else
    echo -e "${GREEN}✓ profiles.yml has no 'config:' section${NC}"
fi

# Check for flags in dbt_project.yml (should exist)
if grep -q "^flags:" dbt_project/dbt_project.yml 2>/dev/null; then
    echo -e "${GREEN}✓ dbt_project.yml has 'flags:' section${NC}"
else
    echo -e "${RED}✗ ERROR: 'flags:' not found in dbt_project.yml${NC}"
    exit 1
fi

# Check packages-install-path
PACKAGES_PATH=$(grep "packages-install-path:" dbt_project/dbt_project.yml | awk '{print $2}' | tr -d '"')
if [ "$PACKAGES_PATH" = "dbt_packages" ]; then
    echo -e "${GREEN}✓ packages-install-path is set to 'dbt_packages'${NC}"
else
    echo -e "${RED}✗ ERROR: packages-install-path is '$PACKAGES_PATH' (should be 'dbt_packages')${NC}"
    exit 1
fi

echo -e "${GREEN}✓ dbt configuration check passed${NC}\n"

# Check 4: Docker network
echo -e "${BOLD}4. Checking Docker network...${NC}"
if docker network inspect itmo-network >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker network 'itmo-network' exists${NC}"
else
    echo -e "${YELLOW}⚠ Docker network 'itmo-network' not found${NC}"
    echo -e "${YELLOW}  It will be created on first 'docker compose up'${NC}"
fi
echo ""

# Check 5: dbt_project directory structure
echo -e "${BOLD}5. Checking dbt_project directory structure...${NC}"
for dir in logs target dbt_packages edr_target; do
    if [ -d "dbt_project/$dir" ]; then
        PERMS=$(stat -c "%a" "dbt_project/$dir" 2>/dev/null || stat -f "%Lp" "dbt_project/$dir" 2>/dev/null)
        OWNER=$(stat -c "%u" "dbt_project/$dir" 2>/dev/null || stat -f "%u" "dbt_project/$dir" 2>/dev/null)
        echo -e "${GREEN}✓ dbt_project/$dir exists (perms: $PERMS, owner: $OWNER)${NC}"
    else
        echo -e "${YELLOW}⚠ dbt_project/$dir missing (will be created)${NC}"
    fi
done
echo ""

# Check 6: Models and schemas
echo -e "${BOLD}6. Checking dbt models...${NC}"
STG_MODELS=$(find dbt_project/models/stg -name "*.sql" 2>/dev/null | wc -l)
ODS_MODELS=$(find dbt_project/models/ods -name "*.sql" 2>/dev/null | wc -l)
DM_MODELS=$(find dbt_project/models/dm -name "*.sql" 2>/dev/null | wc -l)

echo -e "Staging models: $STG_MODELS"
echo -e "ODS models: $ODS_MODELS"
echo -e "Datamart models: $DM_MODELS"

if [ $STG_MODELS -gt 0 ] && [ $ODS_MODELS -gt 0 ] && [ $DM_MODELS -gt 0 ]; then
    echo -e "${GREEN}✓ All model layers present${NC}"
else
    echo -e "${YELLOW}⚠ Some model layers may be empty${NC}"
fi
echo ""

# Check 7: Elementary tests severity
echo -e "${BOLD}7. Checking Elementary test configuration...${NC}"
if grep -q "severity: warn" dbt_project/models/stg/stg_schema.yml 2>/dev/null; then
    echo -e "${GREEN}✓ Elementary tests configured with 'severity: warn'${NC}"
else
    echo -e "${YELLOW}⚠ Elementary tests may fail DAG runs on anomalies${NC}"
fi
echo ""

# Summary
echo -e "${BOLD}=== Verification Summary ===${NC}"
echo -e "${GREEN}✓ All critical checks passed!${NC}"
echo -e "\n${BOLD}Next steps:${NC}"
echo -e "1. Run: ${YELLOW}sudo ./fix_permissions.sh${NC}"
echo -e "2. Run: ${YELLOW}docker compose up -d${NC}"
echo -e "3. Wait 2 minutes, then check: ${YELLOW}docker compose ps${NC}"
echo -e "4. Open Airflow UI: ${YELLOW}http://your-server:8080${NC}"
echo -e "\n${GREEN}Configuration is ready for deployment!${NC}"
