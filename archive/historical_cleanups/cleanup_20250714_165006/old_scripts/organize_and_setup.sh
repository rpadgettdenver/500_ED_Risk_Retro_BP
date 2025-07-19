#!/bin/bash
# Suggested File Name: organize_and_setup.sh
# File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
# Use: Archive old files and set up new modules for the Energize Denver project

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP"

echo -e "${GREEN}🚀 Starting Energize Denver Project Organization${NC}"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Change to project directory
cd "$PROJECT_ROOT" || exit 1

# Step 1: Create archive directories
echo -e "${YELLOW}📁 Creating archive directories...${NC}"
mkdir -p archive/2025-07-initial
mkdir -p archive/gcp-migration-intermediate
echo "✅ Archive directories created"
echo ""

# Step 2: Archive old files
echo -e "${YELLOW}🗄️  Archiving obsolete files...${NC}"

# Archive initial project files
if [ -f "READMEtxt.txt" ]; then
    mv READMEtxt.txt archive/2025-07-initial/
    echo "✅ Moved READMEtxt.txt to archive"
fi

if [ -f "project_handoff.md" ]; then
    mv project_handoff.md archive/2025-07-initial/
    echo "✅ Moved project_handoff.md to archive"
fi

if [ -f "setup_project_structure.sh" ]; then
    mv setup_project_structure.sh archive/2025-07-initial/
    echo "✅ Moved setup_project_structure.sh to archive"
fi

# Archive intermediate GCP files
if [ -f "src/gcp/load_data_and_calculate_old.py" ]; then
    mv src/gcp/load_data_and_calculate_old.py archive/gcp-migration-intermediate/
    echo "✅ Moved load_data_and_calculate_old.py to archive"
fi

if [ -f "src/gcp/create_penalty_view.py" ]; then
    mv src/gcp/create_penalty_view.py archive/gcp-migration-intermediate/
    echo "✅ Moved create_penalty_view.py to archive"
fi

if [ -f "src/gcp/create_penalty_view_fixed.py" ]; then
    mv src/gcp/create_penalty_view_fixed.py archive/gcp-migration-intermediate/
    echo "✅ Moved create_penalty_view_fixed.py to archive"
fi

echo ""

# Step 3: Create Archive README
echo -e "${YELLOW}📝 Creating archive README...${NC}"
cat > archive/README.md << 'EOF'
# Archive Directory

## Purpose
This directory contains historical files from the Energize Denver project evolution.

## /2025-07-initial/
Contains the original project design before GCP migration:
- `READMEtxt.txt` - Original README with local Python module design
- `project_handoff.md` - Initial project handoff document
- `setup_project_structure.sh` - Initial project structure setup script

## /gcp-migration-intermediate/
Contains intermediate versions created during GCP migration:
- `load_data_and_calculate_old.py` - Old calculation script before updates
- `create_penalty_view.py` - Original penalty view implementation
- `create_penalty_view_fixed.py` - Intermediate fix before v3

## Archive Date
Files archived on: $(date '+%Y-%m-%d %H:%M:%S')
EOF
echo "✅ Archive README created"
echo ""

# Step 4: Clean .DS_Store files (optional)
echo -e "${YELLOW}🧹 Cleaning system files...${NC}"
find . -name ".DS_Store" -type f -delete 2>/dev/null
echo "✅ Removed .DS_Store files"
echo ""

# Step 5: Create directories for new modules if they don't exist
echo -e "${YELLOW}📂 Setting up directories for new modules...${NC}"
mkdir -p src/utils
mkdir -p src/analytics
mkdir -p docs/technical
mkdir -p data/gcp_exports
echo "✅ Module directories ready"
echo ""

# Step 6: Create placeholder files for new modules
echo -e "${YELLOW}📄 Creating new module files...${NC}"

# Create init files if they don't exist
touch src/utils/__init__.py
touch src/analytics/__init__.py

echo "✅ Module structure prepared"
echo ""

# Step 7: Create setup confirmation file
echo -e "${YELLOW}📋 Creating setup log...${NC}"
cat > archive/setup_log.txt << EOF
Energize Denver Project Organization Log
========================================
Date: $(date '+%Y-%m-%d %H:%M:%S')
User: $(whoami)

Actions Completed:
1. Created archive directories
2. Archived obsolete files
3. Cleaned system files
4. Prepared module directories
5. Ready for new module installation

Next Steps:
1. Copy local_gcp_bridge.py to src/utils/
2. Copy der_clustering_analysis.py to src/analytics/
3. Copy BigQuery schema docs to docs/technical/
4. Test new modules with GCP data

Archive Contents:
$(ls -la archive/2025-07-initial/ 2>/dev/null || echo "No files in initial archive")
$(ls -la archive/gcp-migration-intermediate/ 2>/dev/null || echo "No files in GCP archive")
EOF
echo "✅ Setup log created"
echo ""

# Step 8: Summary
echo -e "${GREEN}✨ Project organization complete!${NC}"
echo ""
echo "Summary of changes:"
echo "- Archived $(ls archive/2025-07-initial/ 2>/dev/null | wc -l | tr -d ' ') initial project files"
echo "- Archived $(ls archive/gcp-migration-intermediate/ 2>/dev/null | wc -l | tr -d ' ') GCP migration files"
echo "- Created directories for new modules"
echo "- Cleaned system files"
echo ""
echo -e "${YELLOW}📌 Next steps:${NC}"
echo "1. Save the new Python modules from Claude:"
echo "   - local_gcp_bridge.py → src/utils/"
echo "   - der_clustering_analysis.py → src/analytics/"
echo "   - bigquery_schemas.md → docs/technical/"
echo ""
echo "2. Activate your virtual environment:"
echo "   source gcp_env/bin/activate"
echo ""
echo "3. Install any missing dependencies:"
echo "   pip install google-cloud-bigquery pandas numpy"
echo ""
echo -e "${GREEN}🎉 Your project is now organized and ready for the next phase!${NC}"