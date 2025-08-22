import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  ConversationState, 
  ConversationMessage, 
  ConversationSession, 
  PhotoContext,
  WebSocketMessage,
  ConversationResponse 
} from '../types/conversation';
import { useWebSocket } from './useWebSocket';

interface UseConversationOptions {
  userId: string;
  initialPhotos?: PhotoContext[];
  websocketUrl?: string;
  onSessionComplete?: (session: ConversationSession) => void;
  onError?: (error: string) => void;
}

interface UseConversationReturn {
  // 상태
  state: ConversationState;
  
  // 액션
  startSession: (photos: PhotoContext[]) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  endSession: () => Promise<void>;
  selectPhoto: (photoIndex: number) => void;
  
  // WebSocket 제어
  reconnect: () => void;
  disconnect: () => void;
}

export function useConversation({
  userId,
  initialPhotos = [],
  websocketUrl = 'ws://localhost:8000/api/v1/ws',
  onSessionComplete,
  onError
}: UseConversationOptions): UseConversationReturn {
  
  const [state, setState] = useState<ConversationState>({
    session: null,
    messages: [],
    currentPhoto: null,
    isConnected: false,
    isTyping: false,
    connectionStatus: 'disconnected'
  });

  const sessionRef = useRef<string | null>(null);
  const messageQueue = useRef<string[]>([]);

  // WebSocket 메시지 처리
  const handleWebSocketMessage = useCallback((wsMessage: WebSocketMessage) => {
    console.log('Received WebSocket message:', wsMessage);

    switch (wsMessage.type) {
      case 'conversation_response':
        if (wsMessage.content && wsMessage.session_id) {
          const newMessage: ConversationMessage = {
            id: `msg_${Date.now()}_${Math.random()}`,
            type: 'assistant',
            content: wsMessage.content,
            timestamp: wsMessage.timestamp || new Date().toISOString(),
            responseType: wsMessage.response_type as any,
            metadata: wsMessage.metadata || {}
          };

          setState(prev => ({
            ...prev,
            messages: [...prev.messages, newMessage],
            isTyping: false,
            session: wsMessage.session_info ? {
              sessionId: wsMessage.session_info.session_id,
              userId: userId,
              photoIds: prev.session?.photoIds || [],
              turnCount: wsMessage.session_info.turn_count,
              currentState: wsMessage.session_info.current_state,
              cistProgress: wsMessage.session_info.cist_progress || {},
              cistScores: wsMessage.session_info.cist_scores || {},
              isComplete: wsMessage.session_info.is_complete || false,
              startTime: prev.session?.startTime || new Date().toISOString(),
              lastActivity: new Date().toISOString()
            } : prev.session
          }));

          // 세션 완료 체크
          if (wsMessage.session_info?.is_complete) {
            onSessionComplete?.(prev => prev.session!);
          }
        }
        break;

      case 'conversation_error':
        setState(prev => ({
          ...prev,
          isTyping: false,
          lastError: wsMessage.error || '알 수 없는 오류가 발생했습니다.'
        }));
        onError?.(wsMessage.error || '대화 오류');
        break;

      case 'user_joined':
      case 'user_left':
        // 사용자 참여/이탈 처리 (필요시)
        break;

      case 'pong':
        // Ping/pong 응답 (연결 상태 확인)
        break;

      default:
        console.log('Unknown message type:', wsMessage.type);
    }
  }, [userId, onSessionComplete, onError]);

  // WebSocket 연결 상태 처리
  const handleWebSocketConnect = useCallback(() => {
    setState(prev => ({
      ...prev,
      isConnected: true,
      connectionStatus: 'connected',
      lastError: undefined
    }));

    // 대기 중인 메시지들 전송
    if (messageQueue.current.length > 0) {
      messageQueue.current.forEach(content => {
        sendMessage(content);
      });
      messageQueue.current = [];
    }
  }, []);

  const handleWebSocketDisconnect = useCallback(() => {
    setState(prev => ({
      ...prev,
      isConnected: false,
      connectionStatus: 'disconnected',
      isTyping: false
    }));
  }, []);

  const handleWebSocketError = useCallback((error: Event) => {
    setState(prev => ({
      ...prev,
      connectionStatus: 'error',
      lastError: '연결 오류가 발생했습니다.',
      isTyping: false
    }));
    onError?.('WebSocket 연결 오류');
  }, [onError]);

  // WebSocket 훅 사용
  const { sendMessage: sendWebSocketMessage, isConnected, reconnect, disconnect } = useWebSocket({
    url: websocketUrl,
    userId,
    sessionId: sessionRef.current || undefined,
    onMessage: handleWebSocketMessage,
    onConnect: handleWebSocketConnect,
    onDisconnect: handleWebSocketDisconnect,
    onError: handleWebSocketError,
    autoReconnect: true,
    maxReconnectAttempts: 5
  });

  // 세션 시작
  const startSession = useCallback(async (photos: PhotoContext[]) => {
    try {
      const sessionId = `session_${userId}_${Date.now()}`;
      sessionRef.current = sessionId;

      const newSession: ConversationSession = {
        sessionId,
        userId,
        photoIds: photos.map(p => p.id),
        turnCount: 0,
        currentState: 'init',
        cistProgress: {},
        cistScores: {},
        isComplete: false,
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString()
      };

      setState(prev => ({
        ...prev,
        session: newSession,
        messages: [],
        currentPhoto: photos[0] || null
      }));

      // 초기 환영 메시지 (시뮬레이션)
      const welcomeMessage: ConversationMessage = {
        id: `msg_welcome_${Date.now()}`,
        type: 'assistant',
        content: '안녕하세요! 함께 사진을 보며 소중한 추억을 나눠보아요. 사진을 보시면서 떠오르는 생각이나 기억을 자유롭게 말씀해 주세요.',
        timestamp: new Date().toISOString(),
        responseType: 'photo_conversation',
        metadata: { conversation_type: 'welcome' }
      };

      setState(prev => ({
        ...prev,
        messages: [welcomeMessage]
      }));

    } catch (error) {
      console.error('Failed to start session:', error);
      onError?.('세션 시작 실패');
    }
  }, [userId, onError]);

  // 메시지 전송
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // 사용자 메시지 즉시 추가
    const userMessage: ConversationMessage = {
      id: `msg_user_${Date.now()}`,
      type: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isTyping: true
    }));

    // WebSocket이 연결되지 않은 경우 대기열에 추가
    if (!isConnected) {
      messageQueue.current.push(content);
      setState(prev => ({ ...prev, isTyping: false }));
      return;
    }

    try {
      // 현재 세션 정보와 함께 메시지 전송
      const messageData = {
        type: 'chat_message',
        content: content.trim(),
        session_id: sessionRef.current,
        user_id: userId,
        photo_context: state.currentPhoto?.description || state.currentPhoto?.name,
        photo_ids: state.session?.photoIds || [],
        conversation_history: state.messages.slice(-10), // 최근 10개 메시지만
        cist_progress: state.session?.cistProgress || {},
        cist_scores: state.session?.cistScores || {},
        turn_count: state.session?.turnCount || 0,
        timestamp: new Date().toISOString()
      };

      sendWebSocketMessage(messageData);

    } catch (error) {
      console.error('Failed to send message:', error);
      setState(prev => ({
        ...prev,
        isTyping: false,
        lastError: '메시지 전송 실패'
      }));
      onError?.('메시지 전송 실패');
    }
  }, [isConnected, state.currentPhoto, state.session, state.messages, userId, sendWebSocketMessage, onError]);

  // 세션 종료
  const endSession = useCallback(async () => {
    try {
      if (state.session) {
        // 세션 종료 메시지 (선택사항)
        const endMessage: ConversationMessage = {
          id: `msg_end_${Date.now()}`,
          type: 'system',
          content: '대화가 종료되었습니다. 함께해 주셔서 감사합니다!',
          timestamp: new Date().toISOString(),
          responseType: 'evaluation_complete'
        };

        setState(prev => ({
          ...prev,
          messages: [...prev.messages, endMessage],
          session: prev.session ? { ...prev.session, isComplete: true } : null
        }));
      }

      sessionRef.current = null;
    } catch (error) {
      console.error('Failed to end session:', error);
      onError?.('세션 종료 실패');
    }
  }, [state.session, onError]);

  // 사진 선택
  const selectPhoto = useCallback((photoIndex: number) => {
    if (initialPhotos[photoIndex]) {
      setState(prev => ({
        ...prev,
        currentPhoto: initialPhotos[photoIndex]
      }));
    }
  }, [initialPhotos]);

  // 연결 상태 동기화
  useEffect(() => {
    setState(prev => ({
      ...prev,
      isConnected,
      connectionStatus: prev.connectionStatus === 'error' ? 'error' : (isConnected ? 'connected' : 'disconnected')
    }));
  }, [isConnected]);

  return {
    state,
    startSession,
    sendMessage,
    endSession,
    selectPhoto,
    reconnect,
    disconnect
  };
}