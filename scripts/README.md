# Scripts Directory

This directory contains utility scripts for maintaining and updating the Learning Studio project.

## Available Scripts

### Security & Updates

#### `update_security_patches.sh`
Automatically updates packages with security vulnerabilities (non-breaking changes only).

```bash
# Dry run to see what would be updated
./scripts/update_security_patches.sh --dry-run

# Apply security patches
./scripts/update_security_patches.sh
```

**Features:**
- Automatic backups before updates
- Updates Python and JavaScript packages
- Post-update security audit
- Safe rollback capability

#### `update_vite_major.sh`
Updates Vite to v7 (fixes esbuild security vulnerability, but includes breaking changes).

```bash
# Dry run
./scripts/update_vite_major.sh --dry-run

# Apply update (test thoroughly after!)
./scripts/update_vite_major.sh
```

### Database

#### `validate_indexes.py`
Validates database index migrations and provides deployment guidance.

```bash
python scripts/validate_indexes.py
```

---

## Documentation

- **Quick Start Guide:** `../docs/QUICK_START_UPDATES.md`
- **Detailed Documentation:** `../docs/SECURITY_UPDATES.md`

---

## Script Requirements

All scripts assume:
- Virtual environment at `venv/` in project root
- Node.js and npm installed
- Project structure intact

---

## Creating New Scripts

When adding new scripts:
1. Add execute permission: `chmod +x scripts/your_script.sh`
2. Include help/usage information
3. Support `--dry-run` flag when applicable
4. Update this README
5. Add documentation in `docs/`
