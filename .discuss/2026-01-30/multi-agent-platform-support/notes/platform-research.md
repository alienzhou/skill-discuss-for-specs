# Platform Research Results

## Platform Capability Matrix (Code-Verified Version)

| Platform | Skills Support | Hooks Support | Config Location | Adaptation Complexity |
|----------|----------------|---------------|-----------------|------------------------|
| **Already Supported** |
| Claude Code | ✅ `~/.claude/skills/` | ✅ PostToolUse/Stop | `settings.json` | - |
| Cursor | ✅ `~/.cursor/skills/` | ✅ afterFileEdit/stop | `hooks.json` | - |
| **P0** |
| Kilocode | ✅ `~/.kilocode/skills/` | ❌ None (code verification) | SKILL.md | ⭐ Low (Skills) |
| OpenCode | ⚠️ Plugin form | ✅ 20+ hooks | `.opencode/` | ⭐⭐ Medium |
| Roo Code | ⚠️ Rules form | ❌ None | `.roo/rules/` | ⭐⭐ Medium |
| Cline | ⚠️ Rules form | ✅ 6 hooks | `.clinerules/` | ⭐⭐ Medium |
| **P1** |
| Trae | ⚠️ Rules form | ❓ Unclear | UI config mostly | ⭐⭐⭐ High |
| Gemini CLI | ⚠️ No Skills | ✅ 8 hooks | `.gemini/` | ⭐⭐ Medium |
| Codex CLI | ✅ Skills + AGENTS.md | ❌ Only notify (code verification) | `~/.codex/` config.toml | ⭐ Low (Skills) |
| Amp | ✅ SDK Skills | ✅ MCP | MCP integration | ⭐⭐ Medium |
| **P2** |
| Windsurf | ⚠️ Rules form | ❌ None | `.windsurfrules` | ⭐⭐⭐ High |
| Qoder CLI | ✅ Agents (.md) | ⚠️ Commands | `.qoder/agents/` | ⭐⭐ Medium |
| CodeBuddy | ⚠️ Config form | ✅ Hooks + MCP | `.codebuddy/` | ⭐⭐ Medium |

### Legend
- ✅ Full support, compatible with current project architecture
- ⚠️ Partial support, requires adaptation/conversion
- ❌ No support, requires fallback solution
- ❓ Unclear documentation, needs further research

### ⚠️ Important Findings
Code analysis shows **Kilocode and Codex CLI both lack Hooks systems!**
- Kilocode: Only has Skills loading, no Hooks implementation
- Codex CLI: Only has `notify` notification mechanism (executes command after each turn), not a real Hook

---

## P0 Platform Detailed Research

### Kilocode (Deep Code Analysis)

**Core File**: `kilocode/src/services/skills/SkillsManager.ts`

**Skills Directory Structure**:
```
~/.kilocode/skills/              # Global common
~/.kilocode/skills-{mode}/       # Global mode-specific (e.g., skills-code)
.kilocode/skills/                # Project-level common
.kilocode/skills-{mode}/         # Project-level mode-specific
```

**Skills Format**:
```yaml
---
name: skill-name          # Required, 1-64 characters
description: "description"  # Required
---
# Markdown body
```

**Naming Convention** (strict):
- Lowercase letters, numbers, hyphens
- Cannot start/end with hyphen
- Cannot have consecutive hyphens
- Must match directory name

**Priority Rules**:
1. Project-level mode-specific > Project-level common > Global mode-specific > Global common

**Special Features**:
- ✅ Supports symbolic links
- ✅ File watching auto-refresh
- ✅ Backward compatible with `.roo` directory
- ❌ **No Hooks system**

### Codex CLI (Deep Code Analysis)

**Core Files**:
- `codex-rs/core/src/skills/loader.rs` - Skills loading
- `codex-rs/core/src/project_doc.rs` - AGENTS.md processing

**Skills Directory Structure**:
```
.codex/skills/           # Project-level (highest priority)
~/.codex/skills/         # User-level
~/.codex/skills/.system/ # System cache
/etc/codex/skills/       # System-level (Unix only)
```

**Skills Format**:
```yaml
---
name: skill-name          # Required, max 64 characters
description: "description"  # Required, max 1024 characters
metadata:
  short-description: "short description"  # Optional
---
# Markdown body
```

**AGENTS.md Processing**:
- Search upward from CWD to Git root
- Collect all AGENTS.md on path, concatenate in order from root to CWD
- Supports AGENTS.override.md (highest priority)
- Max 32 KiB

**Configuration Format**: TOML (`config.toml`)
```toml
model = "gpt-5.1"
notify = ["notify-send", "Codex"]  # Simple notification, not Hooks
project_doc_max_bytes = 32768
```

**Hooks Status**:
- ❌ **No real Hooks system**
- Only has `notify` configuration: executes external command after each turn
- Passes JSON: `{"type":"agent-turn-complete","turn-id":"12345"}`

### OpenCode
- **Config**: `~/.config/opencode/` (global) or `.opencode/` (project)
- **Hooks**: 20+ built-in hooks, TypeScript plugin form (`.opencode/plugin/`)
- **Features**: Layered configuration merge, supports remote configuration
- **Challenge**: Need to wrap Python hooks into TypeScript or call directly

### Roo Code
- **Rules**: `~/.roo/rules/` (global) or `.roo/rules/` (workspace)
- **Features**: Supports mode-specific rules (rules-{modeSlug})
- **Challenge**: No Hooks system, only Skill-level support possible

### Cline
- **Hooks**: 6 types - PreToolUse, PostToolUse, UserPromptSubmit, TaskStart, TaskResume, TaskCancel
- **Location**: `~/Documents/Cline/Rules/Hooks/` or `.clinerules/hooks/`
- **Communication**: JSON stdin/stdout
- **Limitations**: macOS/Linux only

---

## P1 Platform Detailed Research

### Trae IDE
- **Rules**: Supports Trae Rules, mainly through UI configuration
- **Challenge**: Lacks technical documentation, may require reverse engineering

### Gemini CLI
- **Hooks**: 8 events - SessionStart, BeforeAgent, AfterAgent, BeforeModel, AfterModel, BeforeToolSelection, BeforeTool, AfterTool
- **Configuration**: `~/.gemini/settings.json` or `.gemini/settings.json`
- **Communication**: JSON stdin/stdout, strict "Golden Rule" (only output JSON)

### Codex CLI (OpenAI)
- **Already analyzed in detail in P0 section**
- Skills format compatible, AGENTS.md processing complete
- Configuration uses TOML format
- No Hooks, only simple notify mechanism

### Amp (Sourcegraph)
- **SDK**: TypeScript SDK approach
- **MCP**: Full MCP integration
- **Skills**: Supports custom skills

---

## P2 Platform Detailed Research

### Windsurf
- **Rules**: `global_rules.md`, `.windsurfrules`, `.windsurf/context.md`
- **Limitations**: 6000 character limit
- **Challenge**: No Hooks, Flow-based architecture differs significantly

### Qoder CLI
- **Agents**: `~/.qoder/agents/` or `.qoder/agents/`, defined in .md files
- **Features**: Subagents system, supports frontmatter configuration

### CodeBuddy CLI
- **Config**: `~/.codebuddy/settings.json`
- **Hooks**: Supports pre/post-execution hooks
- **MCP**: Full MCP support
