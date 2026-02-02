/**
 * Installation and uninstallation logic
 */

import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

import {
  checkPythonEnvironment,
  copyDirectory,
  removeDirectory,
  ensureDirectory,
  getHooksDir,
  getLogsDir,
  getPackageRoot
} from './utils.js';

import {
  PLATFORMS,
  detectPlatform,
  getPlatformConfig,
  getSkillsDir,
  getProjectHooksDir,
  installHooksConfig,
  removeHooksConfig,
  platformSupportsStopHook
} from './platform-config.js';

import {
  showBanner,
  createSpinner,
  success,
  error,
  info,
  warning,
  newline,
  showCompletionBox,
  showUninstallBox,
  colors
} from './ui.js';

/**
 * List supported platforms
 * @param {Object} options - Options
 * @param {boolean} options.showStatus - Show detailed installation status
 */
export function listPlatforms(options = {}) {
  newline();
  console.log(colors.bold('Supported Platforms'));
  console.log(colors.dim('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
  newline();
  
  const detected = detectPlatform();
  
  // Group platforms by level
  const l2Platforms = Object.entries(PLATFORMS).filter(([, config]) => config.level === 'L2');
  const l1Platforms = Object.entries(PLATFORMS).filter(([, config]) => config.level === 'L1');
  
  // L2 Platforms
  console.log(colors.primary('  L2 Platforms') + colors.dim(' (Skills + Hooks - auto-reminder)'));
  newline();
  
  for (const [id, config] of l2Platforms) {
    const isDetected = detected.includes(id);
    const status = isDetected 
      ? colors.success('● detected') 
      : colors.dim('○ not found');
    
    console.log(`    ${colors.bold(config.name.padEnd(14))} ${colors.dim(id.padEnd(12))} ${status}`);
    console.log(`      ${colors.dim(`~/${config.configDir}/${config.skillsDir}/`)}`);
    newline();
  }
  
  // L1 Platforms
  console.log(colors.primary('  L1 Platforms') + colors.dim(' (Skills only - manual precipitation)'));
  newline();
  
  for (const [id, config] of l1Platforms) {
    const isDetected = detected.includes(id);
    const status = isDetected 
      ? colors.success('● detected') 
      : colors.dim('○ not found');
    
    console.log(`    ${colors.bold(config.name.padEnd(14))} ${colors.dim(id.padEnd(12))} ${status}`);
    console.log(`      ${colors.dim(`~/${config.configDir}/${config.skillsDir}/`)}`);
    newline();
  }
  
  // Summary
  console.log(colors.dim('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
  
  if (detected.length > 0) {
    console.log(colors.success(`  ${detected.length} platform(s) detected: `) + 
      detected.map(id => colors.bold(id)).join(', '));
  } else {
    console.log(colors.warning('  No platforms detected'));
    console.log(colors.dim('  Install a supported AI assistant first, or use --platform flag'));
  }
  
  newline();
  console.log(colors.dim('  Usage: discuss-for-specs install [-p <platform>]'));
  newline();
}

/**
 * Install skills and hooks
 * 
 * @param {Object} options - Install options
 */
export async function install(options = {}) {
  // Show banner
  showBanner();

  // 1. Check Python environment
  let spinner = createSpinner('Checking Python environment...');
  spinner.start();
  
  const pythonCheck = await checkPythonEnvironment();
  
  if (!pythonCheck.success) {
    spinner.fail('Python environment check failed');
    error(
      'Python 3 is required but was not found',
      'brew install python3  # macOS\nsudo apt install python3  # Ubuntu'
    );
    throw new Error('Python environment check failed. Please install Python 3 and PyYAML.');
  }
  spinner.succeed('Python environment OK');

  // 2. Detect or validate platform
  let targetPlatform = options.platform;
  
  if (!targetPlatform) {
    const detected = detectPlatform();
    
    if (detected.length === 0) {
      error(
        'No supported platform detected',
        'Install a supported AI assistant first, or use --platform flag.\n' +
        '    Supported: claude-code, cursor, kilocode, opencode, codex'
      );
      throw new Error(
        'No supported platform detected. Please install a supported AI assistant first, ' +
        'or specify a platform with --platform.'
      );
    }
    
    if (detected.length === 1) {
      targetPlatform = detected[0];
      info(`Detected platform: ${colors.bold(PLATFORMS[targetPlatform].name)}`);
    } else {
      // Multiple platforms detected, ask user or use first
      info('Multiple platforms detected:');
      detected.forEach(p => console.log(`  ${colors.dim('•')} ${PLATFORMS[p].name}`));
      newline();
      info(`Using: ${colors.bold(PLATFORMS[detected[0]].name)}`);
      console.log(colors.dim('  (Use --platform to specify a different one)'));
      targetPlatform = detected[0];
    }
  }

  const platformConfig = getPlatformConfig(targetPlatform);
  
  // 3. Handle target directory for project-level installation
  let targetDir = null;
  let isProjectLevel = false;
  
  // --project-level is shorthand for --target .
  if (options.projectLevel) {
    const { resolve } = await import('path');
    targetDir = resolve('.');
    isProjectLevel = true;
  } else if (options.target) {
    const { resolve } = await import('path');
    targetDir = resolve(options.target.replace(/^~/, process.env.HOME || ''));
    isProjectLevel = true;
    
    if (!existsSync(targetDir)) {
      error(`Target directory does not exist: ${targetDir}`);
      throw new Error(`Target directory does not exist: ${targetDir}`);
    }
  }
  
  if (isProjectLevel) {
    newline();
    info(`Installing for ${colors.bold(platformConfig.name)} (project-level)`);
    console.log(colors.dim(`  Target: ${targetDir}`));
  } else {
    newline();
    info(`Installing for ${colors.bold(platformConfig.name)} (user-level)`);
  }

  // 4. Get package root (where dist/ and hooks/ are)
  const packageRoot = getPackageRoot();
  
  // 5. Install Skills (unless skipped)
  if (!options.skipSkills) {
    newline();
    spinner = createSpinner('Installing Skills...');
    spinner.start();
    
    const distDir = join(packageRoot, 'dist', targetPlatform);
    const skillsDir = getSkillsDir(targetPlatform, targetDir);
    
    if (!existsSync(distDir)) {
      spinner.warn(`No pre-built skills found for ${targetPlatform}`);
    } else {
      ensureDirectory(skillsDir);
      
      // Copy each skill (merged into single discuss-for-specs as per D7)
      const skills = ['discuss-for-specs'];
      const installedSkills = [];
      
      for (const skill of skills) {
        const srcSkill = join(distDir, skill);
        const destSkill = join(skillsDir, skill);
        
        if (existsSync(srcSkill)) {
          copyDirectory(srcSkill, destSkill);
          installedSkills.push(skill);
          
          // Inject L1 guidance if platform doesn't support stop hook
          if (!platformSupportsStopHook(targetPlatform)) {
            const skillMdPath = join(destSkill, 'SKILL.md');
            const l1GuidancePath = join(srcSkill, 'references', 'l1-guidance.md');
            
            if (existsSync(skillMdPath) && existsSync(l1GuidancePath)) {
              try {
                const skillContent = readFileSync(skillMdPath, 'utf-8');
                const l1Guidance = readFileSync(l1GuidancePath, 'utf-8');
                
                // Extract content layer (skip metadata comments)
                const guidanceLines = l1Guidance.split('\n');
                const contentStart = guidanceLines.findIndex(line => 
                  line.trim().startsWith('##') && !line.trim().startsWith('## 📝')
                );
                const contentEnd = guidanceLines.findIndex((line, idx) => 
                  idx > contentStart && line.trim().startsWith('##') && !line.trim().startsWith('## 📝')
                );
                
                let guidanceContent = '';
                if (contentStart >= 0) {
                  const startIdx = guidanceLines.findIndex((line, idx) => 
                    idx >= contentStart && line.trim().startsWith('## 📝')
                  );
                  const endIdx = contentEnd >= 0 ? contentEnd : guidanceLines.length;
                  guidanceContent = guidanceLines.slice(startIdx, endIdx).join('\n').trim();
                } else {
                  // Fallback: use everything after first ##
                  const firstHeader = guidanceLines.findIndex(line => line.trim().startsWith('##'));
                  if (firstHeader >= 0) {
                    guidanceContent = guidanceLines.slice(firstHeader).join('\n').trim();
                  }
                }
                
                // Find injection point: after "Your Responsibilities" section
                const responsibilitiesMarker = '## 🎯 Your Responsibilities';
                const responsibilitiesIndex = skillContent.indexOf(responsibilitiesMarker);
                
                if (responsibilitiesIndex >= 0 && guidanceContent) {
                  // Find the end of "Your Responsibilities" section (next ## or ---)
                  const afterMarker = skillContent.substring(responsibilitiesIndex);
                  const nextSectionMatch = afterMarker.match(/\n(## |---)/);
                  const injectionPoint = nextSectionMatch 
                    ? responsibilitiesIndex + nextSectionMatch.index + 1
                    : responsibilitiesIndex + afterMarker.length;
                  
                  // Inject guidance
                  const before = skillContent.substring(0, injectionPoint);
                  const after = skillContent.substring(injectionPoint);
                  const updatedContent = before + '\n\n' + guidanceContent + '\n\n' + after;
                  
                  writeFileSync(skillMdPath, updatedContent, 'utf-8');
                  // L1 guidance injected successfully
                }
              } catch (e) {
                // Silent - L1 guidance injection is optional, continue on error
              }
            }
          }
        }
      }
      
      spinner.succeed('Skills installed');
      installedSkills.forEach(skill => success(skill, true));
    }
  }

  // 6. Install Hooks (unless skipped)
  // For project-level: install hooks to project directory
  // For user-level: install hooks to ~/.discuss-for-specs/hooks/
  // Note: L1 platforms don't have hooks support, skip for them
  const isL2Platform = platformSupportsStopHook(targetPlatform);
  
  if (!options.skipHooks && isL2Platform) {
    newline();
    spinner = createSpinner('Installing Hooks...');
    spinner.start();
    
    const srcHooks = join(packageRoot, 'hooks');
    
    // Determine hooks destination based on installation mode
    let destHooks;
    if (isProjectLevel) {
      // Project-level: install hooks to project/.{platform}/hooks/
      destHooks = getProjectHooksDir(targetPlatform, targetDir);
      spinner.text = 'Installing Hooks (project-level)...';
    } else {
      // User-level: install hooks to ~/.discuss-for-specs/hooks/
      destHooks = getHooksDir();
      spinner.text = 'Installing Hooks (user-level)...';
    }
    
    if (!existsSync(srcHooks)) {
      spinner.fail('Hooks source not found');
      throw new Error(`Hooks source not found: ${srcHooks}`);
    }
    
    // Copy hooks to destination directory
    copyDirectory(srcHooks, destHooks);
    
    // Apply stale_threshold if specified
    if (options.staleThreshold !== undefined) {
      const threshold = options.staleThreshold;
      
      // Validate threshold (must be non-negative integer)
      if (!Number.isInteger(threshold) || threshold < 0) {
        spinner.fail('Invalid stale-threshold value');
        throw new Error('--stale-threshold must be a non-negative integer (0 = disabled)');
      }
      
      // Update snapshot_manager.py DEFAULT_STALE_THRESHOLD
      const snapshotManagerPath = join(destHooks, 'common', 'snapshot_manager.py');
      if (existsSync(snapshotManagerPath)) {
        let content = readFileSync(snapshotManagerPath, 'utf-8');
        content = content.replace(
          /DEFAULT_STALE_THRESHOLD\s*=\s*\d+/,
          `DEFAULT_STALE_THRESHOLD = ${threshold}`
        );
        writeFileSync(snapshotManagerPath, content, 'utf-8');
      }
    }
    
    // Create logs directory
    const logsDir = getLogsDir();
    ensureDirectory(logsDir);
    
    spinner.succeed('Hooks installed');
    success(`Copied to ${destHooks}`, true);
    if (options.staleThreshold !== undefined) {
      success(`Stale threshold: ${options.staleThreshold}${options.staleThreshold === 0 ? ' (disabled)' : ' rounds'}`, true);
    }
    success(`Logs directory: ${logsDir}`, true);
    
    // Configure platform hooks
    newline();
    spinner = createSpinner('Configuring platform hooks...');
    spinner.start();
    installHooksConfig(targetPlatform, { targetDir: isProjectLevel ? targetDir : null, hooksDir: destHooks });
    spinner.succeed('Platform hooks configured');
  } else if (!options.skipHooks && !isL2Platform) {
    // L1 platform - inform user that hooks are not applicable
    newline();
    info(`${colors.dim('Hooks not applicable for L1 platform (no auto-reminder)')}`);
    info(`${colors.dim('Use "Precipitation Discipline" section in SKILL.md for manual reminders')}`);
  }

  // 7. Done - show completion box
  const components = [];
  if (!options.skipSkills) {
    components.push(`Skills: ${getSkillsDir(targetPlatform, targetDir)}`);
  }
  if (!options.skipHooks && isL2Platform) {
    if (isProjectLevel) {
      components.push(`Hooks: ${getProjectHooksDir(targetPlatform, targetDir)}`);
    } else {
      components.push(`Hooks: ${getHooksDir()}`);
      components.push(`Logs: ${getLogsDir()}`);
    }
  }
  
  const nextSteps = [`Open ${platformConfig.name}`];
  if (targetDir) {
    nextSteps.push(`Open project: ${targetDir}`);
  }
  nextSteps.push('Start a discussion with your AI assistant');
  if (isL2Platform) {
    nextSteps.push('The hooks will automatically track your progress');
  } else {
    nextSteps.push('Remember to document decisions (L1 platform - no auto-reminder)');
  }
  
  showCompletionBox({ components, nextSteps });
}

/**
 * Uninstall skills and hooks
 * 
 * @param {Object} options - Uninstall options
 */
export async function uninstall(options = {}) {
  // Show banner
  showBanner();

  // 1. Detect or validate platform
  let targetPlatform = options.platform;
  
  if (!targetPlatform) {
    const detected = detectPlatform();
    
    if (detected.length === 0) {
      warning('No supported platform detected');
      return;
    }
    
    targetPlatform = detected[0];
    info(`Detected platform: ${colors.bold(PLATFORMS[targetPlatform].name)}`);
  }

  const platformConfig = getPlatformConfig(targetPlatform);
  
  // Handle target directory for project-level uninstallation
  let targetDir = null;
  let isProjectLevel = false;
  
  // --project-level is shorthand for --target .
  if (options.projectLevel) {
    const { resolve } = await import('path');
    targetDir = resolve('.');
    isProjectLevel = true;
  } else if (options.target) {
    const { resolve } = await import('path');
    targetDir = resolve(options.target.replace(/^~/, process.env.HOME || ''));
    isProjectLevel = true;
  }
  
  if (isProjectLevel) {
    newline();
    info(`Uninstalling from ${colors.bold(platformConfig.name)} (project-level)`);
    console.log(colors.dim(`  Target: ${targetDir}`));
  } else {
    newline();
    info(`Uninstalling from ${colors.bold(platformConfig.name)} (user-level)`);
  }

  // 2. Remove Skills
  if (!options.keepSkills) {
    newline();
    let spinner = createSpinner('Removing Skills...');
    spinner.start();
    
    const skillsDir = getSkillsDir(targetPlatform, targetDir);
    const skills = ['discuss-for-specs'];
    const removedSkills = [];
    
    for (const skill of skills) {
      const skillPath = join(skillsDir, skill);
      if (existsSync(skillPath)) {
        removeDirectory(skillPath);
        removedSkills.push(skill);
      }
    }
    
    if (removedSkills.length > 0) {
      spinner.succeed('Skills removed');
      removedSkills.forEach(skill => success(skill, true));
    } else {
      spinner.info('No skills to remove');
    }
  }

  // 3. Remove Hooks
  if (!options.keepHooks) {
    newline();
    let spinner = createSpinner('Removing Hooks...');
    spinner.start();
    
    let hooksDir;
    if (isProjectLevel) {
      hooksDir = getProjectHooksDir(targetPlatform, targetDir);
    } else {
      hooksDir = getHooksDir();
    }
    
    if (existsSync(hooksDir)) {
      removeDirectory(hooksDir);
      spinner.succeed('Hooks removed');
      success(hooksDir, true);
    } else {
      spinner.info('No hooks to remove');
    }
    
    // Remove hooks from platform config
    newline();
    spinner = createSpinner('Removing platform hooks configuration...');
    spinner.start();
    removeHooksConfig(targetPlatform, targetDir);
    spinner.succeed('Platform hooks configuration removed');
  }

  // 4. Done
  const noteMessage = isProjectLevel 
    ? 'Project-level installation removed.'
    : 'Note: Logs directory was preserved at ~/.discuss-for-specs/logs/\nDelete it manually if you want to remove all data.';
  
  showUninstallBox(
    'Uninstallation complete!',
    noteMessage
  );
}
