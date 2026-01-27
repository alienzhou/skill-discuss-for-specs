# Verification Guide

This document provides end-to-end test scenarios to verify that `discuss-skills` is correctly installed and functioning.

---

## Prerequisites

Before running verification tests:

```bash
# Check Node.js version (>= 16.0.0)
node --version

# Check Python 3 environment
python3 --version

# Check PyYAML
python3 -c "import yaml" && echo "PyYAML OK"
```

---

## Scenario 1: Installation Verification

**Objective**: Verify that the installation completes correctly.

### Steps

```bash
# 1. Install (specify your platform)
discuss-skills install --platform claude-code
# or: discuss-skills install --platform cursor

# 2. Verify Skills installation
ls -la ~/.claude/skills/
# Expected: discuss-coordinator/ and discuss-output/ directories exist

# 3. Verify Hooks installation
ls -la ~/.discuss-for-specs/hooks/
# Expected: file-edit/, stop/, common/ directories exist

# 4. Verify Logs directory
ls -la ~/.discuss-for-specs/logs/
# Expected: directory exists (may be empty)

# 5. Verify platform configuration
cat ~/.claude/settings.json | grep -A10 "hooks"
# Expected: PostToolUse and Stop hooks configured
```

### Expected Output

Installation should display:
```
✅ Installation complete!

Installed components:
  • Skills: /Users/<username>/.claude/skills
  • Hooks: /Users/<username>/.discuss-for-specs/hooks
  • Logs: /Users/<username>/.discuss-for-specs/logs
```

---

## Scenario 2: Create Test Discussion Directory

**Objective**: Set up a test discussion structure for hook testing.

### Steps

```bash
# 1. Create test project
mkdir -p ~/test-discuss-project
cd ~/test-discuss-project

# 2. Create discussion directory structure
mkdir -p discuss/2026-01-27/test-topic

# 3. Create meta.yaml
cat > discuss/2026-01-27/test-topic/meta.yaml << 'EOF'
created_at: "2026-01-27T23:00:00+08:00"
current_run: 0
config:
  suggest_update_runs: 3
  force_update_runs: 10
file_status:
  outline:
    last_modified_run: 0
    pending_update: false
  decisions:
    last_modified_run: 0
    pending_update: false
EOF

# 4. Create outline.md
cat > discuss/2026-01-27/test-topic/outline.md << 'EOF'
# Discussion: Test Topic

## 🔵 Current Focus
- Testing the hook system

## ⚪ Pending
- [ ] Q1: Does hook detect file edits?

## ✅ Confirmed
(None yet)
EOF

# 5. Verify structure
tree discuss/
# Or: find discuss/ -type f
```

### Expected Structure

```
discuss/
└── 2026-01-27/
    └── test-topic/
        ├── meta.yaml
        └── outline.md
```

---

## Scenario 3: File Edit Tracking Hook

**Objective**: Verify that `track_file_edit` hook correctly tracks file modifications.

### Steps

```bash
cd ~/test-discuss-project

# 1. Simulate AI editing outline.md (manual hook invocation)
echo '{"file_path": "'$(pwd)'/discuss/2026-01-27/test-topic/outline.md"}' | \
  python3 ~/.discuss-for-specs/hooks/file-edit/track_file_edit.py

# 2. Verify meta.yaml was updated
cat discuss/2026-01-27/test-topic/meta.yaml
```

### Expected Result

`meta.yaml` should show:
```yaml
file_status:
  outline:
    last_modified_run: 0
    pending_update: true   # <-- Changed from false to true
```

### Log Verification

```bash
# View today's log
cat ~/.discuss-for-specs/logs/discuss-hooks-$(date +%Y-%m-%d).log

# Expected log entries:
# Hook Started: track_file_edit
# [EDIT] .../outline.md - File edit detected
# Discussion detected: .../test-topic (file_type: outline)
# Meta updated: .../test-topic
# Hook Ended: track_file_edit [SUCCESS]
```

---

## Scenario 4: Round Counting (Stop Hook)

**Objective**: Verify that `check_precipitation` hook updates round count and clears pending updates.

### Steps

```bash
cd ~/test-discuss-project

# 1. Ensure meta.yaml has pending_update: true (from Scenario 3)

# 2. Invoke stop hook
echo '{"status": "completed"}' | \
  python3 ~/.discuss-for-specs/hooks/stop/check_precipitation.py

# 3. Verify meta.yaml was updated
cat discuss/2026-01-27/test-topic/meta.yaml
```

### Expected Result

`meta.yaml` should show:
```yaml
current_run: 1                    # <-- Incremented from 0 to 1
file_status:
  outline:
    last_modified_run: 1          # <-- Updated to match current_run
    pending_update: false         # <-- Cleared back to false
```

### Log Verification

```bash
cat ~/.discuss-for-specs/logs/discuss-hooks-$(date +%Y-%m-%d).log | tail -20

# Expected log entries:
# Hook Started: check_precipitation
# Found pending updates in .../test-topic: ['outline']
# Meta updated: .../test-topic
#   current_run: 0 -> 1
#   cleared_pending: ['outline']
# Modified discussions: 1
# Hook Ended: check_precipitation [SUCCESS]
```

---

## Scenario 5: Stale Detection Trigger

**Objective**: Verify that stale reminders are triggered when files are not updated for several rounds.

### Steps

```bash
cd ~/test-discuss-project

# 1. Modify meta.yaml to simulate stale state (4 rounds without outline update)
cat > discuss/2026-01-27/test-topic/meta.yaml << 'EOF'
created_at: "2026-01-27T23:00:00+08:00"
current_run: 5
config:
  suggest_update_runs: 3
  force_update_runs: 10
file_status:
  outline:
    last_modified_run: 1    # 4 rounds stale (5-1=4 > 3)
    pending_update: false
  decisions:
    last_modified_run: 5
    pending_update: false
EOF

# 2. Invoke stop hook
echo '{"status": "completed"}' | \
  python3 ~/.discuss-for-specs/hooks/stop/check_precipitation.py

# 3. Observe output - should include stale reminder
```

### Expected Output

The hook should output a JSON with a stale reminder message (the exact format depends on the platform).

### Log Verification

```bash
grep -A5 "Stale items found" ~/.discuss-for-specs/logs/discuss-hooks-$(date +%Y-%m-%d).log

# Expected:
# [SUGGEST] outline: 4 runs stale
```

---

## Scenario 6: Uninstall Verification

**Objective**: Verify that uninstallation removes all components except logs.

### Steps

```bash
# 1. Run uninstall
discuss-skills uninstall --platform claude-code

# 2. Verify Skills removed
ls ~/.claude/skills/discuss-*
# Expected: "No such file or directory"

# 3. Verify Hooks removed
ls ~/.discuss-for-specs/hooks/
# Expected: directory does not exist or is empty

# 4. Verify platform config cleaned
cat ~/.claude/settings.json | grep discuss-for-specs
# Expected: no matches

# 5. Verify Logs preserved
ls ~/.discuss-for-specs/logs/
# Expected: directory still exists with log files
```

### Expected Output

```
✅ Uninstallation complete!

Note: Logs directory was preserved: ~/.discuss-for-specs/logs/
      Delete it manually if you want to remove all data.
```

---

## Log Observation Guide

### Log Location

```bash
~/.discuss-for-specs/logs/discuss-hooks-YYYY-MM-DD.log
```

### Log Levels

| Level | Usage |
|-------|-------|
| `INFO` | Key operations: hook start/end, discussion detection, meta updates |
| `DEBUG` | Details: input data, file operations, path resolution |
| `WARNING` | Attention needed: stale detection, blocking triggers |
| `ERROR` | Exceptions: parse failures, IO errors |

### Real-time Monitoring

```bash
# Watch logs in real-time
tail -f ~/.discuss-for-specs/logs/discuss-hooks-$(date +%Y-%m-%d).log

# Filter by hook name
tail -f ~/.discuss-for-specs/logs/discuss-hooks-*.log | grep "track_file_edit"

# Show only warnings and errors
grep -E "WARNING|ERROR" ~/.discuss-for-specs/logs/discuss-hooks-*.log
```

### Example Log Output

```
============================================================
2026-01-27 23:30:00 | INFO     | discuss-hooks | Hook Started: track_file_edit
2026-01-27 23:30:00 | INFO     | discuss-hooks | Working Directory: /Users/user/project
2026-01-27 23:30:00 | DEBUG    | discuss-hooks | Input Data: {"file_path": ".../outline.md"}
2026-01-27 23:30:00 | DEBUG    | discuss-hooks | [EDIT] .../outline.md - File edit detected
2026-01-27 23:30:00 | INFO     | discuss-hooks | Discussion detected: .../test-topic (file_type: outline)
2026-01-27 23:30:00 | INFO     | discuss-hooks | Meta updated: .../test-topic
2026-01-27 23:30:00 | DEBUG    | discuss-hooks |   outline.pending_update: True
2026-01-27 23:30:00 | INFO     | discuss-hooks | Hook Ended: track_file_edit [SUCCESS]
============================================================
```

---

## Troubleshooting

### Hook Not Triggering

1. Check platform configuration:
   ```bash
   cat ~/.claude/settings.json | grep -A20 "hooks"
   # or for Cursor:
   cat ~/.cursor/hooks.json
   ```

2. Verify Python path in hooks config points to correct location

3. Check if hooks directory exists:
   ```bash
   ls ~/.discuss-for-specs/hooks/
   ```

### Discussion Not Detected

1. Ensure directory contains `meta.yaml`:
   ```bash
   find . -name "meta.yaml"
   ```

2. Verify working directory when hook is called

### No Logs Generated

1. Check logs directory permissions:
   ```bash
   ls -la ~/.discuss-for-specs/logs/
   ```

2. Manually run hook to check for errors:
   ```bash
   echo '{"file_path": "/test/path"}' | python3 ~/.discuss-for-specs/hooks/file-edit/track_file_edit.py
   ```

---

## Verification Checklist

- [ ] Python 3 + PyYAML environment OK
- [ ] `discuss-skills install` completes successfully
- [ ] Skills directories created correctly
- [ ] Hooks directories created correctly
- [ ] Platform config file updated correctly
- [ ] Logs directory is writable
- [ ] `track_file_edit` hook tracks file modifications
- [ ] `check_precipitation` hook updates round count
- [ ] Stale reminder triggers at threshold
- [ ] Uninstall cleans up correctly

---

## Clean Up

After verification, clean up test resources:

```bash
# Remove test project
rm -rf ~/test-discuss-project

# (Optional) Remove all discuss-for-specs data
rm -rf ~/.discuss-for-specs
```

---

**Last Updated**: 2026-01-27
