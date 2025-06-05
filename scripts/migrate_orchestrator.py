#!/usr/bin/env python3
"""
Migration script to transition from monolithic AGIOrchestrator to refactored version.

This script helps update imports and references throughout the codebase to use
the new refactored orchestrator with extracted components.
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple

# File patterns to check
PYTHON_PATTERNS = ['*.py']
EXCLUDE_DIRS = ['.git', '__pycache__', 'venv', 'env', '.venv', 'htmlcov', 'builds']

# Import replacements
IMPORT_REPLACEMENTS = [
    # Replace old imports with new ones
    (r'from src\.core\.orchestrator import AGIOrchestrator',
     'from src.core.orchestrator_refactored import AGIOrchestrator'),
    (r'from src\.core\.orchestrator import SystemState',
     'from src.core.state_manager import SystemState'),
    (r'from src\.core\.orchestrator import Message',
     'from src.core.event_bus import Message'),
    (r'from src\.core\.orchestrator import StateTransition',
     'from src.core.state_manager import StateTransition'),
]

# Code pattern replacements
CODE_REPLACEMENTS = [
    # Update direct state access
    (r'orchestrator\.state\s*=\s*(\w+)',
     r'await orchestrator.transition_to(\1)'),
    # Update service registration
    (r'orchestrator\.services\[(["\'])(.*?)\1\]\s*=\s*(.+)',
     r'orchestrator.register_service(\1\2\1, \3)'),
    # Update direct service access
    (r'orchestrator\.services\[(["\'])(.*?)\1\]',
     r'orchestrator.get_service(\1\2\1)'),
    # Update state history access
    (r'orchestrator\.state_history',
     r'orchestrator.state_manager.state_history'),
    # Update subscribers access
    (r'orchestrator\.subscribers',
     r'orchestrator.event_bus._event_handlers'),
]


def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the project"""
    python_files = []
    
    for pattern in PYTHON_PATTERNS:
        for file_path in root_dir.rglob(pattern):
            # Skip excluded directories
            if any(exclude in file_path.parts for exclude in EXCLUDE_DIRS):
                continue
            python_files.append(file_path)
            
    return python_files


def update_file(file_path: Path, dry_run: bool = True) -> List[Tuple[str, str]]:
    """Update a single file with replacements"""
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = original_content = f.read()
            
        # Apply import replacements
        for old_pattern, new_pattern in IMPORT_REPLACEMENTS:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_pattern, content)
                changes.append((old_pattern, new_pattern))
                
        # Apply code replacements
        for old_pattern, new_pattern in CODE_REPLACEMENTS:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_pattern, content)
                changes.append((old_pattern, new_pattern))
                
        # Write changes if not dry run and there were changes
        if changes and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return changes


def create_compatibility_shim():
    """Create a compatibility shim for gradual migration"""
    shim_content = '''# core/orchestrator.py
"""
Compatibility shim for gradual migration to refactored orchestrator.

This file provides backwards compatibility while migrating to the new
refactored architecture.
"""

# Re-export from new locations
from src.core.orchestrator_refactored import AGIOrchestrator
from src.core.state_manager import SystemState, StateTransition
from src.core.event_bus import Message

# Provide deprecation warnings
import warnings

def __getattr__(name):
    if name in ['AGIOrchestrator', 'SystemState', 'StateTransition', 'Message']:
        warnings.warn(
            f"Importing {name} from src.core.orchestrator is deprecated. "
            f"Please update your imports to use the new module structure.",
            DeprecationWarning,
            stacklevel=2
        )
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
'''
    
    return shim_content


def main():
    parser = argparse.ArgumentParser(description='Migrate to refactored orchestrator')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be changed without making changes')
    parser.add_argument('--create-shim', action='store_true',
                        help='Create compatibility shim instead of updating files')
    parser.add_argument('--root', type=str, default='.',
                        help='Project root directory')
    
    args = parser.parse_args()
    root_dir = Path(args.root).resolve()
    
    if args.create_shim:
        # Create compatibility shim
        shim_path = root_dir / 'src' / 'core' / 'orchestrator_compat.py'
        print(f"Creating compatibility shim at {shim_path}")
        print(create_compatibility_shim())
        if not args.dry_run:
            with open(shim_path, 'w') as f:
                f.write(create_compatibility_shim())
        return
        
    # Find all Python files
    python_files = find_python_files(root_dir)
    print(f"Found {len(python_files)} Python files to check")
    
    # Process each file
    total_changes = 0
    for file_path in python_files:
        changes = update_file(file_path, args.dry_run)
        if changes:
            print(f"\n{file_path}:")
            for old, new in changes:
                print(f"  - Replace: {old}")
                print(f"    With: {new}")
            total_changes += len(changes)
            
    print(f"\nTotal changes: {total_changes}")
    
    if args.dry_run:
        print("\nThis was a dry run. Use without --dry-run to apply changes.")
    else:
        print("\nChanges applied. Remember to:")
        print("1. Run tests to ensure everything works")
        print("2. Update any documentation referencing the old structure")
        print("3. Remove the old orchestrator.py file when migration is complete")


if __name__ == '__main__':
    main()