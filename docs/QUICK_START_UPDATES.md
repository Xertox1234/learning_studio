# Quick Start: Security Updates

## 🚀 Run Security Patches Now

```bash
# 1. First, do a dry run to see what would be updated
./scripts/update_security_patches.sh --dry-run

# 2. If everything looks good, apply the updates
./scripts/update_security_patches.sh

# 3. Test your application
python manage.py test
python manage.py runserver

# 4. Test frontend
cd frontend
npm run dev
```

---

## 📊 What Gets Updated

### Critical Security Fixes (Safe Updates)
✅ **cryptography** - Encryption security patches  
✅ **requests** - HTTP security fixes  
✅ **djangorestframework-simplejwt** - JWT authentication fix  
✅ **PyJWT** - Token security updates  
✅ Plus 10+ other security and bug fixes

### ⚠️ Not Updated (Requires Manual Review)
- **vite** - Major version (breaking changes) - Use separate script
- **openai** - Major version (API restructure)
- **django-allauth** - Major version (config changes)
- **tailwindcss** - Major version (config changes)

---

## 🔧 Vite Security Update (Breaking Change)

```bash
# Only run this after testing the main security patches
# This fixes a moderate security vulnerability in dev server

# 1. Dry run first
./scripts/update_vite_major.sh --dry-run

# 2. Apply update
./scripts/update_vite_major.sh

# 3. Test thoroughly
cd frontend
npm run dev      # Test dev server
npm run build    # Test production build
npm run preview  # Test preview
```

---

## 🔄 If Something Breaks (Rollback)

```bash
# Python packages
cp requirements.txt.backup.YYYYMMDD_HHMMSS requirements.txt
pip install -r requirements.txt

# Frontend packages
cd frontend
cp package.json.backup.YYYYMMDD_HHMMSS package.json
npm install
```

---

## 📝 Files Created/Modified

**Scripts:**
- `scripts/update_security_patches.sh` - Main security update script
- `scripts/update_vite_major.sh` - Vite major version update

**Documentation:**
- `docs/SECURITY_UPDATES.md` - Complete update documentation

**Backups (auto-created):**
- `requirements.txt.backup.TIMESTAMP`
- `package.json.backup.TIMESTAMP`

---

## ✅ Testing Checklist

After running updates:

**Backend:**
- [ ] `python manage.py test` passes
- [ ] Server starts without errors
- [ ] Login/authentication works
- [ ] API endpoints respond
- [ ] Admin panel loads

**Frontend:**
- [ ] Dev server starts
- [ ] Code editor works
- [ ] All pages load
- [ ] No console errors

---

## 📞 Need Help?

See full documentation: `docs/SECURITY_UPDATES.md`

**Common Issues:**
1. **Import errors** → Check if packages installed correctly
2. **Build fails** → Review error messages, may need rollback
3. **Tests fail** → Check if due to legitimate bugs or test issues
