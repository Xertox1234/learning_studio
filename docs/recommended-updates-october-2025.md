# Recommended Updates - October 2025

**Project**: Learning Studio  
**Date**: October 12, 2025  
**Focus**: Minor updates and maintenance

---

## 🎯 Core Framework Updates

### Python Backend

| Package | Current | Latest | Update Type | Priority |
|---------|---------|--------|-------------|----------|
| **Django** | 5.2.4 | 5.2.7 | Patch | High |
| **Wagtail** | 7.0.1 | 7.1.1 | Minor | High |
| **Wagtail AI** | 2.1.2 | 2.1.2 ✅ | N/A | Already latest! |

**Note**: Wagtail AI 3.0.0a1 (alpha) is available but not recommended for production yet.

---

## 📦 Other Python Package Updates

### API & Framework
- `djangorestframework`: 3.15.2 → 3.16.1 (minor update, new features)
- `channels`: 4.0.0 → 4.3.1 (bug fixes & improvements)
- `celery`: 5.4.0 → 5.5.3 (performance & stability)

### AI & Integration
- `openai`: 1.35.5 → 2.3.0 (⚠️ major update - breaking changes, plan carefully)

### Security & Production
- `cryptography`: 42.0.8 → Latest (security updates)
- `Pillow`: 10.3.0 → Latest (security updates)
- `gunicorn`: 22.0.0 → Latest (stability improvements)

---

## 🌐 Node.js Package Updates

### Root Project (Webpack)

**Non-Breaking Updates** (safe to update):
```json
{
  "react": "19.1.1" → "19.2.0",
  "react-dom": "19.1.1" → "19.2.0",
  "react-router-dom": "7.7.1" → "7.9.4",
  "axios": "1.11.0" → "1.12.2",
  "webpack": "5.101.0" → "5.102.1",
  "@codemirror/autocomplete": "6.18.6" → "6.19.0",
  "@codemirror/commands": "6.8.1" → "6.9.0",
  "@codemirror/view": "6.38.1" → "6.38.5"
}
```

**Major Updates** (require testing):
- `babel-loader`: 9.2.1 → 10.0.0
- `webpack-cli`: 5.1.4 → 6.0.1
- `css-loader`: 6.11.0 → 7.1.2
- `style-loader`: 3.3.4 → 4.0.0

### Frontend Project (Vite)

**⚠️ React Version Discrepancy Detected:**
- Root project: React 19.1.1
- Frontend project: React 18.3.1

**Recommendation**: Either:
1. Update frontend to React 19 (test thoroughly)
2. Keep both on React 18 until ready for major migration

**Safe Updates for Frontend**:
```json
{
  "axios": "1.11.0" → "1.12.2",
  "dompurify": "3.2.6" → "3.2.7",
  "@uiw/react-codemirror": "4.24.1" → "4.25.2",
  "@codemirror/autocomplete": "6.18.6" → "6.19.0",
  "@codemirror/commands": "6.8.1" → "6.9.0",
  "@codemirror/view": "6.38.1" → "6.38.5"
}
```

**Major Updates Available** (defer for now):
- `react`: 18.3.1 → 19.2.0 (major)
- `react-router-dom`: 6.30.1 → 7.9.4 (major)
- `vite`: 5.4.19 → 7.1.9 (major - skip v6!)
- `tailwindcss`: 3.4.17 → 4.1.14 (major)
- `zustand`: 4.5.7 → 5.0.8 (major)
- `eslint`: 8.57.1 → 9.37.0 (major)

---

## 🚀 Quick Update Commands

### Phase 1: Critical Backend Updates (Do First)

```bash
# Update requirements.txt
sed -i '' 's/Django==5.2.4/Django==5.2.7/' requirements.txt
sed -i '' 's/wagtail==7.0.1/wagtail==7.1.1/' requirements.txt
sed -i '' 's/djangorestframework==3.15.2/djangorestframework==3.16.1/' requirements.txt
sed -i '' 's/channels==4.0.0/channels==4.3.1/' requirements.txt
sed -i '' 's/celery==5.4.0/celery==5.5.3/' requirements.txt

# Install updates
pip3 install -r requirements.txt --upgrade

# Run migrations if needed
python3 manage.py migrate

# Test the application
python3 manage.py check
```

### Phase 2: Root Node.js Updates (Safe)

```bash
# Update package.json versions
npm update react react-dom react-router-dom axios webpack

# Or update all non-breaking
npm update

# Test build
npm run build
```

### Phase 3: Frontend Node.js Updates (Safe)

```bash
cd frontend

# Update safe packages
npm update axios dompurify @uiw/react-codemirror @codemirror/autocomplete @codemirror/commands @codemirror/view

# Test dev server
npm run dev

# Test production build
npm run build
```

---

## ⚠️ Items to Defer (Requires Planning)

### OpenAI SDK 1.x → 2.x
**Breaking Changes**:
- Client initialization syntax changed
- Streaming API restructured
- Error handling updated

**Action**: Schedule dedicated testing sprint before updating.

### React 18 → 19 (Frontend)
**Breaking Changes**:
- New compiler and runtime
- Hook behavior changes
- Concurrent features enabled by default

**Action**: Align both projects to same React version first, then plan migration together.

### Vite 5 → 7
**Major Jump**: Skipping Vite 6 entirely.

**Action**: Review Vite 6 & 7 changelogs, plan comprehensive testing.

### Tailwind 3 → 4
**Breaking Changes**:
- Configuration format changed
- Some utility classes removed/renamed
- Plugin API updated

**Action**: Dedicate time to review all custom styles and utilities.

---

## 🧪 Testing Checklist (After Updates)

### Backend
- [ ] Run `python3 manage.py check`
- [ ] Run `python3 manage.py migrate --check`
- [ ] Test admin panel
- [ ] Test API endpoints
- [ ] Test Wagtail CMS pages
- [ ] Test AI features
- [ ] Test WebSocket connections (Channels)
- [ ] Test async tasks (Celery)

### Frontend (Both Projects)
- [ ] Dev server starts without errors
- [ ] Production build completes
- [ ] All routes load correctly
- [ ] CodeMirror editors work
- [ ] API calls succeed
- [ ] Authentication flow works
- [ ] No console errors

---

## 📊 Update Priority Matrix

| Priority | Package | Risk | Effort | Benefit |
|----------|---------|------|--------|---------|
| 🔴 **High** | Django 5.2.4→5.2.7 | Low | 5 min | Security fixes |
| 🔴 **High** | Wagtail 7.0.1→7.1.1 | Low | 5 min | Bug fixes |
| 🟡 **Medium** | DRF 3.15.2→3.16.1 | Low | 10 min | New features |
| 🟡 **Medium** | Channels 4.0.0→4.3.1 | Low | 10 min | Stability |
| 🟡 **Medium** | Celery 5.4.0→5.5.3 | Low | 10 min | Performance |
| 🟡 **Medium** | Node packages (safe) | Low | 15 min | Maintenance |
| 🟢 **Low** | OpenAI 1.x→2.x | High | 2-4 hours | New features |
| 🟢 **Low** | React 18→19 | Medium | 4-8 hours | Performance |
| 🟢 **Low** | Major Node updates | High | 1-2 days | Latest features |

---

## 🎯 Recommended Timeline

### This Week (1-2 hours)
1. ✅ Update Django to 5.2.7
2. ✅ Update Wagtail to 7.1.1
3. ✅ Update DRF, Channels, Celery
4. ✅ Update safe Node packages
5. ✅ Run full test suite

### This Month (4-8 hours)
1. Plan OpenAI SDK migration
2. Research React 19 migration requirements
3. Align React versions between projects
4. Update security packages (cryptography, Pillow)

### Next Quarter (2-3 weeks)
1. Execute OpenAI 2.x migration
2. Execute React 19 migration
3. Plan Vite 7 upgrade
4. Plan Tailwind 4 upgrade

---

## 💡 Pro Tips

1. **Always backup before updates**: `git commit -am "Pre-update snapshot"`
2. **Update in virtual environment first**: Test before committing
3. **Read changelogs**: Especially for minor version bumps
4. **Test incrementally**: Don't update everything at once
5. **Monitor logs**: Watch for deprecation warnings

---

## 🔗 Quick Reference Links

- [Django 5.2 Release Notes](https://docs.djangoproject.com/en/5.2/releases/)
- [Wagtail 7.1 Release Notes](https://docs.wagtail.org/en/stable/releases/7.1.html)
- [DRF 3.16 Changelog](https://www.django-rest-framework.org/community/release-notes/)
- [OpenAI Python SDK Migration](https://github.com/openai/openai-python/blob/main/CHANGELOG.md)
- [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19)

---

## ✅ Next Steps

1. Review this document
2. Create a backup/snapshot
3. Run Phase 1 updates (30 minutes)
4. Test thoroughly
5. Commit and deploy
6. Plan Phase 2 updates

**Estimated Total Time for Safe Updates**: 2-3 hours  
**Risk Level**: 🟢 Low (all minor/patch updates)  
**Recommended Day**: Early in the week with time to monitor

---

**Document Created**: October 12, 2025  
**Next Review**: December 2025 (or after major feature development)
