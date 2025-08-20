import { useEffect, useState } from 'react';

interface ErrorToastProps {
  message: string;
  isVisible: boolean;
  onClose: () => void;
  autoClose?: boolean;
  duration?: number;
}

export default function ErrorToast({
  message,
  isVisible,
  onClose,
  autoClose = true,
  duration = 5000
}: ErrorToastProps) {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setIsAnimating(true);
      
      if (autoClose) {
        const timer = setTimeout(() => {
          handleClose();
        }, duration);
        
        return () => clearTimeout(timer);
      }
    }
  }, [isVisible, autoClose, duration]);

  const handleClose = () => {
    setIsAnimating(false);
    setTimeout(onClose, 300); // Wait for animation to complete
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      handleClose();
    }
  };

  if (!isVisible && !isAnimating) return null;

  return (
    <div
      className={`error-toast ${isAnimating ? 'visible' : 'hidden'}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="toast-content">
        <div className="toast-icon" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="#FEE2E2"/>
            <path d="M15 9l-6 6M9 9l6 6" stroke="#DC2626" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        
        <div className="toast-message">
          <p>{message}</p>
        </div>
        
        <button
          onClick={handleClose}
          className="toast-close"
          aria-label="오류 메시지 닫기"
          type="button"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  );
}