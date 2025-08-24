import { memo } from 'react';
import type { ConversationMessage } from '../../types/conversation';
import { User, Bot, Clock, CheckCircle } from 'lucide-react';

interface MessageBubbleProps {
  message: ConversationMessage;
  isHighlighted?: boolean;
  showTimestamp?: boolean;
}

export const MessageBubble = memo(({ message, isHighlighted = false, showTimestamp = true }: MessageBubbleProps) => {
  const isUser = message.type === 'user';
  const isCISTQuestion = message.responseType === 'cist_question';
  
  const getMessageIcon = () => {
    if (isUser) return <User className="w-6 h-6" />;
    return <Bot className="w-6 h-6" />;
  };

  const getMessageStyle = () => {
    let baseStyle = "p-6 rounded-2xl max-w-4xl shadow-sm border-2 ";
    
    if (isUser) {
      baseStyle += "bg-blue-50 border-blue-200 ml-auto mr-4 ";
    } else {
      baseStyle += "bg-white border-gray-200 mr-auto ml-4 ";
      
      if (isCISTQuestion) {
        baseStyle += "ring-2 ring-orange-200 bg-orange-50 border-orange-300 ";
      }
    }
    
    if (isHighlighted) {
      baseStyle += "ring-4 ring-blue-300 ";
    }
    
    return baseStyle;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  return (
    <div className={`flex items-start mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* 아바타 (사용자 메시지가 아닐 때만) */}
      {!isUser && (
        <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center mr-4 ${
          isCISTQuestion ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-600'
        }`}>
          {getMessageIcon()}
        </div>
      )}
      
      <div className={getMessageStyle()}>
        {/* CIST 질문 표시기 */}
        {isCISTQuestion && (
          <div className="flex items-center mb-3 text-orange-700">
            <CheckCircle className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">인지 기능 확인 질문</span>
          </div>
        )}
        
        {/* 메시지 내용 */}
        <div className={`text-lg leading-relaxed ${
          isUser ? 'text-blue-900' : 'text-gray-800'
        }`}>
          {message.content}
        </div>
        
        {/* 메타데이터 정보 (개발/디버깅용) */}
        {message.metadata?.question_source && (
          <div className="mt-3 text-xs text-gray-500 bg-gray-100 rounded px-2 py-1">
            출처: {message.metadata.question_source}
          </div>
        )}
        
        {/* 타임스탬프 */}
        {showTimestamp && (
          <div className="flex items-center mt-3 text-sm text-gray-500">
            <Clock className="w-4 h-4 mr-1" />
            {formatTimestamp(message.timestamp)}
          </div>
        )}
      </div>
      
      {/* 사용자 아바타 (사용자 메시지일 때) */}
      {isUser && (
        <div className="flex-shrink-0 w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center ml-4">
          {getMessageIcon()}
        </div>
      )}
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';