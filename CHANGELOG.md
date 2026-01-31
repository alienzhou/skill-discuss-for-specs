# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-01

### Added

- **Multi-platform L1 support** - Added installation support for Kilocode, OpenCode, and Codex CLI platforms
  - L1 platforms support skill installation only (no hooks/auto-tracking)
  - L2 platforms (Claude Code, Cursor) retain full functionality with hooks support

### Changed

- **Snapshot-based detection** - Replaced session-based tracking with snapshot-based detection mechanism
  - Removed `session_manager.py`, added `snapshot_manager.py`
  - Discussion state changes are now tracked via `.discuss/.snapshot.yaml`
  - Simplified `check_precipitation.py` logic

- **Unified installation entry** - Consolidated platform-specific installation scripts into a single entry point
  - Removed separate `platforms/*/install.sh` scripts
  - All platform installations are now handled through the npm package

### Removed

- **curl-based installation** - Removed curl installation method in favor of npm-only installation
  - Deleted standalone `install.sh` script
  - Updated all documentation to reflect npm-only installation

### Documentation

- Finalized multi-agent platform support discussion and decisions
- Updated documentation for snapshot-based architecture

## [0.1.0] - 2026-01-29

### Added

- Initial release of `@vibe-x/discuss-for-specs` npm package
- **Discussion facilitation system** with structured templates
- **Hooks system** for automatic precipitation detection
  - Stop hook for checking pending decisions
  - File edit tracking
- **Multi-platform support**
  - Claude Code (L2 - full support)
  - Cursor (L2 - full support)
- **CLI tool** with beautiful output (colors, spinners)
  - `discuss-for-specs install` - Install skill and hooks
  - `discuss-for-specs uninstall` - Remove skill and hooks
  - `discuss-for-specs status` - Check installation status
- **Skill templates** for structured discussions
  - State-priority format for decision tracking
  - Outline, decisions, and notes organization
- Cross-platform distribution architecture
- Comprehensive test suite

[0.2.0]: https://github.com/vibe-x-ai/skill-discuss-for-specs/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vibe-x-ai/skill-discuss-for-specs/releases/tag/v0.1.0
