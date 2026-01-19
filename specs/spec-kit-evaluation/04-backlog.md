# Backlog: Cross-Platform Skills Distribution

> **Created**: 2026-01-19  
> **Purpose**: Items not included in current version (v0.1.0)

---

## Feature Backlog

Items that could be implemented in future versions:

| ID | Feature | Priority | Reason for Deferral |
|----|---------|----------|---------------------|
| F1 | Slash Command support | Medium | D1 decided to focus on Skills first; can be added later |
| F2 | Uninstall command | Low | Can be done manually; not critical for MVP |
| F3 | Update command | Medium | Version checking adds complexity; defer to later |
| F4 | Interactive platform selection | Low | Nice to have, but flag-based works well |
| F5 | Skill selection (install specific skills) | Medium | For now, install all skills together |
| F6 | TypeScript implementation | Medium | Plain JS works; can migrate later if needed |

---

## Technical Optimization Backlog

Future technical improvements:

| ID | Optimization | Priority | Notes |
|----|--------------|----------|-------|
| O1 | Zero-dependency implementation | Medium | Remove `commander` dependency, use native arg parsing |
| O2 | Add unit tests | High | Important for maintenance, but not blocking initial release |
| O3 | Add CI/CD pipeline | Medium | Automate testing and publishing |
| O4 | Support global installation | Low | User-level Skills installation |
| O5 | Add progress indicators | Low | Visual feedback for long operations |

---

## Open Questions

Long-term questions to research or discuss:

| ID | Question | Context |
|----|----------|---------|
| Q1 | Should we support Rules distribution alongside Skills? | Some platforms have distinct Rules mechanisms |
| Q2 | How to handle platform version differences? | e.g., Cursor Beta vs Stable |
| Q3 | Should Skills be bundled into a single file or kept modular? | Trade-off between simplicity and flexibility |
| Q4 | How to handle Skill updates for existing installations? | Need migration/update strategy |
| Q5 | Should we add telemetry for usage analytics? | Helpful for understanding adoption, but privacy concerns |

---

## Platform-Specific Backlog

Deferred platform-specific features:

### Cursor
- [ ] Add `globs` support for file-specific activation
- [ ] Test with Cursor Stable (currently targeting Nightly)

### Gemini CLI
- [ ] Create post-install script to remind users to enable Skills
- [ ] Explore auto-enable possibility

### All Platforms
- [ ] Create platform-specific README files
- [ ] Add troubleshooting guides per platform

---

## References

- [Discussion: D1 - Skill as primary format](./02-architecture-design.md#d1-skill-as-primary-distribution-format)
- [Task List](./04-task-list.md)

---

**Last Updated**: 2026-01-19
