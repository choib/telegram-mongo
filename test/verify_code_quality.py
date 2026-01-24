#!/usr/bin/env python3
"""
Comprehensive code verification script
"""
import ast
import sys
import os
from pathlib import Path

def check_syntax(files):
    """Check Python syntax"""
    errors = []
    for f in files:
        try:
            with open(f) as fp:
                ast.parse(fp.read(), filename=f)
        except SyntaxError as e:
            errors.append(f"Syntax error in {f}: {e}")
    return errors

def check_imports(files):
    """Check if all imports work"""
    errors = []
    for f in files:
        try:
            with open(f) as fp:
                content = fp.read()
            tree = ast.parse(content, filename=f)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            __import__(alias.name)
                        except ImportError as e:
                            errors.append(f"Import error in {f}: {alias.name} - {e}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    try:
                        __import__(module)
                    except ImportError as e:
                        errors.append(f"Import error in {f}: {module} - {e}")
        except Exception as e:
            errors.append(f"Error checking imports in {f}: {e}")
    return errors

def check_unused_imports(files):
    """Check for unused imports"""
    errors = []
    for f in files:
        try:
            with open(f) as fp:
                content = fp.read()
            tree = ast.parse(content, filename=f)
            
            # Get all imported names
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imported.add(name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name.split('.')[0]
                        imported.add(name)
            
            # Get all used names
            used = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used.add(node.id)
            
            unused = imported - used
            if unused:
                errors.append(f"Potential unused imports in {f}: {unused}")
        except Exception as e:
            errors.append(f"Error checking unused imports in {f}: {e}")
    return errors

def main():
    src_dir = Path("src")
    py_files = list(src_dir.glob("*.py"))
    
    print("=" * 60)
    print("CODE QUALITY VERIFICATION")
    print("=" * 60)
    
    # Check syntax
    print("\n1. Checking syntax...")
    syntax_errors = check_syntax(py_files)
    if syntax_errors:
        print("❌ Syntax errors found:")
        for error in syntax_errors:
            print(f"  - {error}")
    else:
        print("✓ All files have valid syntax")
    
    # Check imports
    print("\n2. Checking imports...")
    import_errors = check_imports(py_files)
    if import_errors:
        print("❌ Import errors found:")
        for error in import_errors:
            print(f"  - {error}")
    else:
        print("✓ All imports work correctly")
    
    # Check for unused imports
    print("\n3. Checking for unused imports...")
    unused_errors = check_unused_imports(py_files)
    if unused_errors:
        print("⚠ Potential unused imports (may be false positives):")
        for error in unused_errors:
            print(f"  - {error}")
    else:
        print("✓ No obvious unused imports found")
    
    print("\n" + "=" * 60)
    if not (syntax_errors or import_errors):
        print("✓ CODE VERIFICATION PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ CODE VERIFICATION FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
