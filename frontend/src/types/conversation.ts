// 대화 관련 타입 정의

export interface ConversationMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  photoId?: string;
  responseType?: 'photo_conversation' | 'cist_question' | 'followup_question' | 'evaluation_complete';
  metadata?: {
    cist_category?: string;
    question_source?: 'cache' | 'light_llm' | 'fallback';
    async_task_id?: string;
    awaiting_cist_answer?: boolean;
    [key: string]: any;
  };
}

export interface ConversationSession {
  sessionId: string;
  userId: string;
  photoIds: string[];
  turnCount: number;
  currentState: 'init' | 'photo_based_chat' | 'cist_evaluation' | 'async_processing' | 'completed';
  cistProgress: Record<string, boolean>;
  cistScores: Record<string, number>;
  isComplete: boolean;
  startTime: string;
  lastActivity: string;
}

export interface PhotoContext {
  id: string;
  url: string;
  name: string;
  description?: string;
  tags?: string[];
  uploadedAt: string;
}

export interface CISTResult {
  category: string;
  score: number;
  maxScore: number;
  passed: boolean;
}

export interface ConversationState {
  session: ConversationSession | null;
  messages: ConversationMessage[];
  currentPhoto: PhotoContext | null;
  isConnected: boolean;
  isTyping: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastError?: string;
}

// WebSocket 메시지 타입
export interface WebSocketMessage {
  type: 'chat_message' | 'conversation_response' | 'conversation_error' | 'user_joined' | 'user_left' | 'ping' | 'pong';
  user_id?: string;
  session_id?: string;
  content?: string;
  response_type?: string;
  metadata?: any;
  session_info?: any;
  async_task_id?: string;
  timestamp?: string;
  error?: string;
}

// API 응답 타입
export interface ConversationResponse {
  success: boolean;
  response: {
    content: string;
    response_type: string;
    metadata: any;
  };
  session_info: {
    session_id: string;
    turn_count: number;
    current_state: string;
    cist_progress: Record<string, boolean>;
    cist_scores: Record<string, number>;
    is_complete: boolean;
  };
  async_info?: {
    task_id: string;
    needs_processing: boolean;
  };
  error?: string;
}