#!/bin/bash
#
# Build for Cursor platform
# Read headers/cursor.yaml and inject YAML frontmatter into SKILL.md
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"

echo "Building for Cursor..."

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Build function: read header config and generate SKILL.md with frontmatter
build_skill() {
    local skill_name="$1"
    local skill_dir="$PROJECT_ROOT/skills/$skill_name"
    local output_dir="$BUILD_DIR/$skill_name"
    local header_file="$skill_dir/headers/cursor.yaml"
    local skill_file="$skill_dir/SKILL.md"
    
    mkdir -p "$output_dir"
    
    echo "  - Building $skill_name/SKILL.md"
    
    if [ -f "$header_file" ]; then
        # Read header config (skip comment lines)
        local name=$(grep "^name:" "$header_file" | sed 's/^name: *//' | tr -d '"')
        local description=$(grep "^description:" "$header_file" | sed 's/^description: *//' | tr -d '"')
        
        # Generate SKILL.md with frontmatter
        {
            echo "---"
            echo "name: $name"
            echo "description: \"$description\""
            echo "---"
            echo ""
            cat "$skill_file"
        } > "$output_dir/SKILL.md"
        
        echo "    ✓ Injected frontmatter from headers/cursor.yaml"
    else
        # No header config, copy directly (will show warning)
        echo "    ⚠ Warning: No headers/cursor.yaml found, copying without frontmatter"
        cp "$skill_file" "$output_dir/SKILL.md"
    fi
    
    # Copy references directory (if exists)
    if [ -d "$skill_dir/references" ]; then
        cp -r "$skill_dir/references" "$output_dir/"
        echo "    ✓ Copied references/"
    fi
}

# Build all skills
build_skill "discuss-coordinator"
build_skill "discuss-output"

echo ""
echo "✓ Cursor build complete: $BUILD_DIR"
echo ""
echo "To install, copy to ~/.cursor/skills/:"
echo "  cp -r $BUILD_DIR/* ~/.cursor/skills/"
