import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface LogoutButtonProps {
  className?: string;
  showConfirmation?: boolean;
  variant?: 'button' | 'text';
}

export default function LogoutButton({ 
  className = '', 
  showConfirmation = true,
  variant = 'button'
}: LogoutButtonProps) {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const { signOut, isLoggingOut } = useAuth();

  const handleLogoutClick = () => {
    if (showConfirmation) {
      setShowConfirmDialog(true);
    } else {
      executeLogout();
    }
  };

  const executeLogout = async () => {
    setShowConfirmDialog(false);
    try {
      console.log('LogoutButton: Starting logout process...');
      await signOut();
      console.log('LogoutButton: Logout process completed');
    } catch (error) {
      console.error('LogoutButton: Logout failed:', error);
      // Show error message to user if needed
      alert('로그아웃 중 오류가 발생했습니다. 페이지를 새로고침해주세요.');
    }
  };

  const handleCancel = () => {
    setShowConfirmDialog(false);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleLogoutClick();
    }
  };

  if (showConfirmDialog) {
    return (
      <div className="logout-confirmation-overlay" onClick={handleCancel}>
        <div className="logout-confirmation-dialog" onClick={(e) => e.stopPropagation()}>
          <h3>로그아웃 확인</h3>
          <p>정말 로그아웃하시겠습니까?</p>
          <div className="logout-confirmation-buttons">
            <button
              onClick={executeLogout}
              disabled={isLoggingOut}
              className="logout-confirm-btn"
            >
              {isLoggingOut ? '로그아웃 중...' : '로그아웃'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isLoggingOut}
              className="logout-cancel-btn"
            >
              취소
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'text') {
    return (
      <button
        onClick={handleLogoutClick}
        onKeyDown={handleKeyPress}
        disabled={isLoggingOut}
        className={`logout-text-button ${className}`}
        type="button"
        aria-label={isLoggingOut ? '로그아웃 처리 중...' : '로그아웃'}
      >
        {isLoggingOut ? '로그아웃 중...' : '로그아웃'}
      </button>
    );
  }

  return (
    <button
      onClick={handleLogoutClick}
      onKeyDown={handleKeyPress}
      disabled={isLoggingOut}
      className={`logout-button ${className} ${isLoggingOut ? 'loading' : ''}`}
      type="button"
      aria-label={isLoggingOut ? '로그아웃 처리 중...' : '로그아웃'}
    >
      <div className="logout-button-content">
        {!isLoggingOut && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            className="logout-icon"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16,17 21,12 16,7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        )}
        
        {isLoggingOut && (
          <div className="logout-loading-spinner" aria-hidden="true">
            <div className="spinner"></div>
          </div>
        )}
        
        <span className="logout-button-text">
          {isLoggingOut ? '로그아웃 중...' : '로그아웃'}
        </span>
      </div>
    </button>
  );
}