#!/bin/bash

# Vite Major Version Update Script
# Updates Vite from v5 to v7 (BREAKING CHANGES)
# This fixes the esbuild security vulnerability
# 
# Date: October 14, 2025
# Usage: ./scripts/update_vite_major.sh [--dry-run]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}Running in DRY RUN mode${NC}\n"
fi

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "========================================"
echo "Vite v7 Major Update Script"
echo "========================================"
echo ""

log_warning "This update includes BREAKING CHANGES"
log_info "Vite v5.4.20 → v7.1.9"
log_info "Fixes security vulnerability: GHSA-67mh-4wv8-2f99"
echo ""

cd "$PROJECT_ROOT/frontend"

if [[ "$DRY_RUN" == false ]]; then
    # Backup
    cp package.json "package.json.backup.$(date +%Y%m%d_%H%M%S)"
    log_success "Backup created"
    
    # Update Vite
    log_info "Updating Vite and related packages..."
    npm install vite@^7.1.9 @vitejs/plugin-react@^5.0.4 --save-dev
    
    log_success "Vite updated to v7.1.9"
    echo ""
    
    log_info "Running security audit..."
    npm audit
    
    echo ""
    log_success "Update completed!"
    echo ""
    log_warning "IMPORTANT: Test your build process:"
    echo "  1. npm run dev"
    echo "  2. npm run build"
    echo "  3. npm run preview"
    echo ""
    log_info "Check migration guide: https://vite.dev/guide/migration.html"
else
    log_info "Would update:"
    echo "  • vite: 5.4.20 → 7.1.9"
    echo "  • @vitejs/plugin-react: 4.7.0 → 5.0.4"
fi

echo "========================================"
