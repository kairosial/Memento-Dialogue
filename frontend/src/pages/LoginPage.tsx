import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import GoogleLoginButton from '../components/GoogleLoginButton';
import '../components/GoogleLoginButton.css';
import './LoginPage.css';

export default function LoginPage() {
  const { user, loading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLogging, setIsLogging] = useState(false);

  // Redirect if already authenticated
  if (!loading && user) {
    return <Navigate to="/" replace />;
  }

  const handleLoginSuccess = () => {
    setError(null);
    setIsLogging(false);
    // Navigation will happen automatically due to auth state change
  };

  const handleLoginError = (errorMessage: string) => {
    setError(errorMessage);
    setIsLogging(false);
  };


  if (loading) {
    return (
      <div className="login-page loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>로그인 상태를 확인하는 중...</p>
        </div>
      </div>
    );
  }

  console.log('LoginPage render - user:', user, 'loading:', loading);

  return (
    <div style={{ padding: '20px', minHeight: '100vh', backgroundColor: '#f0f0f0' }}>
      <h1 style={{ color: '#333', textAlign: 'center' }}>메멘토 박스</h1>
      <p style={{ color: '#666', textAlign: 'center' }}>사진으로 시작하는 추억 여행과 자연스러운 인지 기능 점검</p>
      
      <div style={{ maxWidth: '400px', margin: '40px auto', padding: '40px', backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <h2 style={{ color: '#333', marginBottom: '20px' }}>시작하기</h2>
        <p style={{ color: '#666', marginBottom: '30px' }}>구글 계정으로 간편하게 로그인하세요.</p>
        
        <GoogleLoginButton
          onSuccess={handleLoginSuccess}
          onError={handleLoginError}
          disabled={isLogging}
          className="primary-login-button"
        />
        
        {error && (
          <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#fee', borderRadius: '6px', color: '#c00' }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}