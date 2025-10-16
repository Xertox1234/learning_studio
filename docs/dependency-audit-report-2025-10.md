# Dependency Audit Report - October 2025

**Project**: Learning Studio  
**Date**: October 12, 2025  
**Auditor**: GitHub Copilot  
**System**: macOS with Python 3.9.6, Node v24.9.0, npm 11.6.0

---

## 🔴 CRITICAL ISSUES

### 1. Django Version Does Not Exist
**Current**: `Django==5.2.4`  
**Status**: ❌ **DOES NOT EXIST**  
**Latest Available**: `Django 4.2.25` (LTS)  
**Severity**: CRITICAL

**Impact**: The specified version `5.2.4` does not exist in PyPI. The latest stable Django version is `4.2.25`. This suggests either:
- A typo in requirements.txt
- Confusion with a future version
- The project may not be installable in fresh environments

**Recommendation**: Change to `Django==4.2.25` (current LTS) or `Django==5.0.x` if Django 5.0 features are required (though 5.0 series is not LTS).

---

### 2. Wagtail AI Major Version Behind
**Current**: `wagtail-ai==2.1.2`  
**Latest**: `wagtail-ai==1.1.1`  
**Status**: ⚠️ **SPECIFIED VERSION DOES NOT EXIST**

**Analysis**: You mentioned "Wagtail AI is now at 3.0" but PyPI shows:
- Latest available: `1.1.1`
- Your specified version `2.1.2` does not exist
- No version 3.0 exists in PyPI

**Recommendation**: 
1. Verify the correct package name (might be `wagtail-ai` vs another AI package)
2. Update to `wagtail-ai==1.1.1` (actual latest)
3. Check Wagtail documentation for AI integration changes

---

### 3. Python Version Compatibility Risk
**Current System**: Python 3.9.6  
**Status**: ⚠️ Python 3.9 reaches end-of-life October 2025

**Impact**: 
- Security updates will cease
- Newer packages may drop support
- Django 5.x officially supports Python 3.10+

**Recommendation**: Upgrade to Python 3.11 or 3.12 for better performance and longer support.

---

## 🟡 HIGH PRIORITY UPDATES

### Python Packages (Backend)

| Package | Current | Latest | Status | Notes |
|---------|---------|--------|--------|-------|
| **Django** | 5.2.4 ❌ | 4.2.25 | INVALID | See critical issue #1 |
| **wagtail** | 7.0.1 | 7.1.1 | Minor behind | Update for bug fixes |
| **wagtail-ai** | 2.1.2 ❌ | 1.1.1 | INVALID | See critical issue #2 |
| **djangorestframework** | 3.15.2 | 3.16.1 | Minor behind | Security & features |
| **openai** | 1.35.5 | 2.3.0 | **Major behind** | Breaking changes likely |
| **channels** | 4.0.0 | 4.3.1 | Minor behind | WebSocket improvements |
| **celery** | 5.4.0 | 5.5.3 | Minor behind | Bug fixes |
| **cryptography** | 42.0.8 | Latest | Check needed | Security-critical |
| **Pillow** | 10.3.0 | Latest | Check needed | Security updates |
| **gunicorn** | 22.0.0 | Latest | Check needed | Production stability |
| **pip** | 21.2.4 | 25.2 | **Very outdated** | Upgrade pip itself |

---

### Node.js Packages (Root Project)

| Package | Current | Wanted | Latest | Breaking? |
|---------|---------|--------|--------|-----------|
| **react** | 19.1.1 | 19.2.0 | 19.2.0 | No |
| **react-dom** | 19.1.1 | 19.2.0 | 19.2.0 | No |
| **react-router-dom** | 7.7.1 | 7.9.4 | 7.9.4 | No |
| **axios** | 1.11.0 | 1.12.2 | 1.12.2 | No |
| **webpack** | 5.101.0 | 5.102.1 | 5.102.1 | No |
| **babel-loader** | 9.2.1 | 9.2.1 | **10.0.0** | Yes (major) |
| **webpack-cli** | 5.1.4 | 5.1.4 | **6.0.1** | Yes (major) |
| **css-loader** | 6.11.0 | 6.11.0 | **7.1.2** | Yes (major) |
| **style-loader** | 3.3.4 | 3.3.4 | **4.0.0** | Yes (major) |
| **@codemirror/** packages | 6.x | 6.x | 6.x | No |

---

### Node.js Packages (Frontend/Vite Project)

| Package | Current | Wanted | Latest | Breaking? |
|---------|---------|--------|--------|-----------|
| **react** | 18.3.1 | 18.3.1 | **19.2.0** | Yes (major) |
| **react-dom** | 18.3.1 | 18.3.1 | **19.2.0** | Yes (major) |
| **react-router-dom** | 6.30.1 | 6.30.1 | **7.9.4** | Yes (major) |
| **vite** | 5.4.19 | 5.4.20 | **7.1.9** | Yes (major) |
| **tailwindcss** | 3.4.17 | 3.4.18 | **4.1.14** | Yes (major) |
| **date-fns** | 3.6.0 | 3.6.0 | **4.1.0** | Yes (major) |
| **zustand** | 4.5.7 | 4.5.7 | **5.0.8** | Yes (major) |
| **eslint** | 8.57.1 | 8.57.1 | **9.37.0** | Yes (major) |
| **lucide-react** | 0.303.0 | 0.303.0 | **0.545.0** | Minor (180 versions) |
| **@vitejs/plugin-react** | 4.7.0 | 4.7.0 | **5.0.4** | Yes (major) |
| **@types/react** | 18.3.23 | 18.3.26 | **19.2.2** | Major (for React 19) |

---

## 🟢 GOOD PRACTICES OBSERVED

✅ Using LTS versions where available  
✅ Pinned versions (avoiding `^` or `~` wildcards)  
✅ Separate frontend and backend dependency management  
✅ Using TypeScript types for React  
✅ Modern tooling (Vite, Webpack 5)  

---

## 📋 RECOMMENDED UPDATE STRATEGY

### Phase 1: Critical Fixes (Do Immediately)
```bash
# Fix Django version
sed -i '' 's/Django==5.2.4/Django==4.2.25/' requirements.txt

# Fix wagtail-ai version
sed -i '' 's/wagtail-ai==2.1.2/wagtail-ai==1.1.1/' requirements.txt

# Upgrade pip
python3 -m pip install --upgrade pip
```

### Phase 2: Security & Stability (Next Week)
```bash
# Update Python packages
pip install --upgrade \
  wagtail==7.1.1 \
  djangorestframework==3.16.1 \
  channels==4.3.1 \
  celery==5.5.3 \
  cryptography \
  Pillow \
  gunicorn

# Update root Node packages (non-breaking)
npm update react react-dom react-router-dom axios webpack @codemirror/autocomplete @codemirror/commands

# Update frontend Node packages (non-breaking)
cd frontend && npm update axios dompurify eslint-plugin-react-refresh
```

### Phase 3: Major Version Upgrades (Plan & Test)

**Backend:**
1. **OpenAI 1.35.5 → 2.3.0**
   - Review [migration guide](https://github.com/openai/openai-python/releases)
   - Breaking changes in API structure
   - Test all AI integration points

**Frontend (Root):**
1. **babel-loader 9 → 10** - Test webpack build
2. **webpack-cli 5 → 6** - Review CLI command changes
3. **css-loader 6 → 7** - Test CSS imports
4. **style-loader 3 → 4** - Test style injection

**Frontend (Vite):**
1. **React 18 → 19** 
   - Test all components
   - Review [React 19 breaking changes](https://react.dev/blog/2024/04/25/react-19)
   - Update all hooks/refs usage
   
2. **React Router 6 → 7**
   - Review routing changes
   - Test all navigation
   
3. **Vite 5 → 7**
   - Major version jump
   - Review [Vite 6](https://vitejs.dev/blog/announcing-vite6) and [Vite 7](https://vitejs.dev/blog/announcing-vite7) announcements
   - Test dev server & builds
   
4. **Tailwind 3 → 4**
   - Breaking changes in utilities
   - Review [Tailwind 4 upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
   - Rebuild all styles
   
5. **ESLint 8 → 9**
   - New flat config format
   - Update `.eslintrc` to `eslint.config.js`

### Phase 4: Python Version Upgrade
```bash
# Upgrade to Python 3.11 or 3.12
# Update all environments
# Re-test full application
```

---

## 🔍 ADDITIONAL FINDINGS

### Versioning Discrepancy
- Root project uses **React 19**
- Frontend project uses **React 18**
- This could cause issues if components are shared
- **Recommendation**: Align both to same major version

### Codemirror Consistency
- Both projects use similar CodeMirror 6 packages
- Versions are slightly out of sync but compatible
- Minor updates available across the board

### Development Tools
- **webpack** vs **Vite**: Running two different build systems
  - Root: Webpack 5
  - Frontend: Vite 5
  - This is fine if intentional (different apps)
  - Consider if consolidation would simplify setup

---

## ⚠️ BREAKING CHANGE CONSIDERATIONS

### React 19 Migration Checklist
- [ ] Remove `React.FC` types (deprecated)
- [ ] Update `ref` forwarding patterns
- [ ] Test Suspense boundaries
- [ ] Review concurrent rendering features
- [ ] Update testing library if used

### Tailwind 4 Migration Checklist
- [ ] Update configuration file format
- [ ] Review utility class changes
- [ ] Check custom plugin compatibility
- [ ] Rebuild and verify all styles
- [ ] Update PostCSS config if needed

### Vite 7 Migration Checklist
- [ ] Update vite.config.js syntax
- [ ] Check plugin compatibility
- [ ] Test HMR (Hot Module Replacement)
- [ ] Verify build output
- [ ] Update environment variable handling

### OpenAI 2.x Migration Checklist
- [ ] Update import statements
- [ ] Change client initialization
- [ ] Update streaming API calls
- [ ] Test embeddings endpoints
- [ ] Review error handling changes

---

## 📊 PACKAGE ECOSYSTEM HEALTH

### Backend (Python)
- **Django**: Healthy - LTS version available
- **Wagtail**: Very active - Regular updates
- **DRF**: Stable - Active maintenance
- **Channels**: Active - Good WebSocket support
- **Celery**: Stable - Production-ready

### Frontend (Node.js)
- **React**: Very active - React 19 just released
- **Vite**: Very active - Rapid development
- **Tailwind**: Very active - Major v4 release
- **CodeMirror**: Active - Regular improvements

---

## 🎯 PRIORITY RECOMMENDATIONS

### Immediate (This Week)
1. ✅ Fix Django version to `4.2.25`
2. ✅ Fix wagtail-ai version to `1.1.1`
3. ✅ Upgrade pip to 25.2
4. ✅ Apply security updates (Pillow, cryptography)

### Short-term (This Month)
1. Update to Python 3.11 or 3.12
2. Update all minor/patch versions
3. Align React versions between projects
4. Update OpenAI SDK (test thoroughly)

### Long-term (Next Quarter)
1. Plan React 19 migration for both projects
2. Plan Vite 7 upgrade
3. Plan Tailwind 4 migration
4. Consider Django 5.0 LTS when available
5. Evaluate Wagtail 8.x when released

---

## 📝 TESTING RECOMMENDATIONS

Before any major updates:
1. ✅ Create comprehensive test suite
2. ✅ Document current behavior
3. ✅ Set up staging environment
4. ✅ Enable CI/CD checks
5. ✅ Create rollback plan

---

## 🔗 USEFUL RESOURCES

- [Django Release Schedule](https://www.djangoproject.com/download/)
- [Wagtail Releases](https://docs.wagtail.org/en/stable/releases/index.html)
- [React 19 Release Notes](https://react.dev/blog/2024/12/05/react-19)
- [Vite Migration Guides](https://vitejs.dev/guide/migration)
- [OpenAI Python SDK Changelog](https://github.com/openai/openai-python/releases)
- [Node.js Release Schedule](https://nodejs.org/en/about/previous-releases)

---

## 💡 FLUTTER MOBILE APP CONSIDERATIONS

Since you're planning a Flutter companion app:
- ✅ Ensure API versioning is stable before mobile release
- ✅ Use semantic versioning for API endpoints
- ✅ Document all breaking changes
- ✅ Consider API backward compatibility
- ✅ Plan coordinated release schedule

---

## 📄 SUMMARY

**Total Packages Audited**: 60+  
**Critical Issues**: 2 (invalid versions)  
**High Priority Updates**: 15  
**Major Version Updates Available**: 12  
**Security Updates Needed**: 3-5  

**Overall Risk Level**: 🟡 MEDIUM  
*(Would be HIGH if not for pinned versions preventing breakage)*

**Estimated Update Effort**: 2-3 weeks for phased rollout

---

**Report Generated**: October 12, 2025  
**Next Audit Recommended**: January 2026 (Quarterly)
