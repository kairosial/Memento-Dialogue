# Memento Box - API Endpoints Documentation

## Overview
Memento Box 백엔드 API 엔드포인트 명세서입니다. 모든 API는 JWT 토큰 기반 인증을 사용합니다.

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.memento-box.com/api/v1
```

## Authentication
모든 API 요청에는 Authorization 헤더가 필요합니다:
```
Authorization: Bearer <jwt_token>
```

## API Endpoints

### 1. Authentication

#### POST /auth/signup
사용자 회원가입
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "홍길동"
}
```

#### POST /auth/login
사용자 로그인
```json
{
  "email": "user@example.com", 
  "password": "password123"
}
```

#### POST /auth/logout
사용자 로그아웃

#### POST /auth/refresh
JWT 토큰 갱신

### 2. User Profile

#### GET /users/profile
현재 사용자 프로필 조회

#### PUT /users/profile
사용자 프로필 업데이트
```json
{
  "full_name": "홍길동",
  "birth_date": "1950-01-01",
  "gender": "male",
  "phone": "010-1234-5678"
}
```

#### POST /users/onboarding
온보딩 완료 처리
```json
{
  "privacy_consent": true,
  "terms_accepted": true,
  "notification_enabled": true
}
```

### 3. Photos Management

#### GET /photos
사용자 사진 목록 조회
- Query Parameters:
  - `page`: 페이지 번호 (기본값: 1)
  - `limit`: 페이지당 개수 (기본값: 20)
  - `tags`: 태그 필터 (예: "family,travel")
  - `favorite`: 즐겨찾기 필터 (true/false)

#### POST /photos/upload
사진 업로드
```json
{
  "file": "multipart/form-data",
  "description": "가족 여행 사진",
  "tags": ["family", "travel"],
  "taken_at": "2023-07-15T10:30:00Z",
  "location_name": "제주도"
}
```

#### GET /photos/{photo_id}
특정 사진 조회

#### PUT /photos/{photo_id}
사진 정보 업데이트
```json
{
  "description": "수정된 설명",
  "tags": ["family", "vacation"],
  "is_favorite": true
}
```

#### DELETE /photos/{photo_id}
사진 삭제 (소프트 삭제)

### 4. Conversation Sessions

#### POST /sessions
새 회상 세션 시작
```json
{
  "session_type": "reminiscence",
  "selected_photos": ["uuid1", "uuid2", "uuid3"]
}
```

#### GET /sessions
사용자 세션 목록 조회
- Query Parameters:
  - `status`: 상태 필터 (active, completed, paused)
  - `page`: 페이지 번호
  - `limit`: 페이지당 개수

#### GET /sessions/{session_id}
특정 세션 상세 조회

#### PUT /sessions/{session_id}
세션 상태 업데이트
```json
{
  "status": "completed",
  "notes": "세션 완료"
}
```

#### POST /sessions/{session_id}/conversations
세션에 새 대화 추가
```json
{
  "photo_id": "uuid",
  "question_text": "이 사진은 언제 찍으신 건가요?",
  "question_type": "open_ended",
  "conversation_order": 1
}
```

#### PUT /sessions/{session_id}/conversations/{conversation_id}
대화 응답 업데이트
```json
{
  "user_response_text": "2020년 여름에 가족들과 제주도 여행 갔을 때예요",
  "user_response_audio_url": "https://storage.url/audio.mp3",
  "response_duration_seconds": 30
}
```

### 5. CIST Assessment

#### POST /cist/responses
CIST 응답 기록
```json
{
  "session_id": "uuid",
  "conversation_id": "uuid",
  "cist_category": "orientation_time",
  "question_text": "오늘이 몇 년도인지 말씀해 주세요",
  "expected_response": "2025",
  "user_response": "2025년",
  "is_correct": true,
  "partial_score": 1.0,
  "response_time_seconds": 5
}
```

#### GET /cist/performance/{user_id}
사용자 CIST 성과 조회
- 카테고리별 점수 통계
- 시간별 성과 변화

### 6. AI Services

#### POST /ai/generate-question
AI 질문 생성
```json
{
  "photo_id": "uuid",
  "conversation_context": "이전 대화 내용",
  "cist_category": "memory_recall",
  "user_profile": {
    "age": 75,
    "interests": ["가족", "여행"]
  }
}
```

#### POST /ai/analyze-response
사용자 응답 분석
```json
{
  "conversation_id": "uuid",
  "user_response": "음성 또는 텍스트 응답",
  "question_type": "cist_memory",
  "expected_keywords": ["키워드1", "키워드2"]
}
```

### 7. Reports

#### GET /reports/sessions/{session_id}
세션 리포트 조회

#### POST /reports/sessions/{session_id}/generate
세션 리포트 생성 (비동기)

#### GET /reports/users/{user_id}/summary
사용자 전체 요약 리포트
- 기간별 CIST 점수 변화
- 인지 상태 추이
- 권장사항

### 8. Storage

#### POST /storage/upload
파일 업로드 (사진, 음성)
```json
{
  "file": "multipart/form-data",
  "folder": "photos|audio",
  "public": false
}
```

#### GET /storage/download/{file_path}
파일 다운로드 (서명된 URL 반환)

#### DELETE /storage/{file_path}
파일 삭제

## Response Format

### 성공 응답
```json
{
  "success": true,
  "data": { ... },
  "message": "요청이 성공적으로 처리되었습니다"
}
```

### 오류 응답
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "요청 데이터가 유효하지 않습니다",
    "details": { ... }
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | 인증 토큰이 유효하지 않음 |
| `FORBIDDEN` | 요청한 리소스에 접근 권한 없음 |
| `NOT_FOUND` | 요청한 리소스를 찾을 수 없음 |
| `INVALID_REQUEST` | 요청 데이터가 유효하지 않음 |
| `RATE_LIMITED` | API 호출 한도 초과 |
| `SERVER_ERROR` | 서버 내부 오류 |

## Rate Limiting

API 호출 제한:
- **일반 사용자**: 1000 requests/hour
- **파일 업로드**: 100 uploads/hour
- **AI 서비스**: 200 requests/hour

## Pagination

목록 조회 API는 페이지네이션을 지원합니다:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Webhooks

특정 이벤트 발생 시 설정된 URL로 POST 요청:

#### Session Completed
```json
{
  "event": "session.completed",
  "data": {
    "session_id": "uuid",
    "user_id": "uuid",
    "cist_score": 18,
    "completed_at": "2025-08-17T10:30:00Z"
  }
}
```

#### Report Generated
```json
{
  "event": "report.generated", 
  "data": {
    "session_id": "uuid",
    "report_id": "uuid",
    "cognitive_status": "normal"
  }
}
```

## SDK Integration

### Supabase Client Configuration
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://your-project.supabase.co',
  'your-anon-key'
)
```

### Flutter Integration
```dart
import 'package:supabase_flutter/supabase_flutter.dart';

await Supabase.initialize(
  url: 'https://your-project.supabase.co',
  anonKey: 'your-anon-key',
);
```

## Development Notes

1. **모든 타임스탬프는 UTC 기준**으로 저장/반환
2. **파일 업로드는 50MB 제한**
3. **음성 파일은 MP3, WAV 형식 지원**
4. **이미지는 JPEG, PNG 형식 지원**
5. **CIST 점수는 0-21 범위**

## 다음 단계

1. **API 구현**: FastAPI를 사용하여 실제 엔드포인트 구현
2. **테스트 케이스**: 각 엔드포인트별 단위/통합 테스트 작성
3. **API 문서**: OpenAPI/Swagger 자동 생성 문서 설정
4. **클라이언트 SDK**: Flutter용 API 클라이언트 라이브러리 개발