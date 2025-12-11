#!/usr/bin/env python3
"""
Post-Refactoring Validation Script
Run this to verify the refactored application is working correctly.
"""
import sys
import importlib.util


def test_import(module_name, description):
    """Test if a module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"❌ {description}: Module '{module_name}' not found")
            return False
        
        module = importlib.import_module(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_name} - {str(e)}")
        return False


def main():
    """Run validation checks."""
    print("=" * 60)
    print("Post-Refactoring Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("app", "App package"),
        ("app.auth", "Auth blueprint"),
        ("app.routes", "Routes blueprint"),
        ("app.sheets", "Sheets module"),
        ("app.parsers", "Parsers package"),
        ("app.parsers.linkedin", "LinkedIn parser"),
        ("app.parsers.handshake", "Handshake parser"),
        ("app.parsers.generic", "Generic parser"),
    ]
    
    results = []
    for module_name, description in checks:
        results.append(test_import(module_name, description))
    
    print()
    print("=" * 60)
    
    if all(results):
        print("✅ All imports successful!")
        print()
        print("Next steps:")
        print("1. Run tests: pytest")
        print("2. Test locally: flask run")
        print("3. Commit changes: git add . && git commit")
        print("4. Deploy to Render")
        return 0
    else:
        print("❌ Some imports failed. Fix errors before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
