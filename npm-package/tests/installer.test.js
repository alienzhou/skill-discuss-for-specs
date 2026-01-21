/**
 * Tests for src/installer.js
 * kwaipilot-fix: TEST-Issue-002/tpextid6foog2fsp6iq4
 */

import { test, describe, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { existsSync, mkdirSync, rmSync, writeFileSync, readFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

import {
  listPlatforms,
} from '../src/installer.js';

import {
  copyDirectory,
  ensureDirectory,
  removeDirectory,
} from '../src/utils.js';


describe('listPlatforms', () => {
  test('does not throw', () => {
    // listPlatforms just outputs to console, so we check it doesn't throw
    assert.doesNotThrow(() => {
      // Capture console output
      const originalLog = console.log;
      const logs = [];
      console.log = (...args) => logs.push(args.join(' '));
      
      try {
        listPlatforms();
      } finally {
        console.log = originalLog;
      }
      
      // Should have logged something
      assert.ok(logs.length > 0);
    });
  });

  test('outputs platform information', () => {
    const originalLog = console.log;
    const logs = [];
    console.log = (...args) => logs.push(args.join(' '));
    
    try {
      listPlatforms();
    } finally {
      console.log = originalLog;
    }
    
    const output = logs.join('\n');
    assert.ok(output.includes('Claude Code') || output.includes('claude-code'));
    assert.ok(output.includes('Cursor') || output.includes('cursor'));
  });
});


describe('install function', () => {
  test('module exports install function', async () => {
    const { install } = await import('../src/installer.js');
    assert.strictEqual(typeof install, 'function');
  });
});


describe('uninstall function', () => {
  test('module exports uninstall function', async () => {
    const { uninstall } = await import('../src/installer.js');
    assert.strictEqual(typeof uninstall, 'function');
  });
});


describe('Installation utilities integration', () => {
  let testDir;

  beforeEach(() => {
    testDir = join(tmpdir(), `test-installer-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    if (existsSync(testDir)) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  test('copyDirectory copies files correctly', () => {
    // Setup source directory with files
    const srcDir = join(testDir, 'src');
    const destDir = join(testDir, 'dest');
    
    mkdirSync(srcDir);
    writeFileSync(join(srcDir, 'config.json'), '{"key": "value"}');
    mkdirSync(join(srcDir, 'subdir'));
    writeFileSync(join(srcDir, 'subdir', 'nested.txt'), 'nested content');
    
    // Copy
    copyDirectory(srcDir, destDir);
    
    // Verify
    assert.strictEqual(existsSync(join(destDir, 'config.json')), true, 'config.json should be copied');
    assert.strictEqual(existsSync(join(destDir, 'subdir', 'nested.txt')), true, 'nested.txt should be copied');
    
    const content = readFileSync(join(destDir, 'config.json'), 'utf-8');
    assert.strictEqual(content, '{"key": "value"}', 'File content should match');
  });

  test('copyDirectory with overwrite option', () => {
    const srcDir = join(testDir, 'src');
    const destDir = join(testDir, 'dest');
    
    // Create source
    mkdirSync(srcDir);
    writeFileSync(join(srcDir, 'file.txt'), 'new content');
    
    // Create destination with existing file
    mkdirSync(destDir);
    writeFileSync(join(destDir, 'file.txt'), 'old content');
    
    // Copy with overwrite
    copyDirectory(srcDir, destDir, { overwrite: true });
    
    const content = readFileSync(join(destDir, 'file.txt'), 'utf-8');
    assert.strictEqual(content, 'new content', 'File should be overwritten');
  });

  test('removeDirectory cleans up completely', () => {
    const dirToRemove = join(testDir, 'to-remove');
    mkdirSync(dirToRemove);
    mkdirSync(join(dirToRemove, 'subdir'));
    writeFileSync(join(dirToRemove, 'file.txt'), 'content');
    writeFileSync(join(dirToRemove, 'subdir', 'nested.txt'), 'nested');
    
    assert.strictEqual(existsSync(dirToRemove), true, 'Directory should exist before removal');
    
    removeDirectory(dirToRemove);
    
    assert.strictEqual(existsSync(dirToRemove), false, 'Directory should not exist after removal');
  });

  test('ensureDirectory creates nested paths', () => {
    const nestedDir = join(testDir, 'a', 'b', 'c', 'd');
    
    assert.strictEqual(existsSync(nestedDir), false, 'Nested directory should not exist initially');
    
    ensureDirectory(nestedDir);
    
    assert.strictEqual(existsSync(nestedDir), true, 'Nested directory should be created');
  });

  test('simulated install workflow', () => {
    // Simulate the core installation workflow:
    // 1. Create source hooks directory
    // 2. Create destination (platform config) directory
    // 3. Copy hooks to destination
    // 4. Verify installation
    
    const srcHooks = join(testDir, 'source-hooks');
    const destHooks = join(testDir, 'dest-platform', '.claude', 'hooks', 'discuss');
    
    // Create source structure (like npm-package/hooks/)
    mkdirSync(join(srcHooks, 'common'), { recursive: true });
    mkdirSync(join(srcHooks, 'file-edit'), { recursive: true });
    mkdirSync(join(srcHooks, 'stop'), { recursive: true });
    
    writeFileSync(join(srcHooks, 'common', 'utils.py'), '# utils');
    writeFileSync(join(srcHooks, 'file-edit', 'track.py'), '# track');
    writeFileSync(join(srcHooks, 'stop', 'check.py'), '# check');
    
    // Perform install (what installer.js does)
    ensureDirectory(destHooks);
    copyDirectory(srcHooks, destHooks);
    
    // Verify all files copied
    assert.strictEqual(existsSync(join(destHooks, 'common', 'utils.py')), true);
    assert.strictEqual(existsSync(join(destHooks, 'file-edit', 'track.py')), true);
    assert.strictEqual(existsSync(join(destHooks, 'stop', 'check.py')), true);
  });

  test('simulated uninstall workflow', () => {
    // Simulate uninstall workflow:
    // 1. Create installed hooks
    // 2. Remove them
    // 3. Verify cleanup
    
    const installedHooks = join(testDir, '.claude', 'hooks', 'discuss');
    
    // Create "installed" structure
    mkdirSync(join(installedHooks, 'common'), { recursive: true });
    writeFileSync(join(installedHooks, 'common', 'utils.py'), '# utils');
    
    assert.strictEqual(existsSync(installedHooks), true, 'Hooks should exist before uninstall');
    
    // Uninstall
    removeDirectory(installedHooks);
    
    assert.strictEqual(existsSync(installedHooks), false, 'Hooks should be removed after uninstall');
  });
});
