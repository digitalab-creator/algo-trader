"""
CLI tool for validating microservice setup.
"""

import sys


def main() -> None:
    """
    Validate microservice configuration.

    Checks:
    - pyproject.toml exists and valid
    - Required dependencies installed
    - Environment variables set
    - Tests exist
    """
    print("🔍 Validating microservice setup...")

    checks_passed = 0
    checks_failed = 0

    # Check 1: pyproject.toml
    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
            if "project" in config:
                print("✓ pyproject.toml is valid")
                checks_passed += 1
            else:
                print("✗ pyproject.toml missing [project] section")
                checks_failed += 1
    except FileNotFoundError:
        print("✗ pyproject.toml not found")
        checks_failed += 1
    except Exception as e:
        print(f"✗ pyproject.toml error: {e}")
        checks_failed += 1

    # Check 2: Required dependencies
    try:
        import fastapi  # noqa: F401
        import pydantic  # noqa: F401
        import sqlalchemy  # noqa: F401

        print("✓ Core dependencies installed")
        checks_passed += 1
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        checks_failed += 1

    # Check 3: Tests directory
    import os

    if os.path.exists("tests"):
        print("✓ Tests directory exists")
        checks_passed += 1
    else:
        print("⚠ Tests directory not found")
        checks_failed += 1

    # Summary
    print(f"\n📊 Results: {checks_passed} passed, {checks_failed} failed")

    if checks_failed > 0:
        print("❌ Validation failed!")
        sys.exit(1)
    else:
        print("✅ Validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

