import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MessageList } from '../components/conversation/MessageList';
import { MessageInput } from '../components/conversation/MessageInput';
import { PhotoViewer } from '../components/conversation/PhotoViewer';
import { CISTProgressBar } from '../components/conversation/CISTProgressBar';
import { useConversation } from '../hooks/useConversation';
import type { PhotoContext } from '../types/conversation';
import { 
  Wifi, 
  WifiOff, 
  AlertCircle,
  Play,
  BarChart3
} from 'lucide-react';

// 모의 사진 데이터 (실제로는 Supabase에서 가져옴)
const MOCK_PHOTOS: PhotoContext[] = [
  {
    id: 'photo_1',
    url: 'https://images.unsplash.com/photo-1549291981-56d443d5e2c1?w=400',
    name: '가족 여행 사진',
    description: '지난 여름 바닷가에서 찍은 가족 사진입니다.',
    tags: ['가족', '여행', '바다'],
    uploadedAt: '2024-08-15T10:00:00Z'
  },
  {
    id: 'photo_2', 
    url: 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=400',
    name: '생일 파티',
    description: '할머니 생신을 축하하며 찍은 사진입니다.',
    tags: ['생일', '축하', '할머니'],
    uploadedAt: '2024-08-10T15:30:00Z'
  },
  {
    id: 'photo_3',
    url: 'https://images.unsplash.com/photo-1543674892-7d64d45df18b?w=400', 
    name: '공원 산책',
    description: '동네 공원에서 산책하며 찍은 사진입니다.',
    tags: ['산책', '공원', '자연'],
    uploadedAt: '2024-08-05T09:15:00Z'
  }
];

export default function ConversationPage() {
  const { user } = useAuth();
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [isPhotoMinimized, setIsPhotoMinimized] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [sessionStarted, setSessionStarted] = useState(false);

  const {
    state,
    startSession,
    sendMessage,
    selectPhoto,
    reconnect
  } = useConversation({
    userId: user?.id || 'guest',
    initialPhotos: MOCK_PHOTOS,
    websocketUrl: 'ws://localhost:8000/api/v1/ws',
    onSessionComplete: (session) => {
      console.log('Session completed:', session);
      setShowProgress(true);
    },
    onError: (error) => {
      console.error('Conversation error:', error);
    }
  });

  // 세션 자동 시작
  useEffect(() => {
    if (user && !sessionStarted) {
      startSession(MOCK_PHOTOS);
      setSessionStarted(true);
    }
  }, [user, sessionStarted, startSession]);

  // 사진 변경 시 대화 컨텍스트 업데이트
  const handlePhotoChange = (index: number) => {
    setCurrentPhotoIndex(index);
    selectPhoto(index);
  };

  // 연결 상태 표시 컴포넌트
  const ConnectionStatus = () => {
    const getStatusColor = () => {
      switch (state.connectionStatus) {
        case 'connected': return 'text-green-600';
        case 'connecting': return 'text-yellow-600';
        case 'error': return 'text-red-600';
        default: return 'text-gray-400';
      }
    };

    const getStatusIcon = () => {
      switch (state.connectionStatus) {
        case 'connected': return <Wifi className="w-5 h-5" />;
        case 'error': return <WifiOff className="w-5 h-5" />;
        default: return <Wifi className="w-5 h-5" />;
      }
    };

    return (
      <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
        {getStatusIcon()}
        <span className="text-sm font-medium">
          {state.connectionStatus === 'connected' && '연결됨'}
          {state.connectionStatus === 'connecting' && '연결 중...'}
          {state.connectionStatus === 'disconnected' && '연결 끊어짐'}
          {state.connectionStatus === 'error' && '연결 오류'}
        </span>
      </div>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">로그인이 필요합니다</h2>
          <p className="text-gray-600">대화를 시작하려면 먼저 로그인해 주세요.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 헤더 */}
      <header className="bg-white border-b-2 border-gray-200 p-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">회상 대화</h1>
            <p className="text-gray-600">사진을 보며 소중한 추억을 나눠보세요</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <ConnectionStatus />
            
            <button
              onClick={() => setShowProgress(!showProgress)}
              className="p-3 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              aria-label="진행 상황 보기"
            >
              <BarChart3 className="w-6 h-6" />
            </button>
            
            {state.connectionStatus === 'error' && (
              <button
                onClick={reconnect}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                다시 연결
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 사이드바 - 사진 뷰어 */}
        <aside className={`bg-white border-r-2 border-gray-200 transition-all duration-300 ${
          isPhotoMinimized ? 'w-80' : 'w-96'
        }`}>
          <PhotoViewer
            photos={MOCK_PHOTOS}
            currentPhotoIndex={currentPhotoIndex}
            onPhotoChange={handlePhotoChange}
            isMinimized={isPhotoMinimized}
            onToggleMinimize={() => setIsPhotoMinimized(!isPhotoMinimized)}
            className="h-full border-none rounded-none"
          />
        </aside>

        {/* 메인 대화 영역 */}
        <main className="flex-1 flex flex-col">
          {/* CIST 진행 상황 (토글 가능) */}
          {showProgress && (
            <div className="border-b border-gray-200">
              <CISTProgressBar
                cistProgress={state.session?.cistProgress || {}}
                cistScores={state.session?.cistScores || {}}
                currentCategory={
                  state.messages
                    .filter(m => m.responseType === 'cist_question')
                    .pop()?.metadata?.cist_category
                }
                showDetails={false}
                className="border-none rounded-none"
              />
            </div>
          )}

          {/* 메시지 리스트 */}
          <MessageList
            messages={state.messages}
            isLoading={state.isTyping}
            error={state.lastError}
            autoScroll={true}
          />

          {/* 메시지 입력 */}
          <MessageInput
            onSendMessage={sendMessage}
            disabled={!state.isConnected || state.isTyping}
            isLoading={state.isTyping}
            placeholder="사진을 보시면서 떠오르는 생각이나 기억을 말씀해 주세요..."
            maxLength={500}
          />
        </main>
      </div>

      {/* 세션 완료 모달 (필요시) */}
      {state.session?.isComplete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Play className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">대화 완료!</h3>
              <p className="text-gray-600 mb-6">
                오늘의 회상 대화가 성공적으로 완료되었습니다. 
                소중한 추억을 함께 나누어 주셔서 감사합니다.
              </p>
              
              <CISTProgressBar
                cistProgress={state.session?.cistProgress || {}}
                cistScores={state.session?.cistScores || {}}
                showDetails={true}
                className="mb-6"
              />

              <div className="flex space-x-3">
                <button
                  onClick={() => window.location.href = '/reports'}
                  className="flex-1 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  결과 보기
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="flex-1 px-4 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  새 대화 시작
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}