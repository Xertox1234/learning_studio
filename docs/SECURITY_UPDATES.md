# Security Patch Update Documentation

## Overview
This document explains the automated security patch update scripts and the update strategy for the Learning Studio project.

**Last Updated:** October 14, 2025

---

## Scripts

### 1. `update_security_patches.sh`
**Purpose:** Safely updates packages with security vulnerabilities without breaking changes.

**Usage:**
```bash
# Dry run (see what would be updated)
./scripts/update_security_patches.sh --dry-run

# Apply updates
./scripts/update_security_patches.sh
```

**What it updates:**
- ✅ Python packages with security fixes (minor/patch versions only)
- ✅ JavaScript packages with security fixes (patch versions only)
- ✅ Automatic backup of requirements.txt and package.json files
- ✅ Post-update security audit

**Safety Features:**
- Creates timestamped backups before making changes
- Only updates to safe versions (no major version jumps)
- Runs security audits after updates
- Provides rollback instructions

---

### 2. `update_vite_major.sh`
**Purpose:** Update Vite to v7 (fixes critical esbuild vulnerability, but has breaking changes).

**Usage:**
```bash
# Dry run
./scripts/update_vite_major.sh --dry-run

# Apply update
./scripts/update_vite_major.sh
```

**Important:** This is a major version update. Test thoroughly after updating!

---

## Current Security Issues

### Critical (Apply Immediately)
1. **cryptography** (42.0.8 → 46.0.2)
   - CVE: GHSA-h4gh-qq45-vh27, GHSA-79v4-65xg-pq4g
   - Impact: Potential security vulnerabilities in encryption

2. **requests** (2.31.0 → 2.32.5)
   - CVE: GHSA-9wx4-h78v-vm56, GHSA-9hjg-9r4m-mvj7
   - Impact: HTTP request security issues

3. **djangorestframework-simplejwt** (5.3.0 → 5.5.1)
   - CVE: GHSA-5vcc-86wm-547q
   - Impact: JWT token security vulnerability

4. **esbuild/vite** (5.4.20 → 7.1.9)
   - CVE: GHSA-67mh-4wv8-2f99
   - Impact: Dev server can be exploited to read files
   - **Note:** Requires major version update (breaking changes)

---

## Update Strategy

### Phase 1: Non-Breaking Security Patches ⚡
**Timeline:** Immediate
**Risk:** Low
**Script:** `update_security_patches.sh`

Updates included:
- cryptography → 46.0.2
- requests → 2.32.5
- djangorestframework-simplejwt → 5.5.1
- PyJWT → 2.10.1
- bleach → 6.2.0
- channels-redis → 4.3.0
- django-cors-headers → 4.9.0
- whitenoise → 6.11.0
- Other minor/patch updates

**Testing Required:**
- Unit tests: `python manage.py test`
- Manual testing: Basic functionality check
- API endpoint testing

---

### Phase 2: Vite Major Update 🔧
**Timeline:** Within 1 week
**Risk:** Medium (breaking changes)
**Script:** `update_vite_major.sh`

Updates:
- vite: 5.4.20 → 7.1.9
- @vitejs/plugin-react: 4.7.0 → 5.0.4

**Breaking Changes:**
- Build configuration may need adjustments
- Plugin API changes
- Environment variable handling changes

**Testing Required:**
- `npm run dev` - Development server
- `npm run build` - Production build
- `npm run preview` - Preview production build
- Full frontend functionality test

**Migration Guide:** https://vite.dev/guide/migration.html

---

### Phase 3: Major Version Updates 📦
**Timeline:** 2-4 weeks (planned)
**Risk:** High (breaking changes)
**Manual intervention required**

**Deferred Updates:**
1. **django-allauth** (0.63.3 → 65.12.0)
   - Breaking: Settings and URL configuration changes
   - Migration guide needed

2. **openai** (1.35.5 → 2.3.0)
   - Breaking: Complete API restructure
   - Code refactoring required

3. **wagtail-ai** (2.1.2 → 3.0.0)
   - Breaking: API changes
   - Check compatibility with openai v2

4. **tailwindcss** (3.4.18 → 4.1.14)
   - Breaking: New configuration format
   - CSS utility changes

5. **react-router-dom** (6.30.1 → 7.9.4)
   - Breaking: Data loading patterns
   - Route configuration changes

6. **eslint** (8.57.1 → 9.37.0)
   - Breaking: Flat config system
   - Complete config rewrite

---

## Rollback Procedures

### Python Packages
```bash
# Find backup file
ls -la requirements.txt.backup.*

# Restore from backup
cp requirements.txt.backup.YYYYMMDD_HHMMSS requirements.txt

# Reinstall
pip install -r requirements.txt
```

### JavaScript Packages
```bash
# Restore package.json
cp package.json.backup.YYYYMMDD_HHMMSS package.json

# Reinstall
npm install
```

---

## Testing Checklist

### After Security Patches
- [ ] Python tests pass: `python manage.py test`
- [ ] Django admin accessible
- [ ] User authentication works
- [ ] API endpoints respond correctly
- [ ] Code editor functionality intact
- [ ] Forum features working
- [ ] Wagtail CMS accessible

### After Vite Update
- [ ] Frontend dev server starts: `npm run dev`
- [ ] Production build succeeds: `npm run build`
- [ ] Build preview works: `npm run preview`
- [ ] Hot module replacement (HMR) works
- [ ] Code splitting works correctly
- [ ] Static assets load properly
- [ ] React components render correctly

---

## Monitoring

### After Updates, Monitor:
1. **Application logs** for new errors
2. **Performance metrics** for degradation
3. **User reports** for bugs
4. **Security advisories** for new vulnerabilities

### Tools:
```bash
# Python security check
pip-audit

# JavaScript security check
npm audit

# Check outdated packages
pip list --outdated
npm outdated
```

---

## Maintenance Schedule

### Weekly
- Run `pip-audit` and `npm audit`
- Review security advisories

### Monthly
- Check for outdated packages
- Plan updates for non-critical dependencies
- Review and update this documentation

### Quarterly
- Evaluate major version updates
- Plan migration strategies
- Update testing procedures

---

## Contact & Support

For issues with updates:
1. Check rollback procedures above
2. Review backup files
3. Check git history for changes
4. Consult package migration guides

---

## References

- [Vite 7 Migration Guide](https://vite.dev/guide/migration.html)
- [Django Security Releases](https://www.djangoproject.com/weblog/)
- [npm Security Best Practices](https://docs.npmjs.com/auditing-package-dependencies-for-security-vulnerabilities)
- [Python Security Advisories](https://osv.dev/)
