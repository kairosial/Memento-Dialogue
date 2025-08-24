import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="py-8">
      <h1 className="text-4xl text-gray-800 mb-4 text-center font-bold">메멘토 박스</h1>
      <p className="text-xl text-gray-600 text-center mb-8">사진으로 시작하는 추억 여행과 자연스러운 인지 기능 점검</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-12">
        <Link 
          to="/photos" 
          className="bg-white border-2 border-gray-200 rounded-xl p-8 text-center no-underline text-inherit transition-all hover:border-blue-600 hover:shadow-lg hover:-translate-y-1"
        >
          <h3 className="text-gray-800 text-2xl mb-2 font-semibold">사진 업로드</h3>
          <p className="text-gray-600 text-base m-0">추억의 사진을 올려보세요</p>
        </Link>
        
        <Link 
          to="/conversation" 
          className="bg-white border-2 border-gray-200 rounded-xl p-8 text-center no-underline text-inherit transition-all hover:border-blue-600 hover:shadow-lg hover:-translate-y-1"
        >
          <h3 className="text-gray-800 text-2xl mb-2 font-semibold">회상 대화</h3>
          <p className="text-gray-600 text-base m-0">사진을 보며 대화해보세요</p>
        </Link>
        
        <Link 
          to="/reports" 
          className="bg-white border-2 border-gray-200 rounded-xl p-8 text-center no-underline text-inherit transition-all hover:border-blue-600 hover:shadow-lg hover:-translate-y-1"
        >
          <h3 className="text-gray-800 text-2xl mb-2 font-semibold">인지 리포트</h3>
          <p className="text-gray-600 text-base m-0">대화 결과를 확인해보세요</p>
        </Link>
      </div>
    </div>
  );
}