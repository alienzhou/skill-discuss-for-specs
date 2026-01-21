/**
 * discuss-skills main entry
 * 
 * Exports install, uninstall, and utility functions.
 */

export { install, uninstall, listPlatforms } from './installer.js';
export { detectPlatform, getPlatformConfig } from './platform-config.js';
export { checkPythonEnvironment, copyDirectory } from './utils.js';
