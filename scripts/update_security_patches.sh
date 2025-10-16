#!/bin/bash

# Security Patch Update Script
# This script updates packages with known security vulnerabilities
# while avoiding breaking changes (major version updates)
# 
# Date: October 14, 2025
# Usage: ./scripts/update_security_patches.sh [--dry-run]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if dry-run mode
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}Running in DRY RUN mode - no changes will be made${NC}\n"
fi

# Log function
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup
create_backup() {
    local file=$1
    local backup_file="${file}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [[ "$DRY_RUN" == false ]]; then
        cp "$file" "$backup_file"
        log_success "Backup created: $backup_file"
    else
        log_info "Would create backup: $backup_file"
    fi
}

echo "========================================"
echo "Security Patch Update Script"
echo "========================================"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

#####################################
# PYTHON SECURITY UPDATES
#####################################

log_info "Starting Python security updates..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    log_success "Virtual environment activated"
else
    log_error "Virtual environment not found at venv/"
    exit 1
fi

# Backup requirements.txt
create_backup "requirements.txt"

# Define Python packages to update with their minimum safe versions
# Format: "package==current_version::safe_version::reason"
declare -a PYTHON_UPDATES=(
    "cryptography==42.0.8::46.0.2::CRITICAL - Security vulnerabilities GHSA-h4gh-qq45-vh27, GHSA-79v4-65xg-pq4g"
    "requests==2.31.0::2.32.5::CRITICAL - Security vulnerabilities GHSA-9wx4-h78v-vm56, GHSA-9hjg-9r4m-mvj7"
    "djangorestframework-simplejwt==5.3.0::5.5.1::CRITICAL - Security vulnerability GHSA-5vcc-86wm-547q"
    "PyJWT==2.8.0::2.10.1::HIGH - Security updates and bug fixes"
    "Pillow==10.3.0::10.4.0::HIGH - Security patches (avoiding 11.x breaking changes)"
    "psycopg2-binary==2.9.9::2.9.11::MEDIUM - Bug fixes"
    "bleach==6.1.0::6.2.0::MEDIUM - Security patches"
    "channels-redis==4.1.0::4.3.0::MEDIUM - Bug fixes"
    "django-cors-headers==4.3.1::4.9.0::MEDIUM - Security and bug fixes"
    "whitenoise==6.7.0::6.11.0::MEDIUM - Performance improvements"
    "django-mptt==0.16.0::0.18.0::MEDIUM - Bug fixes"
    "drf-spectacular==0.27.2::0.28.0::LOW - Feature updates"
    "python-dotenv==1.0.1::1.1.1::LOW - Bug fixes"
    "Markdown==3.6::3.9::LOW - Feature updates"
    "django-haystack==3.2.1::3.3.0::LOW - Bug fixes"
)

echo "Packages to update:"
for update in "${PYTHON_UPDATES[@]}"; do
    IFS='::' read -r package version reason <<< "$update"
    package_name=$(echo "$package" | cut -d'=' -f1)
    echo -e "  ${YELLOW}•${NC} $package_name → $version ($reason)"
done
echo ""

if [[ "$DRY_RUN" == false ]]; then
    # Update pip first
    log_info "Updating pip..."
    pip install --upgrade pip
    
    # Update each package
    for update in "${PYTHON_UPDATES[@]}"; do
        IFS='::' read -r package version reason <<< "$update"
        package_name=$(echo "$package" | cut -d'=' -f1)
        
        log_info "Updating $package_name to $version..."
        
        if pip install "$package_name==$version"; then
            log_success "$package_name updated successfully"
            
            # Update requirements.txt
            if grep -q "^$package_name==" requirements.txt; then
                sed -i.bak "s/^$package_name==.*/$package_name==$version/" requirements.txt
                rm requirements.txt.bak
            fi
        else
            log_error "Failed to update $package_name"
        fi
        echo ""
    done
    
    log_success "Python security updates completed"
else
    log_info "Would update ${#PYTHON_UPDATES[@]} Python packages"
fi

echo ""
echo "========================================"

#####################################
# FRONTEND SECURITY UPDATES
#####################################

log_info "Starting Frontend security updates..."
echo ""

cd "$PROJECT_ROOT/frontend"

# Backup package.json
create_backup "package.json"

# Define frontend packages to update
declare -a FRONTEND_UPDATES=(
    "@codemirror/view::^6.38.6::Patch update"
    "dompurify::^3.3.0::Security patch"
)

echo "Frontend packages to update:"
for update in "${FRONTEND_UPDATES[@]}"; do
    IFS='::' read -r package version reason <<< "$update"
    echo -e "  ${YELLOW}•${NC} $package → $version ($reason)"
done
echo ""

if [[ "$DRY_RUN" == false ]]; then
    for update in "${FRONTEND_UPDATES[@]}"; do
        IFS='::' read -r package version reason <<< "$update"
        
        log_info "Updating $package to $version..."
        
        if npm install "$package@$version"; then
            log_success "$package updated successfully"
        else
            log_warning "Failed to update $package (non-critical)"
        fi
        echo ""
    done
    
    log_success "Frontend security updates completed"
else
    log_info "Would update ${#FRONTEND_UPDATES[@]} frontend packages"
fi

echo ""
echo "========================================"

#####################################
# ROOT PACKAGE UPDATES
#####################################

log_info "Starting root package security updates..."
echo ""

cd "$PROJECT_ROOT"

# Backup root package.json
create_backup "package.json"

declare -a ROOT_UPDATES=(
    "@codemirror/view::^6.38.6::Patch update"
)

echo "Root packages to update:"
for update in "${ROOT_UPDATES[@]}"; do
    IFS='::' read -r package version reason <<< "$update"
    echo -e "  ${YELLOW}•${NC} $package → $version ($reason)"
done
echo ""

if [[ "$DRY_RUN" == false ]]; then
    for update in "${ROOT_UPDATES[@]}"; do
        IFS='::' read -r package version reason <<< "$update"
        
        log_info "Updating $package to $version..."
        
        if npm install "$package@$version"; then
            log_success "$package updated successfully"
        else
            log_warning "Failed to update $package (non-critical)"
        fi
        echo ""
    done
    
    log_success "Root package security updates completed"
else
    log_info "Would update ${#ROOT_UPDATES[@]} root packages"
fi

echo ""
echo "========================================"

#####################################
# VITE SECURITY UPDATE (REQUIRES CONFIRMATION)
#####################################

log_warning "Vite security update (v5.4.20 → v7.1.9) requires manual intervention"
log_info "This is a major version update with breaking changes"
log_info "Run './scripts/update_vite_major.sh' after reviewing migration guide"

echo ""
echo "========================================"

#####################################
# VERIFICATION
#####################################

if [[ "$DRY_RUN" == false ]]; then
    log_info "Running security audits..."
    echo ""
    
    cd "$PROJECT_ROOT"
    
    # Python security audit
    log_info "Python security audit:"
    source venv/bin/activate
    if command -v pip-audit &> /dev/null; then
        pip-audit || log_warning "Some vulnerabilities may still exist (check output above)"
    else
        log_warning "pip-audit not installed - skipping Python security scan"
    fi
    echo ""
    
    # Frontend security audit
    log_info "Frontend security audit:"
    cd "$PROJECT_ROOT/frontend"
    npm audit || log_warning "Some vulnerabilities may still exist (check output above)"
    echo ""
    
    # Root security audit
    log_info "Root package security audit:"
    cd "$PROJECT_ROOT"
    npm audit || log_warning "Some vulnerabilities may still exist (check output above)"
    echo ""
fi

#####################################
# SUMMARY
#####################################

echo ""
echo "========================================"
echo "SUMMARY"
echo "========================================"

if [[ "$DRY_RUN" == true ]]; then
    log_info "Dry run completed - no changes were made"
    log_info "Run without --dry-run flag to apply updates"
else
    log_success "Security patches applied successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Run tests to verify nothing broke: python manage.py test"
    echo "  2. Start dev server and test manually: python manage.py runserver"
    echo "  3. Test frontend: cd frontend && npm run dev"
    echo "  4. Review breaking changes for major updates in docs/"
    echo "  5. Consider updating Vite (breaking change): ./scripts/update_vite_major.sh"
    echo ""
    log_info "Backup files created with .backup.TIMESTAMP extension"
    log_info "To restore: cp requirements.txt.backup.* requirements.txt"
fi

echo ""
echo "========================================"
echo "Update process completed"
echo "========================================"
