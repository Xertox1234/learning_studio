# Python Learning Studio Documentation

Welcome to the Python Learning Studio documentation! This guide helps you find the information you need quickly.

**Last Updated:** October 20, 2025
**Documentation Version:** 2.1

---

## 🚀 Quick Start

**New to the project?** Start with these essential documents:

1. **[Root CLAUDE.md](../CLAUDE.md)** - Complete development guide with commands, architecture, and patterns
2. **[Security Overview](./security/)** - Current security posture and achievements
3. **[API Reference](./api-reference.md)** - API endpoints and usage

---

## 📚 Documentation Overview

### Project Status

| Aspect | Status | Details |
|--------|--------|---------|
| **Security** | ✅ PRODUCTION READY | All 6 critical CVEs resolved + SQL injection fix |
| **Test Coverage** | ✅ 164+ tests | 100% passing (63 new tests in Oct 2025) |
| **Architecture** | ✅ REFACTORED | Modular API structure (Aug 2025) |
| **Performance** | ✅ OPTIMIZED | 100x improvement (forum pagination) |
| **Data Integrity** | ✅ GDPR COMPLIANT | Soft delete + race condition fixes |
| **E2E Testing** | ✅ IMPLEMENTED | Playwright integration |
| **OWASP Compliance** | ✅ COMPLIANT | API Top 10 + Web Top 10 |
| **Accessibility** | ✅ WCAG 2.4.1 | Skip navigation implemented |

---

## 🗂️ Documentation Structure

### Core Documentation

#### [CLAUDE.md](../CLAUDE.md) (Root)
**Your primary development guide** - Contains everything you need for daily development:
- Development commands (Django, React, Docker)
- Architecture overview (dual frontend, Wagtail CMS, API structure)
- Critical patterns (Exercise system, CodeMirror, Forum integration)
- Security implementation patterns
- Testing strategy
- Environment configuration
- Recent updates and timeline

**Start here for:**
- Running the application
- Understanding the codebase
- Development workflows
- Best practices

#### [API Reference](./api-reference.md)
Complete API endpoint documentation (currently a stub - needs expansion):
- Authentication endpoints
- Wagtail CMS endpoints
- Learning endpoints (courses, lessons, exercises)
- Forum endpoints
- Code execution endpoints

**Status:** ⚠️ Needs completion (66 lines, code file not docs)

---

## 🔒 Security Documentation

### Quick Access
- **[Security Index](./security/README.md)** - Complete security overview
- **[CVE Tracker](./security/CVE_TRACKER.md)** - All 6 CVEs with details
- **[Security Complete Guide](./security-complete.md)** - Phased security hardening
- **[IDOR/BOLA Prevention Guide](./idor-bola-prevention-guide.md)** - Comprehensive implementation guide
- **[IDOR Quick Reference](./idor-quick-reference.md)** - Developer cheat sheet

### Security Achievements (October 2025)

All critical vulnerabilities have been resolved with 100% test coverage:

| CVE | Severity | Vulnerability | Status | PR |
|-----|----------|---------------|--------|-----|
| CVE-2024-EXEC-001 | 🔴 CRITICAL | Remote Code Execution | ✅ Fixed | #3 |
| CVE-2024-XSS-002 | 🔴 CRITICAL | XSS in Embed Code | ✅ Fixed | #14 |
| CVE-2024-JWT-003 | 🔴 CRITICAL | JWT in localStorage | ✅ Fixed | #15 |
| CVE-2024-IDOR-001 | 🔴 CRITICAL | Broken Object-Level Auth | ✅ Fixed | #17 |
| CVE-2024-SECRET-005 | 🔴 CRITICAL | Hardcoded SECRET_KEY | ✅ Fixed | - |
| CVE-2025-SQL-001 | 🔴 CRITICAL | SQL Injection via .extra() | ✅ Fixed | - |
| CVE-2024-CSRF-004 | 🟠 HIGH | CSRF Exemptions | ✅ Fixed | - |

**Security Score:** 98/100
**Status:** Production Ready ✅

---

## 🏗️ Architecture Documentation

### System Architecture

#### [Technical Architecture](./technical-architecture.md) (879 lines)
**Most comprehensive architecture document:**
- System overview
- Technology stack
- Component architecture
- Data flow
- Theme system
- Deployment architecture

#### [Current Architecture](./current-architecture.md) (372 lines)
**Status:** ⚠️ Outdated (July 2025, pre-refactoring)
**Note:** Describes monolithic API structure before August 2025 refactoring. Consider archiving.

#### [Forum Architecture](./forum-architecture.md) (359 lines)
**django-machina integration details:**
- Trust levels (TL0-TL4)
- Forum statistics service
- Signal-driven updates
- Review queue system
- Moderation workflows

---

## 🔧 Feature Documentation

### Core Features

| Feature | Documentation | Status |
|---------|---------------|--------|
| **Authentication** | [AUTHENTICATION_SYSTEM.md](./AUTHENTICATION_SYSTEM.md) | ⚠️ Needs JWT cookie update |
| **Code Execution** | [DOCKER_INTEGRATION.md](./DOCKER_INTEGRATION.md) | ✅ Complete |
| **Forum Integration** | [FORUM_INTEGRATION.md](./FORUM_INTEGRATION.md) | ✅ Complete |
| **Exercise System** | [fill-in-the-blank-exercises.md](./fill-in-the-blank-exercises.md) | ✅ Complete |
| **CodeMirror Editor** | [codemirror-integration.md](./codemirror-integration.md) | ✅ Complete |
| **Wagtail CMS** | [wagtail-ai-setup.md](./wagtail-ai-setup.md) | ✅ Complete |
| **Theme System** | [theme-system.md](./theme-system.md) | ✅ Complete |
| **Error Handling** | [error-boundaries.md](./error-boundaries.md) | ✅ Complete |

### Detailed Feature Docs

#### [Docker Integration](./DOCKER_INTEGRATION.md) (308 lines)
Docker-based secure code execution:
- Container configuration
- Resource limits
- Security isolation
- Fallback handling

#### [Authentication System](./AUTHENTICATION_SYSTEM.md) (194 lines)
JWT-based authentication:
- Token generation
- Middleware
- **Note:** Needs update for httpOnly cookie migration (PR #15)

#### [Forum Integration](./FORUM_INTEGRATION.md) (505 lines)
django-machina integration:
- Setup guide
- Trust level system
- Moderation features
- API endpoints

#### [Fill-in-the-Blank Exercises](./fill-in-the-blank-exercises.md) (712 lines)
Interactive exercise system:
- Template syntax (`{{BLANK_N}}`)
- Solution validation
- Progressive hints
- CodeMirror widgets

#### [CodeMirror Integration](./codemirror-integration.md) (393 lines)
Code editor implementation:
- CodeMirror 6 setup
- Custom widgets
- Syntax highlighting
- Blank field handling

#### [Wagtail AI Setup](./wagtail-ai-setup.md) (183 lines)
CMS and AI integration:
- Wagtail configuration
- AI integration (OpenAI)
- Content management

#### [Theme System](./theme-system.md) (274 lines)
Dark/light mode implementation:
- Theme context
- CSS variables
- Persistence
- Component integration

#### [Error Boundaries](./error-boundaries.md) (303 lines)
React error handling:
- Error boundary component
- Fallback UI
- Error reporting

---

## 🧪 Testing Documentation

### Test Strategy

#### [E2E Testing](./e2e-testing.md) (562 lines)
**Excellent Playwright guide for PR #15:**
- Playwright setup
- Cookie testing patterns
- JWT authentication E2E tests
- Test organization

#### [Testing Overview](./testing.md) (258 lines)
**Generic testing info:**
- Unit testing basics
- Test structure
- **Status:** ⚠️ Needs expansion and cross-references

#### [Forum Testing](./forum-testing.md) (645 lines)
**Forum-specific test suite:**
- Trust level tests
- Statistics tests
- Moderation tests
- Signal tests

### Test Coverage

```bash
# Backend tests
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test

# E2E tests
npm run test:e2e

# Security tests
python manage.py test apps.api.tests.test_object_permissions
python manage.py test apps.api.tests.test_xss_protection
python manage.py test apps.api.tests.test_csrf_protection
```

**Total Tests:** 164+ tests (101 security, 63 new P1 fixes), 100% passing

**Latest Test Additions (October 20, 2025):**
- Forum pagination performance tests (5)
- Enrollment concurrency tests (5)
- Soft delete infrastructure tests (20)
- Mutable default prevention tests (12)
- SQL injection prevention tests (5)
- Accessibility tests (3)

---

## ⚙️ Operations Documentation

### Performance & Monitoring

#### [Performance](./performance.md) (301 lines)
Caching strategies:
- Cache warming
- Invalidation patterns
- Repository pattern
- DI container

#### [Monitoring](./monitoring.md) (420 lines)
Observability setup:
- Logging configuration
- Metrics collection
- Health checks
- Error tracking

#### [Rate Limiting](./rate-limiting.md) (438 lines)
API throttling:
- Rate limit configuration
- Per-endpoint limits
- Custom throttle classes
- Testing

#### [Database Indexes](./database-indexes.md) (241 lines)
Database optimization:
- Index strategies
- Query optimization
- Performance analysis

---

## 📊 Session Reports & Best Practices

### Recent Session Work (October 2025)

#### [Session Summary - October 20, 2025](./SESSION_SUMMARY_2025_10_20.md) (513 lines)
**Comprehensive documentation of Phase 1 P1 critical fixes:**
- Executive summary with key metrics (6/10 P1 todos completed)
- Detailed implementation of each fix with before/after code
- Technical achievements (security, performance, data integrity)
- Test coverage summary (63 new tests, 100% passing)
- Git commit history (8 commits)
- Remaining work analysis
- Lessons learned and best practices
- Performance benchmarks (100x improvements)

#### [Phase 1 P1 Best Practices](./PHASE1_P1_BEST_PRACTICES.md) (60KB+)
**Patterns and lessons from Phase 1 critical fixes:**
- Atomic transaction patterns
- Database-level pagination strategies
- Soft delete implementation with GDPR compliance
- Race condition prevention techniques
- N+1 query prevention
- Migration safety patterns
- Comprehensive testing strategies

#### [Remaining P1 Priority Assessment](./REMAINING_P1_PRIORITY_ASSESSMENT.md) (15KB)
**Prioritization analysis for next session:**
- Detailed analysis of 3 remaining P1 todos
- Effort estimates and risk assessment
- Corrected todo #025 (false alarm - file is fine)
- Recommended next steps (Type Hints → Keyboard Navigation)
- Session metrics summary

#### [Phase 1 Completion Index](./PHASE1_COMPLETION_INDEX.md)
**Quick navigation hub for all Phase 1 work:**
- Document navigation table
- Executive summary of 6 completed + 3 remaining todos
- Key metrics (63 tests, 8 commits, 100x performance)
- Code examples reference (atomic transactions, pagination, soft delete)
- Test examples reference (performance, concurrency, SQL verification)
- Git commit history
- Files modified list
- Next session preparation guide
- Quick reference card

---

## 📊 Audit Reports

Historical audit reports for reference:

### [Security Audit 2025](./audits/security-audit-2025.md) (738 lines)
**Complete security evolution timeline:**
- Phase-by-phase remediation
- Before/after code comparisons
- Test coverage details
- Compliance status
- **Updated:** October 17, 2025 with PR #17

### [Architecture Review 2025](./audits/architecture-review-2025.md)
Architectural analysis:
- Pattern identification
- Modular structure review
- Dependency injection
- Repository pattern

### [Code Quality Review 2025](./audits/code-quality-review-2025.md)
Code quality metrics:
- Complexity analysis
- Best practices adherence
- Refactoring opportunities

### [Pattern Analysis 2025](./audits/pattern-analysis-2025.md)
Design pattern analysis:
- Pattern usage
- Anti-patterns
- Consistency review

### [Data Integrity Audit 2025](./audits/data-integrity-audit-2025.md)
Data integrity review:
- Migration safety
- Constraint validation
- Referential integrity

### [Critical Findings Summary](./audits/critical-findings-summary.md)
Executive summary of all audit findings.

---

## 📝 Miscellaneous Documentation

### Updates & Maintenance

#### [SECURITY_UPDATES.md](./SECURITY_UPDATES.md) (260 lines)
**Dependency security updates:**
- Update scripts
- Security patches
- Rollback procedures
- Testing checklist
- **Note:** This is about dependency updates, not codebase security fixes

#### [Dependency Audit Report (October 2025)](./dependency-audit-report-2025-10.md) (345 lines)
Point-in-time dependency audit.

#### [Recommended Updates (October 2025)](./recommended-updates-october-2025.md) (279 lines)
Temporal update recommendations.

### Migration & Planning

#### [Migration Notes](./migration-notes.md) (112 lines)
**Status:** ⚠️ Unclear which migration this refers to

#### [Headless CMS Migration Plan](./headless-cms-migration-plan.md) (298 lines)
**Status:** ⚠️ Planning document - archive if not executing

#### [Quick Start Updates](./QUICK_START_UPDATES.md) (117 lines)
**Status:** ⚠️ Unclear purpose, content outdated

---

## 🎯 Documentation by Role

### For New Contributors

1. **[Root CLAUDE.md](../CLAUDE.md)** - Start here!
2. **[Technical Architecture](./technical-architecture.md)** - Understand the system
3. **[Security Overview](./security/)** - Learn security patterns
4. **[API Reference](./api-reference.md)** - API usage

**Quick Commands:**
```bash
# Start backend
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver

# Start frontend
cd frontend && npm run dev

# Run tests
python manage.py test
npm run test:e2e
```

### For Security Auditors

1. **[Security Index](./security/README.md)** - Security documentation hub
2. **[CVE Tracker](./security/CVE_TRACKER.md)** - All vulnerabilities and fixes
3. **[Security Audit 2025](./audits/security-audit-2025.md)** - Complete audit timeline
4. **[IDOR/BOLA Prevention](./idor-bola-prevention-guide.md)** - Authorization patterns

**Security Status:**
- ✅ All 5 critical CVEs resolved
- ✅ 101 security tests (100% passing)
- ✅ OWASP compliant
- ✅ Production ready

### For Frontend Developers

1. **[Root CLAUDE.md](../CLAUDE.md)** - Development setup
2. **[Theme System](./theme-system.md)** - Theming patterns
3. **[CodeMirror Integration](./codemirror-integration.md)** - Editor customization
4. **[Error Boundaries](./error-boundaries.md)** - Error handling
5. **[E2E Testing](./e2e-testing.md)** - Playwright tests

**Frontend Stack:**
- React 18 + Vite
- Tailwind CSS
- React Router
- CodeMirror 6
- DOMPurify (XSS protection)

### For Backend Developers

1. **[Root CLAUDE.md](../CLAUDE.md)** - Development setup
2. **[Technical Architecture](./technical-architecture.md)** - System design
3. **[API Reference](./api-reference.md)** - API endpoints
4. **[Docker Integration](./DOCKER_INTEGRATION.md)** - Code execution
5. **[Performance](./performance.md)** - Optimization patterns

**Backend Stack:**
- Django 5.0 + DRF
- Wagtail CMS
- django-machina (forum)
- PostgreSQL (production)
- Docker (code execution)

### For DevOps Engineers

1. **[Monitoring](./monitoring.md)** - Observability
2. **[Performance](./performance.md)** - Optimization
3. **[Database Indexes](./database-indexes.md)** - DB optimization
4. **[Docker Integration](./DOCKER_INTEGRATION.md)** - Container management
5. **[Security Overview](./security/)** - Security posture

**Key Services:**
- Django backend (port 8000)
- React frontend (port 3000/3001)
- Docker code executor
- PostgreSQL database

---

## 🔄 Recent Updates

### October 20, 2025 - Phase 1 P1 Critical Fixes
- ✅ **6 of 10 P1 Critical Todos Completed** ([Session Summary](./SESSION_SUMMARY_2025_10_20.md))
  - **SQL Injection Fix (CVE-2025-SQL-001):** Replaced `.extra()` with safe Django ORM
  - **Mutable Default Prevention:** 12 comprehensive tests added
  - **Skip Navigation Link:** WCAG 2.4.1 Level A compliance
  - **Forum Pagination OOM Fix:** 100x memory reduction (1GB → 10MB), 100x faster (5s → 50ms)
  - **Enrollment Race Condition Fix:** Atomic transactions with `select_for_update()`
  - **Soft Delete Infrastructure:** GDPR Article 17 compliance with PII anonymization
  - 63 new tests added (100% passing)
  - 8 commits pushed to GitHub
  - [Best Practices Documentation](./PHASE1_P1_BEST_PRACTICES.md)
  - [Remaining Work Assessment](./REMAINING_P1_PRIORITY_ASSESSMENT.md)

### October 17, 2025
- ✅ **PR #17:** IDOR/BOLA prevention (CVE-2024-IDOR-001)
  - Three-layer defense strategy
  - 22 comprehensive tests
  - 7 ViewSets secured
  - Security-Sentinel review passed

### October 16, 2025
- ✅ **Phase 2:** Security hardening
  - CSRF protection (12 endpoints)
  - SECRET_KEY environment variable
  - Code execution authentication

### October 2025
- ✅ **PR #15:** JWT httpOnly cookies (CVE-2024-JWT-003)
  - XSS-resistant token storage
  - 15 E2E tests with Playwright
  - Complete documentation

- ✅ **PR #14:** XSS vulnerability fixes (CVE-2024-XSS-002)
  - 23 XSS vulnerabilities fixed
  - DOMPurify integration
  - Centralized sanitization

- ✅ **PR #3:** RCE vulnerability fix (CVE-2024-EXEC-001)
  - Removed exec() fallback
  - Docker enforcement

### August 2025
- ✅ **API Refactoring:** Modular ViewSet structure
  - Broke 3,238-line monolith into modules
  - Repository pattern
  - Dependency injection
  - Service layer extraction

- ✅ **Exercise System:** Fill-in-blank and multi-step exercises
- ✅ **Blog/Courses Redesign:** Modern gradient design
- ✅ **Forum System:** django-machina integration with trust levels

---

## 📖 Documentation Standards

When updating documentation:

1. **Update "Last Updated" date** in file header
2. **Ensure cross-references** are maintained
3. **Test all code examples**
4. **Update this README** if adding new files
5. **Follow markdown formatting** standards
6. **Include version information** for external dependencies

---

## 🐛 Documentation Issues

Found outdated or incorrect documentation?

1. Check [GitHub Issues](https://github.com/Xertox1234/learning_studio/issues)
2. Create a new issue with:
   - File name and line number
   - What's incorrect
   - Suggested correction
3. Label as `documentation`

---

## 📚 External Resources

### Django & DRF
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Wagtail Documentation](https://docs.wagtail.org/)

### React & Frontend
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [CodeMirror 6](https://codemirror.net/)

### Security
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Web Application Top 10](https://owasp.org/Top10/)
- [CWE Database](https://cwe.mitre.org/)

### Testing
- [Playwright Documentation](https://playwright.dev/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)

---

## 🎓 Learning Path

**Recommended learning order for new developers:**

1. **Week 1: Setup & Basics**
   - Read [Root CLAUDE.md](../CLAUDE.md)
   - Set up development environment
   - Run backend and frontend
   - Explore admin panel

2. **Week 2: Architecture**
   - Read [Technical Architecture](./technical-architecture.md)
   - Understand dual frontend approach
   - Study API structure
   - Review exercise system

3. **Week 3: Security**
   - Read [Security Overview](./security/)
   - Understand security patterns
   - Study IDOR/BOLA prevention
   - Review XSS protection

4. **Week 4: Features**
   - Deep dive into specific features
   - Read relevant feature docs
   - Study code examples
   - Write first contribution

---

## 🤝 Contributing to Documentation

We welcome documentation improvements!

### Quick Fixes
- Typos and grammar
- Broken links
- Outdated version numbers
- Code example corrections

### Major Updates
- New feature documentation
- Architecture changes
- Security updates
- API changes

**Process:**
1. Create feature branch
2. Make changes
3. Update this README if needed
4. Submit pull request
5. Label as `documentation`

---

## 📞 Support

### Questions?
- Review [CLAUDE.md](../CLAUDE.md) for development questions
- Check [GitHub Issues](https://github.com/Xertox1234/learning_studio/issues) for known issues
- Review relevant feature documentation

### Security Issues?
- **DO NOT** open public issues
- Email: security@pythonlearning.studio
- Follow responsible disclosure timeline (90 days)

---

**Documentation maintained by the Python Learning Studio team.**

**Last Updated:** October 20, 2025
**Next Review:** January 2026
