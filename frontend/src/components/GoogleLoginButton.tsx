import { useGoogleLogin } from '@react-oauth/google';
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface GoogleLoginButtonProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
  className?: string;
  disabled?: boolean;
}

export default function GoogleLoginButton({
  onSuccess,
  onError,
  className = '',
  disabled = false
}: GoogleLoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { signInWithGoogle } = useAuth();

  let login: (() => void) | null = null;
  
  try {
    login = useGoogleLogin({
      onSuccess: async (tokenResponse) => {
        setIsLoading(true);
        try {
          console.log('Google tokenResponse:', tokenResponse);
          
          // Google access token을 사용하여 사용자 정보 가져오기
          const userInfoResponse = await fetch(
            `https://www.googleapis.com/oauth2/v2/userinfo?access_token=${tokenResponse.access_token}`
          );
          
          if (!userInfoResponse.ok) {
            throw new Error('Failed to get user info from Google');
          }
          
          const userInfo = await userInfoResponse.json();
          console.log('Google userInfo:', userInfo);
          
          // ID token이 있는지 확인 (없다면 access token 사용)
          const token = (tokenResponse as any).id_token || tokenResponse.access_token;
          console.log('Using token:', token ? 'token available' : 'no token');
          
          // Supabase에 로그인 시도
          await signInWithGoogle(token, userInfo);
          onSuccess?.();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '구글 로그인 중 오류가 발생했습니다';
          onError?.(errorMessage);
        } finally {
          setIsLoading(false);
        }
      },
      onError: () => {
        const errorMessage = '구글 로그인을 실행할 수 없습니다. 다시 시도해 주세요.';
        onError?.(errorMessage);
      },
      scope: 'openid email profile'
    });
  } catch (error) {
    console.warn('Google OAuth not properly configured:', error);
    login = () => {
      onError?.('Google OAuth가 설정되지 않았습니다. 환경 변수를 확인해주세요.');
    };
  }

  const handleClick = () => {
    if (!disabled && !isLoading && login) {
      login();
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  };

  return (
    <button
      onClick={handleClick}
      onKeyDown={handleKeyPress}
      disabled={disabled || isLoading}
      className={`google-login-button ${className} ${isLoading ? 'loading' : ''}`}
      type="button"
      aria-label={isLoading ? '구글 로그인 진행 중...' : '구글 계정으로 로그인'}
      role="button"
      tabIndex={0}
    >
      <div className="button-content">
        {!isLoading && (
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            aria-hidden="true"
            className="google-icon"
          >
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
        )}
        
        {isLoading && (
          <div className="loading-spinner" aria-hidden="true">
            <div className="spinner"></div>
          </div>
        )}
        
        <span className="button-text">
          {isLoading ? '로그인 중...' : '구글 계정으로 로그인'}
        </span>
      </div>
    </button>
  );
}