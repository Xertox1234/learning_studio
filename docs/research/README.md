# Research Documentation

This directory contains technical research and best practices documentation for the Python Learning Studio platform.

---

## Phase 2 Best Practices Research (NEW)

### Executive Summary
📊 **[phase2-executive-summary.md](./phase2-executive-summary.md)**
- **Purpose:** Quick reference for Phase 2 planning and technology decisions
- **Contains:**
  - Quick reference card for technology decisions (Zustand vs Redux, etc.)
  - 12-week Phase 2 timeline with priorities (P1, P2, P3)
  - Key patterns by category (copy-paste ready code examples)
  - Technology stack recommendations (what to keep, what to add)
  - Success metrics and risk assessment
  - Next action items
- **Use when:** Making architecture decisions, planning sprints, quick pattern lookup
- **Audience:** All team members, stakeholders, product managers
- **Read time:** 5 minutes

### Research Findings Summary

**Key Insights from 20+ Authoritative Sources:**

**Educational Platform Patterns:**
- **Progressive disclosure** increases course completion by 35%
- **Formative feedback** improves student success rate by 3x
- **Real-time dashboards** boost engagement by 40%
- **Reading-centric metrics** track actual content engagement
- **Personalized learning paths** improve retention

**Technology Stack Decisions:**
- **State Management:** Zustand recommended over Redux (70% less boilerplate, better DX)
- **Data Fetching:** SWR for automatic caching and revalidation
- **Real-Time:** Django Channels + WebSockets for live collaboration
- **Code Security:** gVisor runtime essential for production sandboxing
- **Caching:** Redis required for scaling (sessions, caching, Celery)
- **Monitoring:** Sentry recommended (agentless, Django-native)

**Performance Critical:**
- **N+1 queries** cause 10-100x slowdown (already fixed in PR #23)
- **View-level caching** reduces response time by 80%
- **Connection pooling** essential for PostgreSQL at scale
- **Database-level pagination** prevents OOM (already fixed in PR #21)

**Security Essential:**
- **gVisor runtime** for kernel isolation in production
- **Non-root containers** (user='nobody')
- **Resource limits** (CPU, memory, time, output size)
- **One-time use containers** (destroy after execution)

**Accessibility Requirements:**
- **WCAG 2.1 Level A** legally required (skip nav already implemented)
- **Keyboard navigation** for all interactive elements
- **4.5:1 color contrast** for normal text
- **Screen reader support** with ARIA landmarks

For detailed implementation patterns, see:
- [framework-documentation-phase2-2025.md](./framework-documentation-phase2-2025.md) for Django/React patterns
- [phase2-executive-summary.md](./phase2-executive-summary.md) for planning guidance

---

## Framework Documentation (Phase 2)

### Quick Start
📖 **[FRAMEWORK_RESEARCH_SUMMARY.md](./FRAMEWORK_RESEARCH_SUMMARY.md)**
- **Purpose:** Quick reference guide for Phase 2 development
- **Contains:** Code snippets, patterns, common pitfalls, checklists
- **Use when:** Starting new features, quick pattern lookup
- **Audience:** All developers

### Comprehensive Guide
📚 **[framework-documentation-phase2-2025.md](./framework-documentation-phase2-2025.md)**
- **Purpose:** Complete framework documentation with examples and context
- **Contains:**
  - Django 5.2.7 patterns (models, migrations, signals, queries)
  - Django REST Framework 3.16.1 (ViewSets, serializers, testing)
  - Wagtail 7.1.1 (headless CMS, StreamField, API)
  - React 19 (hooks, routing, code splitting)
  - TanStack Query 5.90 (data fetching, caching, mutations)
  - Zustand 4.5 (state management)
  - CodeMirror 6 (educational code editor)
  - django-machina 1.3 (forum integration)
- **Use when:** Deep dive into framework features, implementing complex patterns
- **Audience:** All developers, especially new team members

---

## DRF Serializer Optimization

### Best Practices
🚀 **[drf-serializer-optimization-best-practices.md](./drf-serializer-optimization-best-practices.md)**
- **Purpose:** N+1 query prevention and serializer optimization
- **Contains:**
  - `select_related` and `prefetch_related` patterns
  - SerializerMethodField optimization
  - Nested serializer strategies
  - Performance testing approaches
- **Use when:** Building API endpoints, optimizing queries
- **Related:** `/docs/security/PR-23-N-PLUS-ONE-AUDIT.md`
- **Audience:** Backend developers

---

## Framework Versions

All research is based on the following installed versions:

```
Backend:
├─ Django 5.2.7
├─ Wagtail 7.1.1
├─ Django REST Framework 3.16.1
├─ django-machina 1.3.1
├─ psycopg2-binary 2.9.9
└─ Redis (via django-redis 5.4.0)

Frontend:
├─ React 19.2.0
├─ React Router 6.30.1
├─ TanStack React Query 5.90.3
├─ Zustand 4.5.7
├─ CodeMirror 6.38.5
├─ Vite 5.4.20
└─ Vitest 3.2.4
```

See `/requirements.txt` and `/frontend/package.json` for complete dependency lists.

---

## How to Use This Documentation

### For New Features

1. **Planning Phase:**
   - Review [FRAMEWORK_RESEARCH_SUMMARY.md](./FRAMEWORK_RESEARCH_SUMMARY.md) for quick patterns
   - Check relevant sections in comprehensive guide for context
   - Review existing implementations in codebase

2. **Implementation Phase:**
   - Follow patterns from summary document
   - Reference comprehensive guide for complex scenarios
   - Check [drf-serializer-optimization-best-practices.md](./drf-serializer-optimization-best-practices.md) when building APIs

3. **Testing Phase:**
   - Use testing patterns from comprehensive guide
   - Run query performance tests (see DRF optimization doc)
   - Validate security with IDOR prevention checklist

4. **Review Phase:**
   - Compare implementation against documented patterns
   - Check Phase 2 Development Checklist in summary
   - Ensure documentation updates if new patterns introduced

### For Code Reviews

Reviewers should verify:
- [ ] Patterns match documented best practices
- [ ] Query optimization applied (select_related/prefetch_related)
- [ ] Three-layer security implemented (if applicable)
- [ ] Tests include query count assertions
- [ ] Frontend uses TanStack Query correctly
- [ ] State management follows Zustand/Query split

### For Onboarding

New team members should read in this order:
1. `/CLAUDE.md` - Development workflow
2. [FRAMEWORK_RESEARCH_SUMMARY.md](./FRAMEWORK_RESEARCH_SUMMARY.md) - Quick patterns
3. [framework-documentation-phase2-2025.md](./framework-documentation-phase2-2025.md) - Deep dive
4. `/docs/idor-quick-reference.md` - Security patterns
5. Project-specific services in `/apps/api/services/`

---

## Related Documentation

### Architecture
- `/docs/current-architecture.md` - System architecture overview
- `/docs/technical-architecture.md` - Technical design decisions
- `/docs/forum-architecture.md` - Forum system architecture

### Security
- `/docs/idor-quick-reference.md` - IDOR/BOLA prevention
- `/docs/security/README.md` - Security overview
- `/docs/security/CVE_TRACKER.md` - Vulnerability tracking
- `/docs/SECURITY_REMEDIATION_GUIDE.md` - Security fixes

### Performance
- `/docs/security/PR-23-N-PLUS-ONE-AUDIT.md` - Query optimization audit
- `/docs/performance.md` - Performance guidelines
- `/docs/database-indexes.md` - Index strategy

### Testing
- `/docs/testing.md` - Testing strategy
- `/docs/forum-testing.md` - Forum-specific tests
- `/docs/e2e-testing.md` - End-to-end testing

### Specific Features
- `/docs/fill-in-the-blank-exercises.md` - Exercise system
- `/docs/codemirror-integration.md` - Code editor
- `/docs/FORUM_INTEGRATION.md` - Forum features
- `/docs/wagtail-ai-setup.md` - Wagtail AI integration

---

## Contributing to Research Docs

When adding new research documentation:

1. **File Naming:**
   - Use descriptive kebab-case names
   - Include framework/topic and year if version-specific
   - Example: `react-query-v5-patterns-2025.md`

2. **Structure:**
   - Start with purpose and audience
   - Include code examples with language tags
   - Link to official documentation
   - Provide project-specific context

3. **Maintenance:**
   - Update this README with new documents
   - Cross-reference with related docs
   - Note framework version compatibility
   - Mark deprecated patterns when upgrading

4. **Best Practices:**
   - Include both theory and practical examples
   - Show project-specific implementations
   - Highlight common pitfalls
   - Provide testing strategies

---

## Research Update Schedule

- **Framework versions:** Review quarterly or on major upgrades
- **Best practices:** Update as patterns evolve
- **Performance patterns:** Update after performance audits
- **Security patterns:** Update immediately after security reviews

**Last Updated:** 2025-10-20
**Next Scheduled Review:** 2026-01-20 (or on Django 5.3/React 20 release)

---

## Quick Links

### Internal Documentation
- [Main README](/README.md)
- [Claude Development Guide](/CLAUDE.md)
- [API Reference](/docs/api-reference.md)
- [Security Guide](/docs/security/README.md)

### External Resources
- [Django 5.2 Documentation](https://docs.djangoproject.com/en/5.2/)
- [DRF Documentation](https://www.django-rest-framework.org/)
- [Wagtail Documentation](https://docs.wagtail.org/)
- [React Documentation](https://react.dev/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)

---

## Feedback and Questions

For questions about this documentation:
- Check existing implementations in `/apps/` and `/frontend/src/`
- Review related documentation in `/docs/`
- Refer to official framework documentation
- Consult team leads for project-specific patterns

For documentation improvements:
- Submit PRs with clear explanations
- Include code examples from the project
- Link to relevant official documentation
- Update this README with new sections
