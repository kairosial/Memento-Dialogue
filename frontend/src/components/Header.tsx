import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserProfile from './UserProfile';

export default function Header() {
  const location = useLocation();
  const { user } = useAuth();

  return (
    <header className="bg-blue-600 text-white py-4 shadow-lg">
      <div className="max-w-6xl mx-auto px-4 flex justify-between items-center">
        <Link to="/" className="text-white no-underline">
          <h2 className="m-0 text-2xl font-bold">메멘토 박스</h2>
        </Link>
        
        <div className="flex items-center gap-8">
          <nav className="flex gap-8">
            <Link 
              to="/photos" 
              className={`text-white no-underline text-lg font-medium px-4 py-2 rounded transition-colors ${
                location.pathname === '/photos' 
                  ? 'bg-white bg-opacity-20' 
                  : 'hover:bg-white hover:bg-opacity-20'
              }`}
            >
              사진
            </Link>
            <Link 
              to="/conversation" 
              className={`text-white no-underline text-lg font-medium px-4 py-2 rounded transition-colors ${
                location.pathname === '/conversation' 
                  ? 'bg-white bg-opacity-20' 
                  : 'hover:bg-white hover:bg-opacity-20'
              }`}
            >
              대화
            </Link>
            <Link 
              to="/reports" 
              className={`text-white no-underline text-lg font-medium px-4 py-2 rounded transition-colors ${
                location.pathname === '/reports' 
                  ? 'bg-white bg-opacity-20' 
                  : 'hover:bg-white hover:bg-opacity-20'
              }`}
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