from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..core.websocket import manager
from ..services.conversation_graph import ConversationGraph
from ..core.config import settings
import json
import uuid
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# ConversationGraph 인스턴스 생성
conversation_graph = None

def get_conversation_graph():
    global conversation_graph
    if conversation_graph is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        conversation_graph = ConversationGraph(openai_api_key, redis_url)
    
    return conversation_graph


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str = Query(None),
    room_id: str = Query(None)
):
    """
    WebSocket 연결 엔드포인트
    
    Query Parameters:
    - user_id: 사용자 ID (선택사항)
    - room_id: 채팅룸 ID (선택사항)
    """
    connection_id = str(uuid.uuid4())
    
    try:
        # WebSocket 연결 수락 및 관리자에 등록
        await manager.connect(websocket, connection_id, user_id, room_id)
        
        # 연결 성공 메시지 전송
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "message": "WebSocket connection established successfully"
        }))
        
        # 채팅룸 정보가 있다면 룸 참여 알림
        if room_id:
            await manager.broadcast_to_room(
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "room_id": room_id,
                    "message": f"User {user_id} joined the room"
                },
                room_id,
                exclude_connection=connection_id
            )
        
        # 메시지 수신 루프
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                
                # 메시지 타입별 처리
                if message_type == "chat_message":
                    await handle_chat_message(message_data, connection_id, user_id, room_id)
                elif message_type == "ping":
                    await handle_ping(websocket, connection_id)
                elif message_type == "join_room":
                    await handle_join_room(message_data, connection_id, user_id)
                elif message_type == "leave_room":
                    await handle_leave_room(message_data, connection_id, user_id)
                else:
                    # 알 수 없는 메시지 타입
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }),
                        connection_id
                    )
                    
            except json.JSONDecodeError:
                # JSON 파싱 오류
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    connection_id
                )
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Failed to process message"
                    }),
                    connection_id
                )
                
    except WebSocketDisconnect:
        # 클라이언트 연결 해제
        logger.info(f"WebSocket disconnected: {connection_id}")
        
        # 채팅룸에서 나가는 알림
        if room_id:
            await manager.broadcast_to_room(
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "room_id": room_id,
                    "message": f"User {user_id} left the room"
                },
                room_id
            )
        
        # 연결 관리자에서 제거
        manager.disconnect(connection_id)
    
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


async def handle_chat_message(message_data: dict, connection_id: str, user_id: str, room_id: str):
    """채팅 메시지 처리 - LangGraph 통합"""
    content = message_data.get("content", "")
    
    if not content.strip():
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "Message content cannot be empty"
            }),
            connection_id
        )
        return
    
    try:
        # ConversationGraph 인스턴스 가져오기
        graph = get_conversation_graph()
        
        # 세션 정보 구성 (메타데이터에서 추출 또는 기본값 사용)
        session_id = message_data.get("session_id", room_id or connection_id)
        photo_context = message_data.get("photo_context")
        conversation_history = message_data.get("conversation_history", [])
        cist_progress = message_data.get("cist_progress", {})
        cist_scores = message_data.get("cist_scores", {})
        turn_count = message_data.get("turn_count", 0)
        photo_ids = message_data.get("photo_ids", [])
        
        # LangGraph로 대화 처리
        result = await graph.process_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=content,
            photo_context=photo_context,
            conversation_history=conversation_history,
            cist_progress=cist_progress,
            cist_scores=cist_scores,
            turn_count=turn_count,
            photo_ids=photo_ids
        )
        
        if result["success"]:
            # 성공적인 응답 처리
            response_message = {
                "type": "conversation_response",
                "user_id": user_id,
                "session_id": session_id,
                "content": result["response"]["content"],
                "response_type": result["response"]["response_type"],
                "metadata": result["response"]["metadata"],
                "session_info": result["session_info"],
                "timestamp": message_data.get("timestamp")
            }
            
            # 비동기 처리 정보가 있다면 포함
            if result.get("async_info", {}).get("task_id"):
                response_message["async_task_id"] = result["async_info"]["task_id"]
            
        else:
            # 오류 응답 처리
            response_message = {
                "type": "conversation_error",
                "user_id": user_id,
                "session_id": session_id,
                "content": result["response"]["content"],
                "error": result.get("error", "Unknown error"),
                "timestamp": message_data.get("timestamp")
            }
        
        # 룸이 지정된 경우 해당 룸에 브로드캐스트, 아니면 개인 메시지
        if room_id:
            await manager.broadcast_to_room(response_message, room_id)
        else:
            await manager.send_personal_message(
                json.dumps(response_message),
                connection_id
            )
            
    except Exception as e:
        logger.error(f"Error in conversation processing: {e}")
        
        # 오류 시 폴백 응답
        error_message = {
            "type": "conversation_error",
            "user_id": user_id,
            "session_id": session_id,
            "content": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 말씀해 주시겠어요?",
            "error": str(e),
            "timestamp": message_data.get("timestamp")
        }
        
        await manager.send_personal_message(
            json.dumps(error_message),
            connection_id
        )


async def handle_ping(websocket: WebSocket, connection_id: str):
    """핑 메시지 처리 (연결 상태 확인)"""
    await websocket.send_text(json.dumps({
        "type": "pong",
        "connection_id": connection_id
    }))


async def handle_join_room(message_data: dict, connection_id: str, user_id: str):
    """룸 참여 처리"""
    target_room = message_data.get("room_id")
    
    if not target_room:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "room_id is required"
            }),
            connection_id
        )
        return
    
    # TODO: 룸 참여 로직 구현
    # 현재는 기본적인 알림만 처리
    await manager.broadcast_to_room(
        {
            "type": "user_joined",
            "user_id": user_id,
            "room_id": target_room,
            "message": f"User {user_id} joined the room"
        },
        target_room,
        exclude_connection=connection_id
    )


async def handle_leave_room(message_data: dict, connection_id: str, user_id: str):
    """룸 나가기 처리"""
    target_room = message_data.get("room_id")
    
    if not target_room:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "room_id is required"
            }),
            connection_id
        )
        return
    
    # TODO: 룸 나가기 로직 구현
    # 현재는 기본적인 알림만 처리
    await manager.broadcast_to_room(
        {
            "type": "user_left",
            "user_id": user_id,
            "room_id": target_room,
            "message": f"User {user_id} left the room"
        },
        target_room,
        exclude_connection=connection_id
    )


@router.get("/ws/status")
async def websocket_status():
    """WebSocket 상태 조회 API"""
    return {
        "success": True,
        "data": {
            "total_connections": manager.get_connection_count(),
            "active_rooms": manager.get_room_count(),
            "rooms": {
                room_id: len(connections) 
                for room_id, connections in manager.room_connections.items()
            }
        }
    }