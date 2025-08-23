import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserProfile from './UserProfile';

export default function Header() {
  const location = useLocation();
  const { user } = useAuth();

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <h2>메멘토 박스</h2>
        </Link>
        
        <div className="header-right">
          <nav className="nav">
            <Link 
              to="/photos" 
              className={`nav-link ${location.pathname === '/photos' ? 'active' : ''}`}
            >
              사진
            </Link>
            <Link 
              to="/conversation" 
              className={`nav-link ${location.pathname === '/conversation' ? 'active' : ''}`}
            >
              대화
            </Link>
            <Link 
              to="/reports" 
              className={`nav-link ${location.pathname === '/reports' ? 'active' : ''}`}
            >
              리포트
            </Link>
          </nav>
          
          {user && <UserProfile />}
        </div>
      </div>
    </header>
  );
}