# Multi-Agent Platform Support Extension

## 🔵 Current Focus
- Snapshot scheme implementation
- Initial batch of supported platforms determination

## ⚪ Pending
- Implement snapshot_manager.py
- Rewrite check_precipitation.py
- Update SKILL.md
- Update npm-package
- L1 platform adaptation (Kilocode, Codex)

## ✅ Confirmed

| ID | Decision | Document |
|----|----------|----------|
| D01 | Replace original dual-hook scheme with snapshot scheme | [D01-snapshot-based-detection.md](decisions/D01-snapshot-based-detection.md) |
| D02 | Remove meta.yaml, merge configuration into snapshot.yaml | [D02-remove-meta-yaml.md](decisions/D02-remove-meta-yaml.md) |
| D03 | Simplify levels to L1 and L2 | [D03-two-level-architecture.md](decisions/D03-two-level-architecture.md) |
| D04 | Snapshot scheme design parameters (24h/mtime/full tracking) | [D04-snapshot-parameters.md](decisions/D04-snapshot-parameters.md) |
| D05 | L1 platform Skill guidance design (two-layer separation) | [D05-l1-skill-guidance.md](decisions/D05-l1-skill-guidance.md) |

## ❌ Rejected
(Nothing yet)

---

## Overview

### Background
Extend support to more AI Agent platforms:
- **P0**: Kilocode, OpenCode, Roo Code, Cline
- **P1**: Trae, Gemini CLI, Codex CLI, Amp
- **P2**: Windsurf, Qoder CLI, CodeBuddy CLI

### Core Findings
Code analysis shows many platforms lack complete Hooks systems, requiring tiered support.

### Final Solution: Two-Level Architecture

| Level | Capability | Required Hooks | Applicable Platforms |
|-------|------------|----------------|----------------------|
| **L1** | Discussion facilitation | None | Kilocode, Codex, Roo Code, Windsurf, Trae |
| **L2** | + Snapshot detection + Auto reminder | Stop only | Claude Code, Cursor, Cline, Gemini CLI, OpenCode, CodeBuddy |

### Snapshot Scheme Core Logic
- Each Stop Hook compares against `.discuss/.snapshot.yaml`
- Detect outline mtime change → `change_count++`
- Detect decisions/notes change → `change_count = 0` (reset)
- Trigger reminder when `change_count >= threshold`

---

## Reference Materials

| Type | File |
|------|------|
| Platform research | [notes/platform-research.md](notes/platform-research.md) |
