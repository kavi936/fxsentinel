#!/usr/bin/env python3
"""
FXSentinel Deployment Readiness Verification
Final verification script to ensure the main app is ready for Railway deployment.
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - FILE NOT FOUND")
        return False

def check_dockerfile():
    """Check Dockerfile configuration"""
    print("\n🔍 Checking Dockerfile...")
    
    if not os.path.exists("Dockerfile"):
        print("❌ Dockerfile not found!")
        return False
    
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    checks = [
        ("FROM python:", "Python base image"),
        ("COPY requirements.txt", "Requirements copying"),
        ("RUN pip install", "Dependencies installation"),
        ("CMD [\"python3\", \"main.py\"]", "Correct startup command")
    ]
    
    passed = 0
    for check, description in checks:
        if check in content:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")
    
    return passed == len(checks)

def check_requirements():
    """Check requirements.txt files"""
    print("\n🔍 Checking requirements files...")
    
    files_to_check = [
        ("requirements.txt", "Root requirements"),
        ("backend/requirements.txt", "Backend requirements")
    ]
    
    passed = 0
    for filepath, description in files_to_check:
        if check_file_exists(filepath, description):
            # Check if Flask is in requirements
            with open(filepath, "r") as f:
                content = f.read()
                if "Flask" in content:
                    print(f"✅ {description} contains Flask")
                    passed += 1
                else:
                    print(f"❌ {description} missing Flask")
    
    return passed == len(files_to_check)

def check_railway_configs():
    """Check Railway configuration files"""
    print("\n🔍 Checking Railway configurations...")
    
    configs_to_check = [
        ("railway.json", "Main app Railway config"),
        ("railway.worker.json", "Worker Railway config")
    ]
    
    passed = 0
    for filepath, description in configs_to_check:
        if check_file_exists(filepath, description):
            try:
                with open(filepath, "r") as f:
                    config = json.load(f)
                    
                # Check required fields
                if "build" in config and "deploy" in config:
                    print(f"✅ {description} has correct structure")
                    passed += 1
                else:
                    print(f"❌ {description} missing required fields")
            except json.JSONDecodeError:
                print(f"❌ {description} has invalid JSON")
    
    return passed == len(configs_to_check)

def check_entry_points():
    """Check entry point files"""
    print("\n🔍 Checking entry points...")
    
    entry_points = [
        ("main.py", "Main app entry point"),
        ("backend/app.py", "Flask application"),
        ("backend/worker_app.py", "Worker entry point")
    ]
    
    passed = 0
    for filepath, description in entry_points:
        if check_file_exists(filepath, description):
            passed += 1
    
    return passed == len(entry_points)

def check_environment_example():
    """Check if environment example exists"""
    print("\n🔍 Checking environment configuration...")
    
    env_files = [
        ("env.example", "Environment example"),
        ("backend/env.example.secure", "Backend environment example")
    ]
    
    passed = 0
    for filepath, description in env_files:
        if check_file_exists(filepath, description):
            passed += 1
    
    return passed >= 1  # At least one should exist

def check_git_status():
    """Check git status"""
    print("\n🔍 Checking git status...")
    
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            changes = result.stdout.strip()
            if changes:
                print("⚠️ Uncommitted changes detected:")
                for line in changes.split('\n'):
                    if line:
                        print(f"   {line}")
                return False
            else:
                print("✅ No uncommitted changes")
                return True
        else:
            print("⚠️ Git status check failed")
            return False
    except FileNotFoundError:
        print("⚠️ Git not available")
        return False

def run_app_test():
    """Run the app test we created earlier"""
    print("\n🔍 Running app functionality test...")
    
    try:
        result = subprocess.run([sys.executable, 'test_app_simple.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ App functionality test passed")
            return True
        else:
            print("❌ App functionality test failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 FXSentinel Deployment Readiness Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    tests = [
        ("Dockerfile Configuration", check_dockerfile),
        ("Requirements Files", check_requirements),
        ("Railway Configurations", check_railway_configs),
        ("Entry Points", check_entry_points),
        ("Environment Configuration", check_environment_example),
        ("Git Status", check_git_status),
        ("App Functionality", run_app_test)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    # Final report
    print("\n" + "=" * 60)
    print("DEPLOYMENT READINESS REPORT")
    print("=" * 60)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your main app is READY for Railway deployment!")
        print("\n📋 Next Steps:")
        print("1. Push your changes to GitHub")
        print("2. Railway will automatically deploy the main app")
        print("3. Monitor the deployment logs in Railway dashboard")
        print("4. Test the deployed app using the health endpoint")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} TESTS FAILED!")
        print("⚠️ Fix the issues above before deploying to Railway")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
