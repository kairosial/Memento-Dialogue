from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid
import json
import logging

from ..models.conversation import (
    ConversationState, ConversationContext, CISTCategory, 
    ResponseType, ConversationMessage, CISTQuestionCandidate,
    CIST_MAX_SCORES, STATE_TRANSITIONS
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """대화 흐름 관리 및 CIST 질문 삽입 타이밍 결정"""
    
    def __init__(self):
        # CIST 질문 삽입을 위한 기본 규칙들
        self.min_turns_before_cist = 2  # CIST 질문 전 최소 대화 턴
        self.max_turns_without_cist = 8  # CIST 없이 진행 가능한 최대 턴
        self.cist_insertion_probability = 0.3  # 기본 CIST 삽입 확률
        
        # 대화 맥락별 가중치
        self.context_weights = {
            "photo_description": 0.8,    # 사진 설명 중
            "memory_recall": 0.9,        # 기억 회상 중
            "storytelling": 0.7,         # 이야기 중
            "emotion_discussion": 0.6,   # 감정 토로 중
            "general_chat": 0.4          # 일반 대화
        }
    
    def should_insert_cist_question(
        self, 
        context: ConversationContext,
        current_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[CISTCategory], str]:
        """
        CIST 질문 삽입 여부 결정
        
        Returns:
            Tuple[bool, Optional[CISTCategory], str]: 
            (삽입 여부, CIST 카테고리, 삽입 이유)
        """
        
        # 1. 기본 조건 확인
        if context.turn_count < self.min_turns_before_cist:
            return False, None, "Minimum turns not reached"
        
        # 2. 이미 완료된 CIST 카테고리 확인
        available_categories = self._get_available_cist_categories(context)
        if not available_categories:
            return False, None, "All CIST categories completed"
        
        # 3. 강제 삽입 조건 (너무 오래 CIST 없이 진행된 경우)
        turns_since_last_cist = self._calculate_turns_since_last_cist(conversation_history)
        if turns_since_last_cist >= self.max_turns_without_cist:
            category = self._select_priority_cist_category(available_categories, context)
            return True, category, "Maximum turns without CIST reached"
        
        # 4. 대화 맥락 기반 적절성 판단
        context_type = self._analyze_conversation_context(current_message, conversation_history)
        contextual_score = self.context_weights.get(context_type, 0.4)
        
        # 5. 사진 관련 대화일 때 특정 CIST 카테고리 우선
        photo_related_category = self._check_photo_related_cist_opportunity(
            current_message, context, available_categories
        )
        
        if photo_related_category:
            if contextual_score > 0.6:
                return True, photo_related_category, f"Photo-related CIST opportunity: {context_type}"
        
        # 6. 기억 관련 대화일 때 메모리 CIST 우선
        memory_related_category = self._check_memory_related_cist_opportunity(
            current_message, conversation_history, available_categories
        )
        
        if memory_related_category:
            if contextual_score > 0.7:
                return True, memory_related_category, f"Memory-related CIST opportunity: {context_type}"
        
        # 7. 확률 기반 일반 삽입 결정
        import random
        adjusted_probability = self.cist_insertion_probability * contextual_score
        
        # 진행도에 따른 확률 조정
        completion_ratio = len([c for c in context.cist_progress.values() if c]) / len(CISTCategory)
        if completion_ratio < 0.3:  # 초기 단계
            adjusted_probability *= 1.2
        elif completion_ratio > 0.7:  # 마무리 단계
            adjusted_probability *= 1.5
        
        if random.random() < adjusted_probability:
            category = self._select_contextual_cist_category(
                available_categories, context_type, current_message
            )
            return True, category, f"Contextual insertion: {context_type} (score: {contextual_score:.2f})"
        
        return False, None, f"Context not suitable: {context_type} (score: {contextual_score:.2f})"
    
    def _get_available_cist_categories(self, context: ConversationContext) -> List[CISTCategory]:
        """완료되지 않은 CIST 카테고리 목록 반환"""
        return [
            category for category in CISTCategory 
            if not context.cist_progress.get(category, False)
        ]
    
    def _calculate_turns_since_last_cist(self, conversation_history: List[Dict[str, Any]]) -> int:
        """마지막 CIST 질문 이후 경과 턴 수 계산"""
        turns_since_cist = 0
        
        for message in reversed(conversation_history):
            if message.get("response_type") == ResponseType.CIST_QUESTION:
                break
            if message.get("message_type") == "user":
                turns_since_cist += 1
        
        return turns_since_cist
    
    def _analyze_conversation_context(
        self, 
        current_message: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """대화 맥락 분석"""
        
        # 키워드 기반 맥락 분석
        message_lower = current_message.lower()
        
        # 사진 설명 관련
        photo_keywords = ["사진", "이미지", "찍었", "보여", "모습", "장면"]
        if any(keyword in message_lower for keyword in photo_keywords):
            return "photo_description"
        
        # 기억 회상 관련
        memory_keywords = ["기억", "생각", "떠올", "추억", "그때", "예전", "옛날"]
        if any(keyword in message_lower for keyword in memory_keywords):
            return "memory_recall"
        
        # 이야기 관련
        story_keywords = ["이야기", "얘기", "일어났", "경험", "사건", "일"]
        if any(keyword in message_lower for keyword in story_keywords):
            return "storytelling"
        
        # 감정 표현 관련
        emotion_keywords = ["기뻤", "슬펐", "즐거웠", "행복", "우울", "감정", "느낌"]
        if any(keyword in message_lower for keyword in emotion_keywords):
            return "emotion_discussion"
        
        return "general_chat"
    
    def _check_photo_related_cist_opportunity(
        self, 
        current_message: str, 
        context: ConversationContext,
        available_categories: List[CISTCategory]
    ) -> Optional[CISTCategory]:
        """사진 관련 대화에서 적절한 CIST 카테고리 확인"""
        
        message_lower = current_message.lower()
        
        # 언어기능(이름대기) - 사진 속 사물/인물 언급 시
        if CISTCategory.LANGUAGE_NAMING in available_categories:
            naming_triggers = ["사람", "물건", "동물", "꽃", "나무", "건물", "차", "음식"]
            if any(trigger in message_lower for trigger in naming_triggers):
                return CISTCategory.LANGUAGE_NAMING
        
        # 장소 지남력 - 사진 촬영 장소 언급 시
        if CISTCategory.ORIENTATION_PLACE in available_categories:
            place_triggers = ["여기", "장소", "어디", "곳", "위치"]
            if any(trigger in message_lower for trigger in place_triggers):
                return CISTCategory.ORIENTATION_PLACE
        
        return None
    
    def _check_memory_related_cist_opportunity(
        self,
        current_message: str,
        conversation_history: List[Dict[str, Any]],
        available_categories: List[CISTCategory]
    ) -> Optional[CISTCategory]:
        """기억 관련 대화에서 적절한 CIST 카테고리 확인"""
        
        message_lower = current_message.lower()
        
        # 기억 관련 CIST 카테고리들 우선순위 순서
        memory_categories = [
            CISTCategory.MEMORY_RECALL,
            CISTCategory.MEMORY_REGISTRATION,
            CISTCategory.MEMORY_RECOGNITION
        ]
        
        memory_triggers = ["기억", "생각", "떠올", "잊었", "기억나"]
        
        if any(trigger in message_lower for trigger in memory_triggers):
            for category in memory_categories:
                if category in available_categories:
                    return category
        
        return None
    
    def _select_priority_cist_category(
        self, 
        available_categories: List[CISTCategory],
        context: ConversationContext
    ) -> CISTCategory:
        """우선순위 기반 CIST 카테고리 선택"""
        
        # 우선순위 정의 (중요도 순)
        priority_order = [
            CISTCategory.ORIENTATION_TIME,    # 시간 지남력 (기본)
            CISTCategory.MEMORY_REGISTRATION, # 기억등록
            CISTCategory.LANGUAGE_NAMING,     # 언어기능
            CISTCategory.MEMORY_RECALL,       # 기억회상
            CISTCategory.EXECUTIVE_FUNCTION,  # 집행기능
            CISTCategory.ORIENTATION_PLACE,   # 장소 지남력
            CISTCategory.ATTENTION,           # 주의력
            CISTCategory.MEMORY_RECOGNITION   # 기억재인
        ]
        
        for category in priority_order:
            if category in available_categories:
                return category
        
        # 남은 카테고리 중 첫 번째 반환
        return available_categories[0]
    
    def _select_contextual_cist_category(
        self,
        available_categories: List[CISTCategory],
        context_type: str,
        current_message: str
    ) -> CISTCategory:
        """맥락 기반 CIST 카테고리 선택"""
        
        # 맥락별 선호 카테고리
        context_preferences = {
            "photo_description": [CISTCategory.LANGUAGE_NAMING, CISTCategory.ORIENTATION_PLACE],
            "memory_recall": [CISTCategory.MEMORY_RECALL, CISTCategory.MEMORY_REGISTRATION],
            "storytelling": [CISTCategory.MEMORY_REGISTRATION, CISTCategory.EXECUTIVE_FUNCTION],
            "emotion_discussion": [CISTCategory.MEMORY_RECALL, CISTCategory.ATTENTION],
            "general_chat": [CISTCategory.ORIENTATION_TIME, CISTCategory.ATTENTION]
        }
        
        preferred_categories = context_preferences.get(context_type, [])
        
        # 선호 카테고리 중 사용 가능한 것 선택
        for category in preferred_categories:
            if category in available_categories:
                return category
        
        # 선호 카테고리가 없으면 우선순위 기반 선택
        return self._select_priority_cist_category(available_categories, None)
    
    def update_cist_progress(
        self, 
        context: ConversationContext, 
        category: CISTCategory, 
        score: float
    ):
        """CIST 진행 상황 업데이트"""
        context.cist_progress[category] = True
        context.cist_scores[category] = score
        context.updated_at = datetime.now()
        
        logger.info(f"CIST progress updated: {category} = {score}")
    
    def get_conversation_completion_status(self, context: ConversationContext) -> Dict[str, Any]:
        """대화 완료 상태 확인"""
        total_categories = len(CISTCategory)
        completed_categories = len([c for c in context.cist_progress.values() if c])
        completion_ratio = completed_categories / total_categories
        
        total_possible_score = sum(CIST_MAX_SCORES.values())
        current_score = sum(context.cist_scores.values())
        score_ratio = current_score / total_possible_score if total_possible_score > 0 else 0
        
        return {
            "completed_categories": completed_categories,
            "total_categories": total_categories,
            "completion_ratio": completion_ratio,
            "current_score": current_score,
            "total_possible_score": total_possible_score,
            "score_ratio": score_ratio,
            "is_complete": completion_ratio >= 1.0,
            "remaining_categories": [
                cat for cat in CISTCategory 
                if not context.cist_progress.get(cat, False)
            ]
        }
    
    def transition_state(
        self, 
        context: ConversationContext, 
        new_state: ConversationState,
        reason: str = ""
    ) -> bool:
        """상태 전환"""
        if new_state not in STATE_TRANSITIONS.get(context.current_state, []):
            logger.warning(
                f"Invalid state transition: {context.current_state} -> {new_state}"
            )
            return False
        
        old_state = context.current_state
        context.current_state = new_state
        context.updated_at = datetime.now()
        
        logger.info(
            f"State transition: {old_state} -> {new_state} "
            f"(reason: {reason})"
        )
        return True