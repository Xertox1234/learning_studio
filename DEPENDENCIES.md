# System Dependencies

This document lists system-level dependencies required for Python Learning Studio.

## Required System Libraries

### libmagic (File Type Detection)

**Required for:** File upload MIME type validation (CVE-2024-FILE-001 fix)
**Python package:** `python-magic==0.4.27`

libmagic is a library for detecting file types based on file content (magic bytes), not just file extensions. This provides security against extension spoofing attacks where malicious files are renamed with safe extensions.

#### Installation

**macOS (Homebrew):**
```bash
brew install libmagic
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libmagic1 libmagic-dev
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install file-devel
# OR
sudo dnf install file-devel
```

**Windows:**
```bash
# Install via pip with bundled DLL
pip install python-magic-bin

# OR manually install from:
# https://github.com/pidydx/libmagicwin64
```

**Docker (Alpine):**
```dockerfile
RUN apk add --no-cache libmagic
```

**Docker (Debian/Ubuntu):**
```dockerfile
RUN apt-get update && apt-get install -y libmagic1
```

#### Verification

Test that libmagic is installed correctly:

```bash
python3 -c "import magic; print(magic.from_file('/etc/hosts', mime=True))"
# Expected output: text/plain
```

If you get `ImportError: failed to find libmagic`, the system library is not installed or not in the library path.

#### Graceful Degradation

If libmagic is not installed, the application will still function but with reduced security:
- ✅ Extension validation still active (whitelist-based)
- ✅ Content validation via Pillow still active
- ❌ MIME type validation disabled (graceful fallback)

**Production deployment:** libmagic installation is **strongly recommended** for defense-in-depth security.

## Python Dependencies

All Python dependencies are listed in `requirements.txt`. Install with:

```bash
pip install -r requirements.txt
```

### Key Security-Related Packages

- **Pillow** (10.3.0): Image validation and processing
- **python-magic** (0.4.27): MIME type detection (requires libmagic)
- **bleach** (6.1.0): HTML sanitization (XSS prevention)
- **django-csp** (3.8): Content Security Policy headers
- **django-cors-headers** (4.3.1): CORS policy management

## Development Dependencies

For development and testing:

```bash
pip install -r requirements.txt
```

Includes:
- django-debug-toolbar
- django-extensions
- coverage (for test coverage)

## Troubleshooting

### ImportError: failed to find libmagic

**Problem:** python-magic cannot find the libmagic system library.

**Solutions:**

1. **Verify installation:**
   ```bash
   # macOS
   brew list libmagic

   # Ubuntu/Debian
   dpkg -l | grep libmagic

   # CentOS/RHEL
   rpm -qa | grep file-libs
   ```

2. **Set library path (macOS):**
   ```bash
   export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
   ```

3. **Set library path (Linux):**
   ```bash
   export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
   ```

4. **Windows alternative:**
   ```bash
   pip uninstall python-magic
   pip install python-magic-bin
   ```

### File Upload Tests Failing

If file upload tests fail with MIME validation errors:

1. Ensure libmagic is installed (see above)
2. Run tests with verbose output:
   ```bash
   DJANGO_SETTINGS_MODULE=learning_community.settings.development \
     python manage.py test apps.api.tests.test_image_upload_validation -v 2
   ```
3. Check that test images are valid:
   ```bash
   file --mime-type <test-file>
   ```

## Security Notes

### Why libmagic?

File extensions are **not secure** - they can be trivially changed:
```bash
# Malicious script disguised as image
mv malware.sh avatar.jpg
```

libmagic reads the **file content** (magic bytes) to determine the real type:
```python
import magic
magic.from_file('avatar.jpg', mime=True)
# Returns: 'text/x-shellscript' (not image/jpeg!)
```

This defense-in-depth approach prevents:
- **Extension spoofing** attacks
- **Polyglot files** (files valid in multiple formats)
- **MIME type confusion** vulnerabilities

### Additional Validation Layers

libmagic is just one layer. The application also uses:
1. Extension whitelist (reject unknown extensions)
2. **libmagic MIME validation** (this document)
3. Pillow content validation (verify image format)
4. File size limits (prevent DoS)
5. Dimension validation (prevent processing bombs)
6. UUID-based filenames (prevent path traversal)

See `docs/audits/FILE_UPLOAD_SECURITY_AUDIT.md` for complete documentation.

## Production Deployment Checklist

- [ ] libmagic installed on all application servers
- [ ] libmagic installed in Docker containers
- [ ] Verification test passes: `python -c "import magic; print('OK')"`
- [ ] File upload tests passing: `python manage.py test apps.api.tests.test_image_upload_validation`
- [ ] Upload limits configured: `FILE_UPLOAD_MAX_MEMORY_SIZE = 5MB`
- [ ] Rate limiting active: `DEFAULT_THROTTLE_RATES = {'file_upload': '10/minute'}`

## References

- libmagic project: https://github.com/ahupp/python-magic
- File command (uses libmagic): https://www.darwinsys.com/file/
- MIME type detection: https://en.wikipedia.org/wiki/File_(command)
- Security best practices: https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload
