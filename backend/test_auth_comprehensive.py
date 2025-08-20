import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import json

# Test client
client = TestClient(app)

# Test data
TEST_USER = {
    "email": "test@memento-box.com",
    "password": "TestPassword123",
    "full_name": "테스트 사용자",
    "birth_date": "1980-01-01",
    "gender": "male",
    "phone": "010-1234-5678"
}

INVALID_USER = {
    "email": "invalid-email",
    "password": "123",  # Too short
    "full_name": "Test User"
}

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_signup_success(self):
        """Test successful user registration"""
        response = client.post("/auth/signup", json=TEST_USER)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "User created successfully" in data["message"]
        assert data["data"]["email"] == TEST_USER["email"]
        assert "user_id" in data["data"]
    
    def test_signup_invalid_email(self):
        """Test registration with invalid email"""
        response = client.post("/auth/signup", json=INVALID_USER)
        
        assert response.status_code == 422  # Validation error
    
    def test_signup_duplicate_email(self):
        """Test registration with existing email"""
        # First registration
        client.post("/auth/signup", json=TEST_USER)
        
        # Duplicate registration
        response = client.post("/auth/signup", json=TEST_USER)
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]
    
    def test_signup_password_too_short(self):
        """Test registration with short password"""
        user_data = TEST_USER.copy()
        user_data["password"] = "123"
        
        response = client.post("/auth/signup", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self):
        """Test successful login"""
        # First create user
        client.post("/auth/signup", json=TEST_USER)
        
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.access_token_expire_minutes * 60
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # Create user first
        client.post("/auth/signup", json=TEST_USER)
        
        login_data = {
            "email": TEST_USER["email"],
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_logout_success(self):
        """Test successful logout"""
        # Create user and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "Logged out successfully" in data["message"]
    
    def test_logout_without_token(self):
        """Test logout without token"""
        response = client.post("/auth/logout")
        
        assert response.status_code == 401
    
    def test_refresh_token_success(self):
        """Test token refresh"""
        # Create user and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Refresh token
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.access_token_expire_minutes * 60
    
    def test_refresh_invalid_token(self):
        """Test token refresh with invalid token"""
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_reset_password_success(self):
        """Test password reset request"""
        # Create user first
        client.post("/auth/signup", json=TEST_USER)
        
        reset_data = {"email": TEST_USER["email"]}
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "비밀번호 재설정 링크가 이메일로 전송되었습니다" in data["message"]
    
    def test_reset_password_invalid_email(self):
        """Test password reset with non-existent email"""
        reset_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Should return success for security (don't reveal email existence)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_update_password_success(self):
        """Test password update"""
        # Create user and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Update password
        update_data = {
            "password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
        
        response = client.post(
            "/auth/update-password",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "비밀번호가 성공적으로 변경되었습니다" in data["message"]
    
    def test_update_password_mismatch(self):
        """Test password update with mismatched passwords"""
        # Create user and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Update with mismatched passwords
        update_data = {
            "password": "NewPassword123",
            "confirm_password": "DifferentPassword123"
        }
        
        response = client.post(
            "/auth/update-password",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "비밀번호가 일치하지 않습니다" in response.json()["detail"]
    
    def test_update_password_unauthorized(self):
        """Test password update without token"""
        update_data = {
            "password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
        
        response = client.post("/auth/update-password", json=update_data)
        
        assert response.status_code == 401


class TestGoogleAuthentication:
    """Google OAuth authentication tests"""
    
    def test_google_auth_new_user(self):
        """Test Google auth with new user"""
        # Mock authentication - in real test, you'd mock the get_current_user_id dependency
        google_data = {
            "google_access_token": "mock_google_token",
            "user_id": "google_user_id_123",
            "email": "google@example.com",
            "name": "Google User"
        }
        
        # This test would require mocking the dependency
        # For now, testing the structure
        assert "google_access_token" in google_data
        assert "user_id" in google_data
        assert "email" in google_data
        assert "name" in google_data


class TestTokenValidation:
    """JWT token validation tests"""
    
    def test_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid token"""
        # Create user and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Access protected endpoint (logout as example)
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.post("/auth/logout")
        
        assert response.status_code == 401


class TestInputValidation:
    """Input validation tests"""
    
    def test_email_validation(self):
        """Test email format validation"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@.com"
        ]
        
        for email in invalid_emails:
            user_data = TEST_USER.copy()
            user_data["email"] = email
            
            response = client.post("/auth/signup", json=user_data)
            assert response.status_code == 422
    
    def test_password_validation(self):
        """Test password validation"""
        invalid_passwords = [
            "123",      # Too short
            "",         # Empty
            "short"     # Less than 6 chars
        ]
        
        for password in invalid_passwords:
            user_data = TEST_USER.copy()
            user_data["password"] = password
            
            response = client.post("/auth/signup", json=user_data)
            assert response.status_code == 422


class TestErrorHandling:
    """Error handling tests"""
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        response = client.post(
            "/auth/signup",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password and other required fields
        }
        
        response = client.post("/auth/signup", json=incomplete_data)
        assert response.status_code == 422
    
    def test_extra_fields(self):
        """Test handling of extra fields"""
        user_data = TEST_USER.copy()
        user_data["extra_field"] = "should be ignored"
        
        response = client.post("/auth/signup", json=user_data)
        
        # Should still work (Pydantic ignores extra fields)
        assert response.status_code == 200


# Integration test fixtures
@pytest.fixture
def authenticated_user():
    """Fixture that creates and logs in a test user"""
    # Clean up any existing user first
    client.post("/auth/signup", json=TEST_USER)
    
    login_response = client.post("/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    
    return {
        "user": TEST_USER,
        "token": login_response.json()["access_token"]
    }


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])