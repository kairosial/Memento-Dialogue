#!/usr/bin/env python3
"""
Simple test script to verify API endpoints are working.
Run this after starting the server to test basic functionality.
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check endpoint."""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_root_endpoint():
    """Test root endpoint."""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_docs_endpoint():
    """Test API documentation endpoint."""
    print("\n🔍 Testing API docs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API docs accessible")
        else:
            print(f"❌ API docs failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_signup_validation():
    """Test signup endpoint validation."""
    print("\n🔍 Testing signup validation...")
    try:
        # Test invalid data
        invalid_data = {
            "email": "invalid-email",
            "password": "123"  # Too short
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=invalid_data)
        if response.status_code == 422:
            print("✅ Signup validation working")
            print(f"   Validation errors detected correctly")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting API tests...\n")
    
    test_health_check()
    test_root_endpoint()
    test_docs_endpoint()
    test_signup_validation()
    
    print("\n🎯 Test Summary:")
    print("- If health check passed, the server is running correctly")
    print("- Visit http://localhost:8000/docs for interactive API documentation")
    print("- Use the docs to test actual authentication and CRUD operations")


if __name__ == "__main__":
    main()