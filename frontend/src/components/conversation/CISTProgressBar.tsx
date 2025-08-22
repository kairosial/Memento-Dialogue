import { memo } from 'react';
import { CheckCircle, Circle, Clock } from 'lucide-react';

interface CISTCategory {
  id: string;
  name: string;
  description: string;
  maxScore: number;
}

interface CISTProgressBarProps {
  cistProgress: Record<string, boolean>;
  cistScores: Record<string, number>;
  currentCategory?: string;
  showDetails?: boolean;
  className?: string;
}

// CIST 카테고리 정의
const CIST_CATEGORIES: CISTCategory[] = [
  {
    id: 'orientation_time',
    name: '시간 지남력',
    description: '현재 날짜와 시간 인식',
    maxScore: 4
  },
  {
    id: 'orientation_place',
    name: '장소 지남력',
    description: '현재 위치 인식',
    maxScore: 1
  },
  {
    id: 'memory_registration',
    name: '기억 등록',
    description: '새로운 정보 기억하기',
    maxScore: 3
  },
  {
    id: 'memory_recall',
    name: '기억 회상',
    description: '이전 정보 떠올리기',
    maxScore: 3
  },
  {
    id: 'memory_recognition',
    name: '기억 재인',
    description: '기억 정보 확인하기',
    maxScore: 4
  },
  {
    id: 'attention',
    name: '주의력',
    description: '집중력과 정신적 조작',
    maxScore: 1
  },
  {
    id: 'executive_function',
    name: '집행 기능',
    description: '언어 추론과 문제 해결',
    maxScore: 2
  },
  {
    id: 'language_naming',
    name: '언어 기능',
    description: '사물과 개념 이름대기',
    maxScore: 3
  }
];

export const CISTProgressBar = memo(({ 
  cistProgress, 
  cistScores, 
  currentCategory,
  showDetails = false,
  className = ""
}: CISTProgressBarProps) => {
  
  const completedCount = Object.values(cistProgress).filter(Boolean).length;
  const totalCount = CIST_CATEGORIES.length;
  const progressPercentage = (completedCount / totalCount) * 100;
  
  const totalScore = Object.values(cistScores).reduce((sum, score) => sum + score, 0);
  const maxTotalScore = CIST_CATEGORIES.reduce((sum, cat) => sum + cat.maxScore, 0);

  const getCategoryStatus = (categoryId: string) => {
    if (cistProgress[categoryId]) return 'completed';
    if (currentCategory === categoryId) return 'current';
    return 'pending';
  };

  const getCategoryIcon = (categoryId: string) => {
    const status = getCategoryStatus(categoryId);
    
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'current':
        return <Clock className="w-5 h-5 text-blue-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getCategoryStyle = (categoryId: string) => {
    const status = getCategoryStatus(categoryId);
    
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'current':
        return 'bg-blue-50 border-blue-200 text-blue-800 ring-2 ring-blue-300';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-600';
    }
  };

  if (!showDetails) {
    // 간단한 진행 바
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">인지 기능 확인 진행</span>
          <span className="text-sm text-gray-600">
            {completedCount} / {totalCount}
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-blue-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        {totalScore > 0 && (
          <div className="mt-2 text-center text-sm text-gray-600">
            총점: {totalScore.toFixed(1)} / {maxTotalScore}점
          </div>
        )}
      </div>
    );
  }

  // 상세 진행 정보
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-800">인지 기능 확인 진행 상황</h3>
          <div className="text-sm text-gray-600">
            {completedCount} / {totalCount} 완료
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
          <div 
            className="bg-gradient-to-r from-blue-500 to-green-500 h-4 rounded-full transition-all duration-500"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        <div className="flex justify-between text-xs text-gray-500">
          <span>시작</span>
          <span>{Math.round(progressPercentage)}% 완료</span>
          <span>완료</span>
        </div>
      </div>

      {/* 카테고리별 상세 정보 */}
      <div className="space-y-3">
        {CIST_CATEGORIES.map((category) => {
          const status = getCategoryStatus(category.id);
          const score = cistScores[category.id] || 0;
          
          return (
            <div
              key={category.id}
              className={`p-4 border-2 rounded-lg transition-all duration-200 ${getCategoryStyle(category.id)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getCategoryIcon(category.id)}
                  <div>
                    <h4 className="font-medium">{category.name}</h4>
                    <p className="text-sm opacity-75">{category.description}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  {status === 'completed' && (
                    <div className="text-sm font-medium">
                      {score.toFixed(1)} / {category.maxScore}
                    </div>
                  )}
                  {status === 'current' && (
                    <div className="text-sm font-medium">진행 중</div>
                  )}
                  {status === 'pending' && (
                    <div className="text-sm opacity-50">대기 중</div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 총점 표시 */}
      {totalScore > 0 && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-800">총 점수</span>
            <span className="text-xl font-bold text-blue-600">
              {totalScore.toFixed(1)} / {maxTotalScore}
            </span>
          </div>
          
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(totalScore / maxTotalScore) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
});

CISTProgressBar.displayName = 'CISTProgressBar';