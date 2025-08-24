import { useEffect, useRef, memo } from 'react';
import type { ConversationMessage } from '../../types/conversation';
import { MessageBubble } from './MessageBubble';
import { Loader2, AlertCircle } from 'lucide-react';

interface MessageListProps {
  messages: ConversationMessage[];
  isLoading?: boolean;
  error?: string | null;
  autoScroll?: boolean;
  highlightedMessageId?: string;
}

export const MessageList = memo(({ 
  messages, 
  isLoading = false, 
  error = null,
  autoScroll = true,
  highlightedMessageId
}: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 자동 스크롤
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end' 
      });
    }
  }, [messages.length, autoScroll]);

  // 빈 메시지 리스트 처리
  if (messages.length === 0 && !isLoading && !error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-xl font-medium text-gray-700 mb-2">
            대화를 시작해보세요
          </h3>
          <p className="text-gray-500 leading-relaxed">
            사진을 보며 떠오르는 추억이나 생각을 자유롭게 말씀해 주세요.
            AI가 함께 대화하며 소중한 기억들을 나누어드립니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto bg-gray-50 px-4 py-6"
      style={{ scrollBehavior: 'smooth' }}
    >
      <div className="max-w-5xl mx-auto">
        {/* 오류 메시지 */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-xl flex items-start">
            <AlertCircle className="w-6 h-6 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-red-800 font-medium mb-1">연결 오류</h4>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* 메시지 목록 */}
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            isHighlighted={message.id === highlightedMessageId}
            showTimestamp={true}
          />
        ))}

        {/* 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex justify-start mb-6">
            <div className="flex items-center space-x-4 ml-4">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-gray-600 animate-spin" />
              </div>
              <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center space-x-2 text-gray-600">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-sm">생각하고 있어요...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 스크롤 위치 참조 */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
});

MessageList.displayName = 'MessageList';