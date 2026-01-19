# Architecture Design: Cross-Platform Skills Distribution

> **Created**: 2026-01-19  
> **Status**: Confirmed  
> **Discussion Source**: [spec-kit-evaluation discussion](../discuss/2026-01-19/spec-kit-evaluation/)

---

## 1. Design Overview

### 1.1 Design Goals

1. **Cross-Platform Consistency**: Single source of Skill content, deployable to multiple platforms
2. **Maintainability**: Adding new platforms should only require configuration changes
3. **Good User Experience**: One-command installation
4. **Extensibility**: Preserve space for platform-specific customizations

### 1.2 Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Config Layer                             │
│               config/platforms.yaml                          │
│         (Platform definitions, directories, headers)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Template Layer                            │
│                  skills/<name>/                              │
│     ├── SKILL.md (common content)                           │
│     └── headers/<platform>.yaml (platform headers)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Build Layer                              │
│              npm package: discuss-skills                     │
│    (CLI commands: install, platforms, version)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decisions

### D1: Skill as Primary Distribution Format

**Decision Time**: R2  
**Status**: ✅ Confirmed

#### Background

Need to determine the format for distributing discussion capabilities (`discuss-coordinator`, `discuss-output`) across different AI products.

#### Options Considered

| Option | Description | Pros | Cons | Decision |
|--------|-------------|------|------|----------|
| Skill | Capability extensions based on SKILL.md | All mainstream platforms support; auto triggering; high standardization | Cursor still in Beta | ✅ |
| Slash Command | User explicitly triggers with `/xxx` | Clear user control | Large format differences (Markdown vs TOML); requires more adaptation | ❌ |
| Rules | Rule files auto-load | Simple | Not suitable for complex capabilities; different platform formats | ❌ |

#### Final Decision

Use **Skill** as the primary distribution format. Other formats (like Slash Commands) can be secondary, deferred for later implementation.

#### Rationale

1. **Broad Platform Support**: Claude Code, Cursor, GitHub Copilot, Windsurf, and Gemini CLI all support Skills
2. **Unified Format**: All platforms use `SKILL.md` + YAML frontmatter
3. **Automatic Triggering**: Better user experience, no need to remember commands
4. **Extensible**: Slash Command support can be added in the future

---

### D2: Preserve Header Separation Design

**Decision Time**: R3  
**Status**: ✅ Confirmed

#### Background

The current project has a `skills/<name>/headers/<platform>.yaml` design that separates YAML frontmatter from Skill content. Need to decide whether to keep this design.

#### Options Considered

| Option | Description | Pros | Cons | Decision |
|--------|-------------|------|------|----------|
| Separated | `headers/<platform>.yaml` + `SKILL.md` | Reserves space for platform differences; flexible combination during build | Slightly more files | ✅ |
| Merged | Single `SKILL.md` including frontmatter | Simple and intuitive | Refactoring needed when platform differences exist | ❌ |

#### Final Decision

Preserve the `skills/<name>/headers/<platform>.yaml` separated design.

#### Rationale

1. **Platform Differences Exist**: Claude Code supports `allowed-tools`, Cursor supports `alwaysApply` and `globs`
2. **Build-time Concatenation**: `headers/<platform>.yaml` + `SKILL.md` → complete file
3. **Good Extensibility**: Adding a new platform only requires adding the corresponding header file

#### Expected Structure

```
skills/
├── discuss-coordinator/
│   ├── SKILL.md
│   └── headers/
│       ├── claude-code.yaml
│       ├── cursor.yaml
│       ├── github-copilot.yaml
│       ├── windsurf.yaml
│       └── gemini.yaml
└── discuss-output/
    └── (same structure)
```

---

### D3: Adopt Centralized Configuration Management

**Decision Time**: R5  
**Status**: ✅ Confirmed

#### Background

Need to manage configuration information for multiple platforms (directory conventions, header file names, etc.). Decide between centralized configuration or platform-specific hardcoding.

#### Options Considered

| Option | Description | Pros | Cons | Decision |
|--------|-------------|------|------|----------|
| Centralized Config | `config/platforms.yaml` | Single source of truth; simple to add platforms; generalized build scripts | Need to parse configuration | ✅ |
| Hardcoded | Independent `build.sh` per platform | Simple and direct | Lots of duplicate code; troublesome to add new platforms | ❌ |

#### Final Decision

Create `config/platforms.yaml` to centrally manage platform information.

#### Rationale

1. **Adopt Proven Solution**: spec-kit's `AGENT_CONFIG` pattern is well-tested
2. **Maintainability**: Adding a new platform only requires adding one configuration entry
3. **Generalized Build Scripts**: One script handles all platforms

#### Expected Configuration

```yaml
# config/platforms.yaml
platforms:
  claude-code:
    name: "Claude Code"
    skills_dir: ".claude/skills"
    header_file: "claude-code.yaml"
    status: "stable"

  cursor:
    name: "Cursor"
    skills_dir: ".cursor/skills"
    header_file: "cursor.yaml"
    status: "beta"
    note: "Skills feature may require Nightly version"

  github-copilot:
    name: "GitHub Copilot"
    skills_dir: ".github/skills"
    header_file: "github-copilot.yaml"
    status: "stable"

  windsurf:
    name: "Windsurf"
    skills_dir: ".windsurf/skills"
    header_file: "windsurf.yaml"
    status: "stable"

  gemini:
    name: "Gemini CLI"
    skills_dir: ".gemini/skills"
    header_file: "gemini.yaml"
    status: "needs-enable"
    note: "Need to run `gemini skills enable <name>` to enable"
```

---

### D4: Distribute Installation Commands via npm

**Decision Time**: R5  
**Status**: ✅ Confirmed

#### Background

Users need to install Skills into their projects. Need to determine the distribution and installation method.

#### Options Considered

| Option | Description | Pros | Cons | Decision |
|--------|-------------|------|------|----------|
| npm package | `npx discuss-skills install` | Standardized; no download needed; good version management | Requires Node.js environment | ✅ |
| Installation script | `./install.sh --platform cursor` | Simple | Need to download script first | ❌ |
| Manual copy | Users manually copy files | Simplest | Poor experience; error-prone | ❌ |
| Git clone | Run build after `git clone` | Good version control | Users need to understand build process | ❌ |

#### Final Decision

Publish `discuss-skills` package via npm, providing bin commands.

#### Rationale

1. **User Experience**: `npx discuss-skills install` - done with one command
2. **Version Management**: npm has built-in version management
3. **No Pre-download**: `npx` runs directly
4. **Industry Standard**: Like `create-react-app`, `specify`, etc.

#### Expected Commands

```bash
# Install to current project
npx discuss-skills install --platform cursor

# Install to specific directory
npx discuss-skills install --platform claude-code --target ~/my-project

# View supported platforms
npx discuss-skills platforms

# View version
npx discuss-skills --version
```

---

### D5: npm Package Design

**Decision Time**: R6  
**Status**: ✅ Confirmed

#### Background

Determine the specific design of the npm package: package name, implementation language, dependency strategy.

#### Options Considered

**Package Name Selection**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| `discuss-skills` | Descriptive; easy to remember | Slightly longer | ✅ |
| `skill-discuss` | Consistent with project name | Less intuitive | ❌ |
| `dskill` | Short | Meaning unclear | ❌ |

**Implementation Language**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Node.js | Native to npm; good ecosystem; large user base | Requires Node environment | ✅ |
| Python | Already has pyproject.toml | Needs pipx; not as widespread as npm | ❌ |

#### Final Decision

- **Package Name**: `discuss-skills`
- **Language**: Node.js (TypeScript optional)
- **Dependencies**: Minimized, may only need `commander` or native parsing

#### Expected package.json

```json
{
  "name": "discuss-skills",
  "bin": {
    "discuss-skills": "./bin/cli.js"
  },
  "dependencies": {
    // Minimal or no dependencies
  }
}
```

---

### D6: Pre-built Content in npm Package

**Decision Time**: R7  
**Status**: ✅ Confirmed

#### Background

The npm package needs to include the Skill files. Decide whether to include source files and build at install time, or include pre-built files ready for direct copy.

#### Options Considered

| Option | Description | Pros | Cons | Decision |
|--------|-------------|------|------|----------|
| Pre-built | Include complete SKILL.md files (header + content) for each platform | Fast installation; no build step; no external dependencies needed at runtime | Larger package size; need to rebuild when source changes | ✅ |
| Build at install | Include source files, concatenate header + content during `install` command | Smaller package; always uses latest structure | Slower installation; more complex logic; potential for build errors | ❌ |

#### Final Decision

Include **pre-built content** in the npm package. The package will contain complete `SKILL.md` files for each platform, generated during the package build/publish process.

#### Rationale

1. **Fast Installation**: Users just copy files, no concatenation needed at runtime
2. **No Runtime Dependencies**: Installation logic is simple file copy
3. **Reliability**: Pre-built files are tested before publish, reducing installation errors
4. **Offline Friendly**: All content is already in the package, no network requests needed

#### Expected Package Structure

```
discuss-skills/
├── bin/
│   └── cli.js
├── dist/                          # Pre-built files
│   ├── claude-code/
│   │   ├── discuss-coordinator/
│   │   │   └── SKILL.md          # Complete file (header + content)
│   │   └── discuss-output/
│   │       └── SKILL.md
│   ├── cursor/
│   │   └── ...
│   ├── github-copilot/
│   │   └── ...
│   ├── windsurf/
│   │   └── ...
│   └── gemini/
│       └── ...
├── config/
│   └── platforms.yaml
└── package.json
```

#### Build Process

During package build (before `npm publish`):

```bash
# Build script concatenates headers + content for each platform
node scripts/build.js

# Output: dist/<platform>/<skill>/SKILL.md
```

#### Install Logic (Simplified)

```javascript
// Installation is now simple file copy
async function install(platform, targetDir) {
  const sourceDir = path.join(__dirname, '../dist', platform);
  const targetSkillsDir = path.join(targetDir, platformConfig.skills_dir);
  
  // Just copy the pre-built files
  copyDirectory(sourceDir, targetSkillsDir);
}
```

---

## 3. Platform Header Templates

### 3.1 Claude Code (`headers/claude-code.yaml`)

```yaml
---
name: discuss-coordinator
description: "Discussion mode coordinator managing output strategy, problem tracking, and precipitation rules. Use when user requests discussion mode or wants to track decisions."
---
```

**Notes**:
- `description` must be single line, cannot use YAML multi-line syntax
- Recommended to clearly state "when to use" (Use when...)

### 3.2 Cursor (`headers/cursor.yaml`)

```yaml
---
name: discuss-coordinator
description: "Discussion mode coordinator managing output strategy, problem tracking, and precipitation rules. Use when user requests discussion mode or wants to track decisions."
alwaysApply: false
---
```

**Notes**:
- `alwaysApply: false` means Agent decides based on context
- Can add `globs` to limit application scope

### 3.3 Other Platforms

Similar structure, with platform-specific fields as needed. The common fields (`name`, `description`) remain consistent across all platforms.

---

## 4. Compatibility Considerations

### 4.1 Unknown Field Handling

- **Claude Code** will ignore unrecognized fields (like `alwaysApply`)
- **Cursor** will ignore unrecognized fields (like `allowed-tools`)

This means merging fields is technically possible, but for clarity, maintaining separate headers is recommended.

### 4.2 Feature Status

| Platform | Skills Feature | Stability |
|----------|----------------|-----------|
| Claude Code | ✅ Fully available | Stable |
| Cursor | ⚠️ May require Nightly | Beta |
| GitHub Copilot | ✅ Fully available | Stable |
| Windsurf | ✅ Fully available | Stable |
| Gemini CLI | ⚠️ Needs manual enable | Stable (once enabled) |

---

## 5. References

- [Technical Research](./01-technical-research.md)
- [spec-kit Project](https://github.com/spec-kit/spec-kit)
- [Discussion Records](../discuss/2026-01-19/spec-kit-evaluation/)

---

**Last Updated**: 2026-01-19
