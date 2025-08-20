#!/usr/bin/env python3
"""
Manual API testing script for Memento Box Authentication
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("=== Testing Memento Box Authentication API ===\n")
    
    # Test data
    test_user = {
        "email": "test@memento-test.com",
        "password": "TestPassword123",
        "full_name": "테스트 사용자"
    }
    
    print("1. Testing Signup...")
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=test_user)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    except Exception as e:
        print(f"Signup test failed: {e}\n")
    
    print("2. Testing Login...")
    try:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
        
        if "access_token" in result:
            token = result["access_token"]
            
            print("3. Testing Protected Endpoint (Logout)...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
            
            print("4. Testing Token Refresh...")
            response = requests.post(f"{BASE_URL}/auth/refresh", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
            
            print("5. Testing Password Reset...")
            reset_data = {"email": test_user["email"]}
            response = requests.post(f"{BASE_URL}/auth/reset-password", json=reset_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
            
    except Exception as e:
        print(f"Login test failed: {e}\n")
    
    print("6. Testing Invalid Login...")
    try:
        invalid_login = {
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=invalid_login)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    except Exception as e:
        print(f"Invalid login test failed: {e}\n")

if __name__ == "__main__":
    test_api()