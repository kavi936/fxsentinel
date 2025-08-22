#!/usr/bin/env python3
"""
Simple Web App Functionality Test
Tests basic functionality of FXSentinel web application
"""

import os
import sys
import requests
import time
import subprocess
import threading
from datetime import datetime

def print_status(message, status="INFO"):
    """Print a formatted status message"""
    status_icons = {
        "SUCCESS": "✅",
        "ERROR": "❌", 
        "WARNING": "⚠️",
        "INFO": "ℹ️"
    }
    icon = status_icons.get(status, "ℹ️")
    print(f"{icon} {message}")

def start_backend_server():
    """Start the backend server"""
    print_status("Starting backend server...", "INFO")
    
    # Change to backend directory and start server
    os.chdir('backend')
    process = subprocess.Popen(['python3', 'app.py'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(5)
    
    # Check if process is running
    if process.poll() is None:
        print_status("Backend server started successfully", "SUCCESS")
        return process
    else:
        stdout, stderr = process.communicate()
        print_status(f"Backend server failed to start: {stderr.decode()}", "ERROR")
        return None

def start_frontend_server():
    """Start the frontend development server"""
    print_status("Starting frontend server...", "INFO")
    
    # Return to root directory
    os.chdir('..')
    
    # Start frontend server
    process = subprocess.Popen(['npm', 'run', 'dev'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(10)
    
    # Check if process is running
    if process.poll() is None:
        print_status("Frontend server started successfully", "SUCCESS")
        return process
    else:
        stdout, stderr = process.communicate()
        print_status(f"Frontend server failed to start: {stderr.decode()}", "ERROR")
        return None

def test_backend_endpoints():
    """Test backend API endpoints"""
    print_status("Testing backend endpoints...", "INFO")
    
    base_url = "http://localhost:5001"
    endpoints = [
        "/",
        "/api/news",
        "/api/economic-calendar"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print_status(f"Backend endpoint {endpoint} working", "SUCCESS")
            else:
                print_status(f"Backend endpoint {endpoint} returned {response.status_code}", "WARNING")
        except requests.exceptions.RequestException as e:
            print_status(f"Backend endpoint {endpoint} failed: {str(e)}", "ERROR")

def test_frontend_access():
    """Test frontend access"""
    print_status("Testing frontend access...", "INFO")
    
    try:
        # Try to access the frontend
        response = requests.get("http://localhost:5173", timeout=10)
        if response.status_code == 200:
            print_status("Frontend is accessible", "SUCCESS")
            return True
        else:
            print_status(f"Frontend returned status {response.status_code}", "WARNING")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Frontend access failed: {str(e)}", "ERROR")
        return False

def test_api_integration():
    """Test API integration between frontend and backend"""
    print_status("Testing API integration...", "INFO")
    
    try:
        # Test if frontend can access backend API
        response = requests.get("http://localhost:5001/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'articles' in data or 'news' in data:
                print_status("API integration working - news data available", "SUCCESS")
                return True
            else:
                print_status("API integration working but no news data", "WARNING")
                return False
        else:
            print_status(f"API integration failed - status {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"API integration failed: {str(e)}", "ERROR")
        return False

def main():
    """Run the functionality test"""
    print("🚀 FXSentinel Web App Functionality Test")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv('backend/.env')
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend server
        backend_process = start_backend_server()
        if not backend_process:
            print_status("Cannot proceed without backend server", "ERROR")
            return
        
        # Test backend endpoints
        test_backend_endpoints()
        
        # Start frontend server
        frontend_process = start_frontend_server()
        if not frontend_process:
            print_status("Cannot proceed without frontend server", "ERROR")
            return
        
        # Test frontend access
        frontend_working = test_frontend_access()
        
        # Test API integration
        api_working = test_api_integration()
        
        # Summary
        print_status("\n" + "="*50, "INFO")
        print_status("FUNCTIONALITY TEST SUMMARY", "INFO")
        print_status("="*50, "INFO")
        
        if backend_process and frontend_process and frontend_working and api_working:
            print_status("🎉 Your web app is working correctly!", "SUCCESS")
            print_status("Frontend: http://localhost:5173", "INFO")
            print_status("Backend: http://localhost:5001", "INFO")
            print_status("You can now access your web app in the browser", "INFO")
        else:
            print_status("⚠️ Some components are not working properly", "WARNING")
            print_status("Check the output above for specific issues", "INFO")
        
        # Keep servers running for manual testing
        print_status("Servers are running. Press Ctrl+C to stop.", "INFO")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print_status("Stopping servers...", "INFO")
    
    except Exception as e:
        print_status(f"Test failed with error: {str(e)}", "ERROR")
    
    finally:
        # Clean up processes
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
            print_status("Backend server stopped", "INFO")
        
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
            print_status("Frontend server stopped", "INFO")

if __name__ == "__main__":
    main()
