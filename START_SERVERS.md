# 🚀 How to Start the Application

## Quick Start (Copy & Paste)

### Terminal 1: Django Backend (API Server)
```bash
cd /Users/williamtower/projects/learning_studio
source venv/bin/activate
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver
```

**Expected Output**:
```
System check identified no issues (0 silenced).
Django version 5.2.7, using settings 'learning_community.settings.development'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

✅ **Backend is ready** when you see: `Starting development server at http://127.0.0.1:8000/`

---

### Terminal 2: React Frontend (UI Server)
```bash
cd /Users/williamtower/projects/learning_studio/frontend
npm run dev
```

**Expected Output**:
```
  VITE v5.4.20  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

✅ **Frontend is ready** when you see: `Local: http://localhost:3000/`

---

## Access the Application

Once BOTH servers are running:

1. **Open your browser** → http://localhost:3000
2. **Click "Sign in"** or go to http://localhost:3000/login
3. **Use demo credentials**:
   - **Email**: `test@pythonlearning.studio`
   - **Password**: `testpass123`

---

## 🔍 Troubleshooting

### "Cannot connect to server" or Login fails

**Cause**: Django backend is not running

**Solution**:
1. Check Terminal 1 - Django server should show "Starting development server at http://127.0.0.1:8000/"
2. If not running, start it with the command above
3. Test API: http://localhost:8000/api/v1/forums/ (should return JSON)

---

### "Page not found" or White screen

**Cause**: React frontend is not running

**Solution**:
1. Check Terminal 2 - Vite should show "Local: http://localhost:3000/"
2. If not running, start it with `npm run dev` from the frontend directory
3. Make sure you're accessing http://localhost:3000 (NOT port 8000)

---

### Port 8000 or 3000 already in use

**Solution**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

Then restart the servers.

---

### CORS errors in browser console

**Cause**: Accessing the wrong URL

**Solution**: Always use http://localhost:3000 (NOT http://localhost:8000)
- Port 3000 = React frontend (correct)
- Port 8000 = Django API only (for API calls, not direct browsing)

---

## 🎯 Quick Test After Startup

### 1. Test Django API
Open: http://localhost:8000/api/v1/forums/

Expected: JSON response with forum data

### 2. Test React Frontend
Open: http://localhost:3000

Expected: Homepage with navigation

### 3. Test Login
1. Go to: http://localhost:3000/login
2. Enter:
   - Email: `test@pythonlearning.studio`
   - Password: `testpass123`
3. Click "Sign in"
4. Should redirect to dashboard

---

## 📌 Important Notes

- **Always run BOTH servers** for the application to work
- **Use port 3000** in your browser (React frontend)
- **Port 8000** is only for API calls (Django backend)
- **Keep both terminal windows open** while using the app
- **Press Ctrl+C** in each terminal to stop the servers

---

## ✅ Success Checklist

- [ ] Terminal 1 shows: "Starting development server at http://127.0.0.1:8000/"
- [ ] Terminal 2 shows: "Local: http://localhost:3000/"
- [ ] Can access http://localhost:3000 in browser
- [ ] Can log in with demo credentials
- [ ] Forum, courses, and exercises load

---

**Need Help?** Check the docs/headless-cms-migration-plan.md file for detailed architecture information.
