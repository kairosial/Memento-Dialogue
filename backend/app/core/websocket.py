from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리를 위한 매니저 클래스"""
    
    def __init__(self):
        # 활성 연결들을 저장하는 딕셔너리 {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 채팅룸별 연결들을 저장하는 딕셔너리 {room_id: [connection_ids]}
        self.room_connections: Dict[str, List[str]] = {}
        # 연결 ID와 유저 정보를 매핑 {connection_id: user_info}
        self.connection_users: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None, room_id: str = None):
        """WebSocket 연결을 수락하고 관리 목록에 추가"""
        await websocket.accept()
        
        # 연결 정보 저장
        self.active_connections[connection_id] = websocket
        self.connection_users[connection_id] = {
            "user_id": user_id,
            "room_id": room_id
        }
        
        # 채팅룸이 지정된 경우 룸에 추가
        if room_id:
            if room_id not in self.room_connections:
                self.room_connections[room_id] = []
            self.room_connections[room_id].append(connection_id)
        
        logger.info(f"WebSocket connection established: {connection_id} (user: {user_id}, room: {room_id})")

    def disconnect(self, connection_id: str):
        """WebSocket 연결을 제거"""
        if connection_id in self.active_connections:
            # 채팅룸에서 제거
            user_info = self.connection_users.get(connection_id, {})
            room_id = user_info.get("room_id")
            
            if room_id and room_id in self.room_connections:
                if connection_id in self.room_connections[room_id]:
                    self.room_connections[room_id].remove(connection_id)
                    # 빈 방은 제거
                    if not self.room_connections[room_id]:
                        del self.room_connections[room_id]
            
            # 연결 정보 제거
            del self.active_connections[connection_id]
            del self.connection_users[connection_id]
            
            logger.info(f"WebSocket connection removed: {connection_id}")

    async def send_personal_message(self, message: str, connection_id: str):
        """특정 연결에 개인 메시지 전송"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast_to_room(self, message: dict, room_id: str, exclude_connection: str = None):
        """특정 채팅룸의 모든 연결에 메시지 브로드캐스트"""
        if room_id not in self.room_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_connections = []
        
        for connection_id in self.room_connections[room_id]:
            if exclude_connection and connection_id == exclude_connection:
                continue
                
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
        
        # 실패한 연결들을 정리
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

    async def broadcast_to_all(self, message: dict, exclude_connection: str = None):
        """모든 활성 연결에 메시지 브로드캐스트"""
        message_str = json.dumps(message)
        disconnected_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            if exclude_connection and connection_id == exclude_connection:
                continue
                
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # 실패한 연결들을 정리
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

    def get_room_connections(self, room_id: str) -> List[str]:
        """특정 룸의 연결 목록 반환"""
        return self.room_connections.get(room_id, [])

    def get_connection_count(self) -> int:
        """총 활성 연결 수 반환"""
        return len(self.active_connections)

    def get_room_count(self) -> int:
        """총 활성 룸 수 반환"""
        return len(self.room_connections)


# 전역 ConnectionManager 인스턴스
manager = ConnectionManager()