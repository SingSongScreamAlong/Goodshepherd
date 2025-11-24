"""
Comprehensive test runner for The Good Shepherd backend.
Runs all tests and generates a report.
"""
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    success = result.returncode == 0
    print(f"\n{'✓' if success else '✗'} {description}: {'PASSED' if success else 'FAILED'}")

    return success

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("THE GOOD SHEPHERD - COMPREHENSIVE TEST SUITE")
    print("="*60)

    # Change to backend directory
    backend_dir = Path(__file__).parent

    results = []

    # 1. Check Python syntax
    print("\n\n### STEP 1: SYNTAX CHECKS ###")
    cmd = f"cd {backend_dir} && python -m py_compile $(find . -name '*.py' | grep -v __pycache__ | grep -v alembic/versions)"
    results.append(("Syntax Check", run_command(cmd, "Python Syntax Validation")))

    # 2. Run pytest with coverage
    print("\n\n### STEP 2: UNIT TESTS ###")
    cmd = f"cd {backend_dir} && python -m pytest tests/ -v --tb=short"
    results.append(("Unit Tests", run_command(cmd, "Unit Tests (pytest)")))

    # 3. Test imports
    print("\n\n### STEP 3: IMPORT TESTS ###")
    cmd = f"cd {backend_dir} && python -c 'from backend.core import *; from backend.models import *; from backend.services import *; print(\"All imports successful\")'"
    results.append(("Import Tests", run_command(cmd, "Import Tests")))

    # Print summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30s} {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} test suites passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
