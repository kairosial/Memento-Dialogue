import { useState, useEffect, useRef, useCallback } from 'react';
import type { WebSocketMessage } from '../types/conversation';

interface UseWebSocketOptions {
  url: string;
  userId?: string;
  sessionId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  socket: WebSocket | null;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (message: any) => void;
  disconnect: () => void;
  reconnect: () => void;
  lastError: string | null;
}

export function useWebSocket({
  url,
  userId,
  sessionId,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  autoReconnect = true,
  maxReconnectAttempts = 5
}: UseWebSocketOptions): UseWebSocketReturn {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastError, setLastError] = useState<string | null>(null);
  
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      setLastError(null);

      // WebSocket URL 구성
      const wsUrl = new URL(url);
      if (userId) wsUrl.searchParams.set('user_id', userId);
      if (sessionId) wsUrl.searchParams.set('room_id', sessionId);

      const newSocket = new WebSocket(wsUrl.toString());

      newSocket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        onConnect?.();
      };

      newSocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          setLastError('메시지 파싱 오류');
        }
      };

      newSocket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        setSocket(null);
        onDisconnect?.();

        // 자동 재연결 시도
        if (shouldReconnect.current && autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000); // 지수 백오프
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        setLastError('연결 오류가 발생했습니다');
        onError?.(error);
      };

      setSocket(newSocket);
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
      setLastError('WebSocket 생성 실패');
    }
  }, [url, userId, sessionId, onMessage, onConnect, onDisconnect, onError, autoReconnect, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    shouldReconnect.current = false;
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    if (socket) {
      socket.close(1000, 'User disconnect');
    }
  }, [socket]);

  const reconnect = useCallback(() => {
    shouldReconnect.current = true;
    reconnectAttempts.current = 0;
    if (socket) {
      socket.close();
    }
    connect();
  }, [socket, connect]);

  const sendMessage = useCallback((message: any) => {
    if (socket && isConnected) {
      try {
        socket.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        setLastError('메시지 전송 실패');
      }
    } else {
      console.warn('WebSocket is not connected');
      setLastError('연결되지 않음');
    }
  }, [socket, isConnected]);

  // 컴포넌트 마운트 시 연결
  useEffect(() => {
    connect();

    // 컴포넌트 언마운트 시 정리
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [connect]);

  // ping 메시지로 연결 상태 유지
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 30000); // 30초마다 ping

    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    socket,
    isConnected,
    connectionStatus,
    sendMessage,
    disconnect,
    reconnect,
    lastError
  };
}