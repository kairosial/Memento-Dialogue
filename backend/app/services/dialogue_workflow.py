from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import os
from supabase import create_client, Client
import uuid
from datetime import datetime
from app.core.config import settings
from .dialogue_prompt import (
    ROUTER_PROMPT,
    STANDARD_RESPONSE_PROMPT,
    FALLBACK_PROMPT,
    CACHE_RETRIEVE_AND_EVALUATE_PROMPT
)

class WorkflowInput(TypedDict):
    """그래프 실행을 위해 외부에서 주입되는 초기 데이터"""
    conversation_id: str
    user_id: str
    user_message: str
    photo_context: Dict[str, Any]

class IntermediateState(TypedDict):
    """노드 간 결정에 사용되는 임시 데이터"""
    cache_score: Optional[float]
    routing_decision: str

class FinalOutput(TypedDict):
    """최종적으로 사용자에게 전달될 결과물"""
    response_text: str
    response_audio_url: Optional[str]

class GraphState(TypedDict):
    """전체 워크플로우를 관통하는 상태 객체"""
    input_data: WorkflowInput
    message_history: List[Dict[str, str]]
    intermediate: IntermediateState
    output: FinalOutput
    photo_info: Optional[Dict[str, Any]]  # 사진 정보 저장
    session_id: Optional[str]  # 세션 ID 저장
    _authenticated_client: Optional[Client]  # 인증된 Supabase 클라이언트
    turn_count: int  # 현재 턴 수 (conversation_order 기반)
    assessment_completed: Dict[str, bool]  # 평가 완료 상태 {"time_orientation": bool, "language_naming": bool}

class DialogueWorkflow:
    """LangGraph 기반 대화 워크플로우 시스템"""
    
    def __init__(self):
        # 필수 환경 변수 검증 (settings 사용)
        openai_key = settings.OPENAI_API_KEY
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_ANON_KEY
        
        # LangSmith 설정
        langsmith_tracing = settings.LANGSMITH_TRACING and settings.LANGSMITH_TRACING.lower() == "true"
        langsmith_project = settings.LANGSMITH_PROJECT or "memento-box-dialogue"
        
        # LangSmith 환경변수 설정 (LangChain이 자동으로 읽도록)
        if settings.LANGSMITH_TRACING:
            os.environ["LANGSMITH_TRACING"] = settings.LANGSMITH_TRACING
        if settings.LANGSMITH_API_KEY:
            os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        if settings.LANGSMITH_PROJECT:
            os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        if settings.LANGSMITH_ENDPOINT:
            os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not supabase_key:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")
        
        try:
            # LangSmith 메타데이터 설정
            langsmith_metadata = {
                "service": "dialogue_workflow",
                "version": "1.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            }
            
            self.llm_mini = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=openai_key,
                metadata=langsmith_metadata if langsmith_tracing else None
            )
            self.llm_nano = ChatOpenAI(
                model="gpt-4o-mini",
                max_tokens=256,
                api_key=openai_key,
                metadata=langsmith_metadata if langsmith_tracing else None
            )
            print(f"OpenAI LLM clients initialized successfully (LangSmith tracing: {langsmith_tracing})")
        except Exception as e:
            print(f"Failed to initialize OpenAI clients: {e}")
            raise
        
        try:
            # Supabase 클라이언트
            self.supabase: Client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_key
            )
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            raise
        
        try:
            # 워크플로우 구성
            self.app = self._build_workflow()
            print("LangGraph workflow compiled successfully")
        except Exception as e:
            print(f"Failed to build LangGraph workflow: {e}")
            raise
    
    def _build_workflow(self):
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(GraphState)
        
        # 노드 추가
        workflow.add_node("init_state", self.init_state_node)
        workflow.add_node("router", self.router_node)
        workflow.add_node("time_orientation", self.time_orientation_node)
        workflow.add_node("language_naming", self.language_naming_node)
        workflow.add_node("standard_response", self.standard_response_node)
        workflow.add_node("cache_retrieve", self.cache_retrieve_and_evaluate_node)
        workflow.add_node("fallback", self.fallback_node)
        
        # 진입점 설정
        workflow.set_entry_point("init_state")
        
        # 엣지 정의
        workflow.add_edge("init_state", "router")
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "time_orientation": "time_orientation",
                "language_naming": "language_naming", 
                "standard_chat": "standard_response",
                "assessment_chat": "cache_retrieve"
            }
        )
        workflow.add_edge("time_orientation", END)
        workflow.add_edge("language_naming", END)
        workflow.add_edge("standard_response", END)
        workflow.add_conditional_edges(
            "cache_retrieve",
            self._cache_decision,
            {
                "use_cache": END,
                "use_fallback": "fallback"
            }
        )
        workflow.add_edge("fallback", END)
        
        return workflow.compile()
    
    def init_state_node(self, state: GraphState) -> GraphState:
        """상태 초기화 노드: DB에서 대화 기록 및 사진 정보 조회"""
        conversation_id = state["input_data"]["conversation_id"]
        user_id = state["input_data"]["user_id"]
        photo_context = state["input_data"]["photo_context"]
        
        # 상태에서 인증된 클라이언트 가져오기
        client = state.get("_authenticated_client", self.supabase)
        
        print(f"🔍 상태 초기화: conversation_id={conversation_id}, user_id={user_id}")
        
        try:
            # 사진 정보 조회 (photo_context에 photo_id가 있는 경우)
            photo_info = None
            if photo_context.get("photo_id"):
                try:
                    photo_response = client.table("photos").select(
                        "id, filename, file_path, description, tags, location_name, photo_analyze_result"
                    ).eq("id", photo_context["photo_id"]).single().execute()
                    
                    if photo_response.data:
                        photo_info = photo_response.data
                        print(f"📷 사진 정보 로드됨: {photo_info}")
                except Exception as photo_error:
                    print(f"❌ 사진 정보 로드 실패: {photo_error}")
            
            # conversation_id를 session_id로 사용 (main.py에서 이미 세션 생성됨)
            session_id = conversation_id
            print(f"✅ 세션 ID 설정: {session_id}")
            
            # 해당 세션의 기존 대화 내역 조회
            conversations_response = client.table("conversations").select(
                "id, ai_output, user_input, conversation_order"
            ).eq("session_id", session_id).order("conversation_order").execute()
            
            print(f"💬 기존 대화 내역: {len(conversations_response.data) if conversations_response.data else 0}개")
            
            # 현재 턴 수 계산 (다음 conversation_order)
            current_turn = len(conversations_response.data) + 1 if conversations_response.data else 1
            print(f"📊 현재 턴 수: {current_turn}")
            
            # 메시지 히스토리 구성
            system_content = "당신은 치매 진단을 위한 따뜻한 대화 시스템입니다."
            if photo_info:
                system_content += f" 현재 사진 정보: 파일명({photo_info.get('filename', 'N/A')}), 설명({photo_info.get('description', 'N/A')}), 위치({photo_info.get('location_name', 'N/A')}), 태그({', '.join(photo_info.get('tags', []))})"
            
            message_history = [{"role": "system", "content": system_content}]
            
            # 기존 대화 내용 추가
            if conversations_response.data:
                for conv in conversations_response.data:
                    if conv.get("ai_output"):
                        message_history.append({
                            "role": "assistant", 
                            "content": conv["ai_output"]
                        })
                    if conv.get("user_input"):
                        message_history.append({
                            "role": "user", 
                            "content": conv["user_input"]
                        })
            
            state["message_history"] = message_history
            state["intermediate"] = {"cache_score": None, "routing_decision": ""}
            state["output"] = {"response_text": "", "response_audio_url": None}
            state["turn_count"] = current_turn
            state["assessment_completed"] = {"time_orientation": False, "language_naming": False}
            
            # photo_info와 session_id를 상태에 저장
            if photo_info:
                state["photo_info"] = photo_info
            state["session_id"] = session_id
            
        except Exception as e:
            print(f"Database operation failed: {e}")
            # 에러시 기본 상태 설정
            system_content = "당신은 치매 진단을 위한 따뜻한 대화 시스템입니다."
            state["message_history"] = [{"role": "system", "content": system_content}]
            state["intermediate"] = {"cache_score": None, "routing_decision": ""}
            state["output"] = {"response_text": "", "response_audio_url": None}
            state["session_id"] = conversation_id
            state["turn_count"] = 1  # 에러시 첫 번째 턴으로 가정
            state["assessment_completed"] = {"time_orientation": False, "language_naming": False}
        
        return state
    
    def router_node(self, state: GraphState) -> GraphState:
        """라우터 노드: 턴 수에 따른 평가 라우팅"""
        turn_count = state.get("turn_count", 1)
        user_message = state["input_data"]["user_message"]
        
        print(f"🔀 라우터 노드: turn_count={turn_count}")
        
        # 첫 번째와 두 번째 턴은 rule-based로 평가 노드로 라우팅
        if turn_count == 1:
            routing_decision = "time_orientation"
            print("🕐 첫 번째 턴 → 시간 지남력 평가")
        elif turn_count == 2:
            routing_decision = "language_naming"
            print("🗣️ 두 번째 턴 → 언어기능 평가")
        else:
            # 세 번째 턴부터는 기존 LangGraph 워크플로우 사용
            print("💬 세 번째 턴 이후 → 기존 워크플로우 사용")
            
            # 기존 라우터 로직 사용
            message_history = state["message_history"]
            
            # dialogue_prompt.py의 ROUTER_PROMPT 사용
            from .dialogue_prompt import ROUTER_PROMPT
            routing_prompt = ROUTER_PROMPT
            
            try:
                response = self.llm_mini.invoke([
                    SystemMessage(content=routing_prompt),
                    HumanMessage(content=f"사용자 메시지: {user_message}\n대화 히스토리: {message_history}")
                ])
                
                routing_decision = response.content.strip().lower()
                if routing_decision not in ["standard_chat", "assessment_chat"]:
                    routing_decision = "standard_chat"  # 기본값
                    
            except Exception as e:
                print(f"Router decision failed: {e}")
                routing_decision = "standard_chat"
        
        state["intermediate"]["routing_decision"] = routing_decision
        print(f"✅ 라우팅 결정: {routing_decision}")
        
        return state
    
    def time_orientation_node(self, state: GraphState) -> GraphState:
        """시간 지남력 평가 노드 (첫 번째 턴)"""
        print("🕐 시간 지남력 평가 노드 실행")
        
        # 현재 날짜 정보 가져오기
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # TIME_ORIENTATION_PROMPT 사용
        from .dialogue_prompt import TIME_ORIENTATION_PROMPT
        
        try:
            # 프롬프트 포맷팅
            time_question = TIME_ORIENTATION_PROMPT.format(
                current_year=current_year,
                current_month=current_month
            )
            
            state["output"]["response_text"] = time_question.strip()
            state["assessment_completed"]["time_orientation"] = True
            print(f"✅ 시간 지남력 질문 생성 완료: {current_year}년 {current_month}월")
            
        except Exception as e:
            print(f"❌ 시간 지남력 질문 생성 실패: {e}")
            state["output"]["response_text"] = f"기억 여행을 시작합니다. 여행을 떠나는 오늘은 {current_year}년 {current_month}월 며칠인가요?"
        
        return state
    
    def language_naming_node(self, state: GraphState) -> GraphState:
        """언어기능(이름대기) 평가 노드 (두 번째 턴)"""
        print("🗣️ 언어기능 평가 노드 실행")
        
        photo_info = state.get("photo_info", {})
        
        try:
            # 사진 분석 결과에서 key_objects 추출
            photo_analyze_result = photo_info.get('photo_analyze_result', {})
            key_objects = photo_analyze_result.get('key_objects', [])
            
            if not key_objects:
                # key_objects가 없으면 기본 응답
                state["output"]["response_text"] = "답변 감사해요. 그럼 지금부터 과거로 거슬러 올라가 보겠습니다... 3.. 2.. 1. 이 사진에서 보이는 것들을 하나씩 말씀해 주시겠어요?"
                print("⚠️ 사진에 key_objects가 없어 기본 질문 사용")
            else:
                # 첫 번째 객체를 선택하여 질문 생성
                selected_object = key_objects[0] if key_objects else "물건"
                
                # 사진이 찍힌 연도 계산 (taken_at 기준, 없으면 created_at 사용)
                taken_at = photo_info.get('taken_at') or photo_info.get('created_at')
                years_diff = 0
                if taken_at:
                    try:
                        # ISO 형식의 날짜 파싱
                        if isinstance(taken_at, str):
                            taken_date = datetime.fromisoformat(taken_at.replace('Z', '+00:00'))
                        else:
                            taken_date = taken_at
                        
                        years_diff = datetime.now().year - taken_date.year
                        if years_diff < 0:
                            years_diff = 0
                    except Exception as date_error:
                        print(f"⚠️ 날짜 파싱 오류: {date_error}")
                        years_diff = 0
                
                # NAMING_PROMPT 사용
                from .dialogue_prompt import NAMING_PROMPT
                
                photo_description = photo_info.get('description', '사진')
                
                # 객체 위치 기반 질문 생성 (간단한 버전)
                if years_diff > 0:
                    response_text = f"답변 감사해요. 그럼 지금부터 {years_diff}년 전으로 거슬러 올라가 보겠습니다... 3.. 2.. 1. 사진에서 보이는 {selected_object} 같은 것이 무엇인지 말씀해 주시겠어요?"
                else:
                    response_text = "답변 감사해요. 그럼 지금부터 과거로 거슬러 올라가 보겠습니다... 3.. 2.. 1. 사진에서 보이는 것들 중 하나를 가리켜서 이름을 말씀해 주시겠어요?"
                
                state["output"]["response_text"] = response_text
                print(f"✅ 언어기능 질문 생성 완료: {selected_object} 기반")
            
            state["assessment_completed"]["language_naming"] = True
            
        except Exception as e:
            print(f"❌ 언어기능 질문 생성 실패: {e}")
            state["output"]["response_text"] = "답변 감사해요. 그럼 지금부터 과거로 거슬러 올라가 보겠습니다... 3.. 2.. 1. 이 사진에서 보이는 것 중 하나를 말씀해 주시겠어요?"
            state["assessment_completed"]["language_naming"] = True
        
        return state
    
    def standard_response_node(self, state: GraphState) -> GraphState:
        """일반 응답 생성 노드: 자연스러운 일상 대화"""
        user_message = state["input_data"]["user_message"]
        photo_context = state["input_data"]["photo_context"]
        photo_info = state.get("photo_info", {})
        message_history = state.get("message_history", [])
        
        # 사진 정보 포함한 컨텍스트 구성
        photo_description = ""
        if photo_info:
            # 기본 사진 정보
            basic_info = f"사진 정보: {photo_info.get('description', '')}, 위치: {photo_info.get('location_name', '')}, 태그: {', '.join(photo_info.get('tags', []))}"
            
            # 분석 결과 추가
            analyze_result = photo_info.get('photo_analyze_result')
            if analyze_result:
                analysis_info = []
                if analyze_result.get('caption'):
                    analysis_info.append(f"분석 설명: {analyze_result['caption']}")
                if analyze_result.get('mood'):
                    analysis_info.append(f"분위기: {analyze_result['mood']}")
                if analyze_result.get('key_objects'):
                    analysis_info.append(f"주요 객체: {', '.join(analyze_result['key_objects'])}")
                if analyze_result.get('people_description'):
                    analysis_info.append(f"인물: {analyze_result['people_description']}")
                if analyze_result.get('time_of_day'):
                    analysis_info.append(f"시간대: {analyze_result['time_of_day']}")
                
                if analysis_info:
                    photo_description = f"{basic_info}\n분석 결과: {', '.join(analysis_info)}"
                else:
                    photo_description = basic_info
            else:
                photo_description = basic_info
        
        # dialogue_prompt.py의 STANDARD_RESPONSE_PROMPT 사용 (템플릿 변수 적용)
        conversation_prompt = STANDARD_RESPONSE_PROMPT.format(
            photo_description=photo_description,
            user_message=user_message,
            message_history=message_history
        )
        
        try:
            response = self.llm_mini.invoke([
                SystemMessage(content=conversation_prompt),
                HumanMessage(content=user_message)
            ])
            
            state["output"]["response_text"] = response.content.strip()
            
        except Exception as e:
            print(f"Standard response generation failed: {e}")
            state["output"]["response_text"] = "죄송합니다. 다시 말씀해 주시겠어요?"
        
        return state
    
    def cache_retrieve_and_evaluate_node(self, state: GraphState) -> GraphState:
        """캐시 검색 및 평가 노드: 인지기능 평가 질문 검색"""
        user_message = state["input_data"]["user_message"]
        message_history = state.get("message_history", [])
        
        try:
            # Supabase에서 CIST 질문 템플릿 검색
            response = self.supabase.table("cist_question_templates").select(
                "*"
            ).limit(5).execute()
            
            if response.data:
                # dialogue_prompt.py의 CACHE_RETRIEVE_AND_EVALUATE_PROMPT 사용
                # 실제 구현시에는 이 프롬프트를 사용하여 가장 적합한 질문 선택
                evaluate_prompt = CACHE_RETRIEVE_AND_EVALUATE_PROMPT
                
                # 간단한 유사도 평가 (실제로는 벡터 DB 사용 권장)
                best_question = response.data[0]
                cache_score = 0.9  # 임시 점수
                
                state["intermediate"]["cache_score"] = cache_score
                state["output"]["response_text"] = best_question["template_text"]
            else:
                state["intermediate"]["cache_score"] = 0.3  # 낮은 점수
                
        except Exception as e:
            print(f"Cache retrieval failed: {e}")
            state["intermediate"]["cache_score"] = 0.3
        
        return state
    
    def fallback_node(self, state: GraphState) -> GraphState:
        """대체 응답 처리 노드: 경량 LLM으로 응답 생성"""
        user_message = state["input_data"]["user_message"]
        conversation_id = state["input_data"]["conversation_id"]
        photo_context = state["input_data"]["photo_context"]
        photo_info = state.get("photo_info", {})
        message_history = state.get("message_history", [])
        
        # 사진 분석 결과 요약 (fallback용 간단 버전)
        photo_metadata = ""
        if photo_info:
            analyze_result = photo_info.get('photo_analyze_result')
            if analyze_result:
                context_parts = []
                if analyze_result.get('caption'):
                    context_parts.append(f"사진: {analyze_result['caption'][:50]}...")
                if analyze_result.get('mood'):
                    context_parts.append(f"분위기: {analyze_result['mood']}")
                
                if context_parts:
                    photo_metadata = f"참고: {', '.join(context_parts)}"
        
        # dialogue_prompt.py의 FALLBACK_PROMPT 사용
        fallback_prompt = FALLBACK_PROMPT
        
        try:
            # 프롬프트에 컨텍스트 정보 포함
            context_info = f"사용자 메시지: {user_message}\n사진 메타데이터: {photo_metadata}\n최근 대화: {message_history[-2:] if message_history else []}"
            
            response = self.llm_nano.invoke([
                SystemMessage(content=fallback_prompt),
                HumanMessage(content=context_info)
            ])
            
            state["output"]["response_text"] = response.content.strip()
            
            # 백그라운드에서 고품질 질문 생성 요청
            self._schedule_background_task(user_message, conversation_id, photo_context)
            
        except Exception as e:
            print(f"Fallback response failed: {e}")
            state["output"]["response_text"] = "네, 알겠습니다."
        
        return state
    
    def _schedule_background_task(self, user_message: str, conversation_id: str, photo_context: dict):
        """Celery를 통한 백그라운드 작업 스케줄링"""
        try:
            from tasks import generate_high_quality_questions
            
            context = {
                "user_message": user_message,
                "conversation_id": conversation_id, 
                "photo_context": photo_context
            }
            
            # 비동기 작업 발행
            generate_high_quality_questions.delay(context)
            print(f"Background task scheduled for conversation: {conversation_id}")
            
        except Exception as e:
            print(f"Failed to schedule background task: {e}")
    
    def _route_decision(self, state: GraphState) -> str:
        """라우터 결정에 따른 경로 선택"""
        return state["intermediate"]["routing_decision"]
    
    def _cache_decision(self, state: GraphState) -> str:
        """캐시 점수에 따른 경로 선택"""
        cache_score = state["intermediate"]["cache_score"]
        if cache_score and cache_score >= 0.85:
            return "use_cache"
        return "use_fallback"
    
    async def _save_conversation_to_db(self, state: GraphState, authenticated_client: Client = None) -> None:
        """대화 내용을 DB에 저장"""
        try:
            # 인증된 클라이언트가 있으면 사용, 없으면 기본 클라이언트 사용
            client = authenticated_client if authenticated_client else self.supabase
            
            session_id = state.get("session_id")
            user_message = state["input_data"]["user_message"]
            ai_response = state["output"]["response_text"]
            photo_context = state["input_data"]["photo_context"]
            user_id = state["input_data"]["user_id"]
            
            print(f"💾 대화 저장 시도: session_id={session_id}, user_id={user_id}")
            
            if not session_id:
                print("❌ session_id 없음, 대화 저장 건너뜀")
                return
            
            # 다음 conversation_order 계산
            count_response = client.table("conversations").select(
                "conversation_order"
            ).eq("session_id", session_id).execute()
            
            next_order = len(count_response.data) + 1 if count_response.data else 1
            print(f"📊 대화 순서: {next_order}")
            
            # 평가 유형 결정
            routing_decision = state["intermediate"].get("routing_decision", "")
            question_type = "open_ended"  # 기본값
            cist_category = None
            is_cist_item = False
            
            if routing_decision == "time_orientation":
                question_type = "cist_orientation"
                cist_category = "orientation_time"
                is_cist_item = True
                print("📊 시간 지남력 평가로 분류")
            elif routing_decision == "language_naming":
                question_type = "cist_language"
                cist_category = "language_naming"
                is_cist_item = True
                print("📊 언어기능 평가로 분류")
            
            # 대화 레코드 생성
            conversation_data = {
                "session_id": session_id,
                "user_id": user_id,
                "photo_id": photo_context.get("photo_id"),
                "conversation_order": next_order,
                "ai_output": ai_response,
                "question_type": question_type,
                "cist_category": cist_category,
                "user_input": user_message,
                "is_cist_item": is_cist_item
            }
            
            print(f"📝 대화 데이터: {conversation_data}")
            
            insert_response = client.table("conversations").insert(conversation_data).execute()
            if insert_response.data:
                print(f"✅ 대화 저장 성공: {insert_response.data[0]['id']}")
            else:
                print("❌ 대화 저장 실패: 응답 데이터 없음")
                
        except Exception as e:
            print(f"❌ 대화 저장 DB 오류: {type(e).__name__}: {str(e)}")
            # 디버깅을 위해 상세 오류 정보 출력
            import traceback
            print(f"📋 상세 오류: {traceback.format_exc()}")

    async def process_message(self, input_data: WorkflowInput, authenticated_client: Client = None) -> FinalOutput:
        """메시지 처리 진입점"""
        initial_state = {
            "input_data": input_data,
            "message_history": [],
            "intermediate": {"cache_score": None, "routing_decision": ""},
            "output": {"response_text": "", "response_audio_url": None},
            "photo_info": None,
            "session_id": None,
            "turn_count": 1,  # 기본값, init_state_node에서 실제 값으로 업데이트
            "assessment_completed": {"time_orientation": False, "language_naming": False},
            "_authenticated_client": authenticated_client
        }
        
        try:
            print(f"🚀 워크플로우 시작: conversation_id={input_data['conversation_id']}")
            
            final_state = await self.app.ainvoke(initial_state)
            print(f"✅ 워크플로우 완료: conversation_id={input_data['conversation_id']}")
            
            # 대화 내용을 DB에 저장
            if final_state["output"]["response_text"]:
                try:
                    await self._save_conversation_to_db(final_state, authenticated_client)
                    print("✅ 대화 DB 저장 완료")
                except Exception as db_error:
                    print(f"❌ 대화 DB 저장 실패: {db_error}")
                    # 대화 저장 실패해도 응답은 전송
            
            return final_state["output"]
        except Exception as e:
            import traceback
            print(f"❌ 워크플로우 실행 실패: conversation_id={input_data['conversation_id']}, error={e}")
            print(f"📋 상세 오류: {traceback.format_exc()}")
            return {
                "response_text": "죄송합니다. 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "response_audio_url": None
            }
