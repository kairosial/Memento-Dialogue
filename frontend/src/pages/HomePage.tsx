import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="page-container">
      <h1>메멘토 박스</h1>
      <p>사진으로 시작하는 추억 여행과 자연스러운 인지 기능 점검</p>
      
      <div className="navigation-cards">
        <Link to="/photos" className="nav-card">
          <h3>사진 업로드</h3>
          <p>추억의 사진을 올려보세요</p>
        </Link>
        
        <Link to="/conversation" className="nav-card">
          <h3>회상 대화</h3>
          <p>사진을 보며 대화해보세요</p>
        </Link>
        
        <Link to="/reports" className="nav-card">
          <h3>인지 리포트</h3>
          <p>대화 결과를 확인해보세요</p>
        </Link>
      </div>
    </div>
  );
}