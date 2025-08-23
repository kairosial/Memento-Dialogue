import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import LogoutButton from './LogoutButton';
import './UserProfile.css';
import './LogoutButton.css';

export default function UserProfile() {
  const { user } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  if (!user) return null;

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const closeDropdown = () => {
    setIsDropdownOpen(false);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleDropdown();
    }
  };

  // Get user display name from metadata or email
  const displayName = user.user_metadata?.full_name || 
                     user.user_metadata?.name || 
                     user.email?.split('@')[0] || 
                     '사용자';
  
  const avatarUrl = user.user_metadata?.avatar_url || user.user_metadata?.picture;

  return (
    <div className="user-profile">
      <button
        onClick={toggleDropdown}
        onKeyDown={handleKeyPress}
        className="user-profile-trigger"
        aria-label="사용자 메뉴 열기"
        aria-expanded={isDropdownOpen}
        aria-haspopup="true"
      >
        <div className="user-avatar">
          {avatarUrl ? (
            <img 
              src={avatarUrl} 
              alt={`${displayName}의 프로필`}
              className="user-avatar-image"
            />
          ) : (
            <div className="user-avatar-placeholder">
              {displayName.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div className="user-info">
          <span className="user-name">{displayName}</span>
          <span className="user-email">{user.email}</span>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`dropdown-arrow ${isDropdownOpen ? 'open' : ''}`}
          aria-hidden="true"
        >
          <polyline points="6,9 12,15 18,9" />
        </svg>
      </button>

      {isDropdownOpen && (
        <>
          <div 
            className="user-profile-overlay" 
            onClick={closeDropdown}
            aria-hidden="true"
          />
          <div className="user-profile-dropdown" role="menu">
            <div className="dropdown-header">
              <div className="dropdown-user-info">
                <div className="dropdown-name">{displayName}</div>
                <div className="dropdown-email">{user.email}</div>
              </div>
            </div>
            
            <div className="dropdown-divider" />
            
            <div className="dropdown-actions">
              <div onClick={closeDropdown}>
                <LogoutButton 
                  variant="text" 
                  className="dropdown-logout"
                  showConfirmation={true}
                />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}