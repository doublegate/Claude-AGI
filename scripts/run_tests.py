#!/usr/bin/env python3
"""
Test Runner for Claude-AGI
=========================

Run all tests or specific test categories.

Usage:
    python scripts/run_tests.py [category]
    
Categories:
    all         - Run all tests (default)
    unit        - Run unit tests only
    integration - Run integration tests only
    safety      - Run safety-critical tests only
    performance - Run performance tests only
    coverage    - Run with coverage report
"""

import sys
import subprocess
from pathlib import Path

def run_tests(category="all"):
    """Run tests based on category"""
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    # Base pytest command
    cmd = ["python", "-m", "pytest", "-v"]
    
    # Add category-specific options
    if category == "unit":
        cmd.extend(["-m", "unit", "tests/unit/"])
    elif category == "integration":
        cmd.extend(["-m", "integration", "tests/integration/"])
    elif category == "safety":
        cmd.extend(["-m", "safety", "tests/safety/"])
    elif category == "performance":
        cmd.extend(["-m", "performance", "tests/performance/"])
    elif category == "coverage":
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term", "tests/"])
    else:  # all
        cmd.append("tests/")
    
    # Add common options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--durations=10",  # Show 10 slowest tests
        "-p", "no:warnings"  # Suppress warnings for cleaner output
    ])
    
    print(f"Running {category} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run tests
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode

def main():
    """Main entry point"""
    category = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    valid_categories = ["all", "unit", "integration", "safety", "performance", "coverage"]
    if category not in valid_categories:
        print(f"Invalid category: {category}")
        print(f"Valid categories: {', '.join(valid_categories)}")
        sys.exit(1)
    
    exit_code = run_tests(category)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()