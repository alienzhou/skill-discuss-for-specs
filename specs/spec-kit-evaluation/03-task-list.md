# Task List: Cross-Platform Skills Distribution Implementation

> **Created**: 2026-01-19  
> **Status**: Ready for development

---

## Development Tasks

### Phase 1: Configuration Setup

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| T1.1 | Create `config/platforms.yaml` | P0 | 🔴 TODO | Define all 5 platforms |
| T1.2 | Add header files for Cursor | P0 | 🔴 TODO | `skills/*/headers/cursor.yaml` |
| T1.3 | Add header files for GitHub Copilot | P1 | 🔴 TODO | `skills/*/headers/github-copilot.yaml` |
| T1.4 | Add header files for Windsurf | P1 | 🔴 TODO | `skills/*/headers/windsurf.yaml` |
| T1.5 | Add header files for Gemini | P1 | 🔴 TODO | `skills/*/headers/gemini.yaml` |

### Phase 2: Build System (D6)

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| T2.1 | Create build script (`scripts/build.js`) | P0 | 🔴 TODO | Concatenate headers + content → `dist/` |
| T2.2 | Generate `dist/<platform>/<skill>/SKILL.md` | P0 | 🔴 TODO | Pre-built files for all platforms |
| T2.3 | Add build to prepublish hook | P1 | 🔴 TODO | Auto-build before npm publish |

### Phase 3: npm Package Implementation

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| T3.1 | Create npm package directory structure | P0 | 🔴 TODO | `npm/` directory |
| T3.2 | Implement `package.json` | P0 | 🔴 TODO | Package metadata, bin config, files list |
| T3.3 | Implement CLI entry point (`bin/cli.js`) | P0 | 🔴 TODO | Use commander or native args |
| T3.4 | Implement `install` command | P0 | 🔴 TODO | Copy pre-built files from `dist/` |
| T3.5 | Implement `platforms` command | P1 | 🔴 TODO | List supported platforms |
| T3.6 | Add error handling and validation | P1 | 🔴 TODO | User-friendly error messages |

### Phase 4: Testing

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| T4.1 | Test build script | P0 | 🔴 TODO | Verify `dist/` output is correct |
| T4.2 | Local testing with `npm link` | P0 | 🔴 TODO | Verify all commands work |
| T4.3 | Test installation for each platform | P0 | 🔴 TODO | Verify correct file copy |
| T4.4 | Test `npx` execution | P1 | 🔴 TODO | Verify works without prior install |

### Phase 5: Documentation & Release

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| T5.1 | Update project README | P1 | 🔴 TODO | Add installation instructions |
| T5.2 | Create CHANGELOG | P2 | 🔴 TODO | Initial release notes |
| T5.3 | Publish to npm | P1 | 🔴 TODO | Initial release v0.1.0 |

---

## Temporary Todos

Items that need attention but aren't development tasks:

| Item | Description | Status |
|------|-------------|--------|
| npm package name availability | Verify `discuss-skills` is available on npm | 🔴 TODO |
| Claude Code header verification | Verify existing header file format is correct | 🔴 TODO |

---

## Task Dependencies

```
Phase 1 (Config)          Phase 2 (Build)         Phase 3 (npm)           Phase 4 (Test)
─────────────────────────────────────────────────────────────────────────────────────────

T1.1 ─┬─────────────────► T2.1 ─► T2.2 ─────────► T3.1 ─► T3.2 ─► T3.3 ─► T4.1
      │                     │                       │
T1.2 ─┤                     │                       ├─► T3.4 ─► T4.2 ─► T4.3
      │                     │                       │
T1.3 ─┤                     └─► T2.3                ├─► T3.5
      │                                             │
T1.4 ─┤                                             └─► T3.6
      │
T1.5 ─┘

T4.3 ─► T4.4 ─► T5.1 ─► T5.3
```

---

## Priority Legend

- **P0**: Critical, must complete for MVP
- **P1**: Important, should complete for initial release
- **P2**: Nice to have, can defer if needed

## Status Legend

- 🔴 TODO: Not started
- 🟡 In Progress: Currently working on
- 🟢 Done: Completed
- ⏸️ Blocked: Waiting on dependency

---

**Last Updated**: 2026-01-19
