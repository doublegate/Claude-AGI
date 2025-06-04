#!/usr/bin/env python3
"""
Local CI Script - Run the same tests as CI pipeline locally
Matches the optimized CI pipeline structure for consistency
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, env_vars=None, cwd=None):
    """Run a command and return success status"""
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    print(f"🔄 Running: {cmd}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            env=env, 
            cwd=cwd,
            capture_output=False
        )
        duration = time.time() - start_time
        print(f"✅ Completed in {duration:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"❌ Failed after {duration:.2f}s (exit code: {e.returncode})")
        return False

def setup_environment():
    """Set up the test environment"""
    print("🏗️  Setting up test environment...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    return True

def install_dependencies():
    """Install test dependencies"""
    print("📦 Installing dependencies...")
    
    commands = [
        "python -m pip install --upgrade pip",
        "pip install -r requirements.txt",
        "pip install -r requirements-test.txt"
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    
    return True

def run_unit_tests():
    """Run unit tests with coverage"""
    print("\n🧪 Running unit tests...")
    
    env_vars = {"CLAUDE_AGI_TEST_MODE": "true"}
    
    return run_command(
        "pytest tests/unit -v --cov=src --cov-report=term-missing --cov-report=html",
        env_vars=env_vars
    )

def run_integration_tests():
    """Run integration tests (requires services)"""
    print("\n🔗 Running integration tests...")
    
    # Check if services are available
    print("⚠️  Note: Integration tests require Redis and PostgreSQL")
    print("   Start services with: docker-compose up -d redis postgres")
    
    env_vars = {
        "CLAUDE_AGI_TEST_MODE": "true",
        "REDIS_URL": "redis://localhost:6379",
        "POSTGRES_URL": "postgresql://postgres:postgres@localhost:5432/claude_agi_test"
    }
    
    return run_command(
        "pytest tests/integration -v --timeout=60 --timeout-method=thread",
        env_vars=env_vars
    )

def run_safety_tests():
    """Run safety validation tests"""
    print("\n🛡️  Running safety tests...")
    
    env_vars = {"CLAUDE_AGI_TEST_MODE": "true"}
    
    return run_command(
        "pytest tests/safety -v -m safety",
        env_vars=env_vars
    )

def run_performance_tests():
    """Run performance benchmark tests"""
    print("\n⚡ Running performance tests...")
    
    env_vars = {"CLAUDE_AGI_TEST_MODE": "true"}
    
    return run_command(
        "pytest tests/performance -v",
        env_vars=env_vars
    )

def main():
    """Main CI runner"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    print(f"🚀 Claude-AGI Local CI Runner")
    print(f"📋 Test type: {test_type}")
    print("=" * 50)
    
    # Setup
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Install dependencies (like CI setup job)
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Run tests based on type
    results = {}
    
    if test_type in ["all", "unit"]:
        results["unit"] = run_unit_tests()
    
    if test_type in ["all", "integration"]:
        results["integration"] = run_integration_tests()
    
    if test_type in ["all", "safety"]:
        results["safety"] = run_safety_tests()
    
    if test_type in ["all", "performance"]:
        results["performance"] = run_performance_tests()
    
    if test_type == "coverage":
        # Run all tests with comprehensive coverage
        print("\n📊 Running comprehensive coverage analysis...")
        env_vars = {"CLAUDE_AGI_TEST_MODE": "true"}
        results["coverage"] = run_command(
            "pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml",
            env_vars=env_vars
        )
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.title()}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Ready for CI/CD")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()