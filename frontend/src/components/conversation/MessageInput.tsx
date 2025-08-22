import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Loader2, Mic, MicOff } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export function MessageInput({ 
  onSendMessage, 
  disabled = false, 
  isLoading = false,
  placeholder = "메시지를 입력하세요...",
  maxLength = 500
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled && !isLoading) {
      onSendMessage(trimmedMessage);
      setMessage('');
      
      // 텍스트 영역 높이 리셋
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter 키로 전송 (Shift+Enter는 줄바꿈)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setMessage(value);
      
      // 텍스트 영역 자동 높이 조절
      const textarea = e.target;
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  const handleVoiceToggle = () => {
    // TODO: 음성 인식 기능 구현
    setIsRecording(!isRecording);
    console.log('Voice recording toggle:', !isRecording);
  };

  const canSend = message.trim().length > 0 && !disabled && !isLoading;

  return (
    <div className="bg-white border-t-2 border-gray-200 p-6">
      <div className="max-w-4xl mx-auto">
        {/* 입력 영역 */}
        <div className="flex items-end space-x-4">
          {/* 음성 인식 버튼 */}
          <button
            type="button"
            onClick={handleVoiceToggle}
            disabled={disabled}
            className={`flex-shrink-0 w-14 h-14 rounded-full flex items-center justify-center transition-all duration-200 ${
              isRecording 
                ? 'bg-red-500 text-white hover:bg-red-600' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            aria-label={isRecording ? '녹음 중지' : '음성 입력'}
          >
            {isRecording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          </button>

          {/* 텍스트 입력 영역 */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-2xl resize-none 
                       focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none
                       disabled:bg-gray-100 disabled:cursor-not-allowed
                       placeholder-gray-500"
              style={{ minHeight: '56px' }}
            />
            
            {/* 글자 수 표시 */}
            <div className="absolute right-3 bottom-2 text-xs text-gray-400">
              {message.length}/{maxLength}
            </div>
          </div>

          {/* 전송 버튼 */}
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend}
            className={`flex-shrink-0 w-14 h-14 rounded-full flex items-center justify-center transition-all duration-200 ${
              canSend
                ? 'bg-blue-500 text-white hover:bg-blue-600 transform hover:scale-105' 
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
            aria-label="메시지 전송"
          >
            {isLoading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <Send className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* 음성 인식 상태 표시 */}
        {isRecording && (
          <div className="mt-4 flex items-center justify-center text-red-600">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">음성을 듣고 있습니다...</span>
            </div>
          </div>
        )}

        {/* 도움말 텍스트 */}
        <div className="mt-3 text-center text-sm text-gray-500">
          Enter로 전송 • Shift+Enter로 줄바꿈 • 음성 버튼으로 말하기
        </div>
      </div>
    </div>
  );
}