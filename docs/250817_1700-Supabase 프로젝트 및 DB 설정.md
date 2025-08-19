# Memento Box - Database Setup Guide

## Overview
이 문서는 Memento Box 프로젝트의 Supabase 데이터베이스 설정과 구조에 대한 가이드입니다.

## Supabase 프로젝트 설정

### 1. Supabase 프로젝트 생성
1. [Supabase 콘솔](https://supabase.com/dashboard)에 로그인
2. "New Project" 클릭
3. 프로젝트 정보 입력:
   - **Name**: memento-box
   - **Database Password**: 강력한 비밀번호 생성
   - **Region**: Northeast Asia (Seoul) - ap-northeast-2

### 2. 환경 변수 설정
1. 프로젝트 생성 후 Settings > API 페이지에서 다음 정보 확인:
   - Project URL
   - API Keys (anon public, service_role)

2. `.env` 파일 생성 (`.env.example` 참고):
```bash
cp .env.example .env
```

3. `.env` 파일에 실제 값들로 업데이트:
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
DATABASE_URL=postgresql://postgres:your_password@db.your-project-ref.supabase.co:5432/postgres
```

### 3. 데이터베이스 스키마 생성
1. Supabase 콘솔에서 SQL Editor 열기
2. `database/schema.sql` 파일의 내용을 복사하여 실행
3. 스키마 생성 완료 확인

### 4. 인증 설정
1. Authentication > Settings 페이지로 이동
2. Email 인증 활성화:
   - **Enable email confirmations**: true
   - **Enable email change confirmations**: true
3. Password 정책 설정:
   - **Minimum password length**: 8
   - **Require uppercase**: true
   - **Require numbers**: true

### 5. Storage 설정
1. Storage > Buckets 페이지로 이동
2. "memento-storage" 버킷 생성:
   - **Name**: memento-storage
   - **Public bucket**: false (보안을 위해 비공개)
3. Storage 정책 설정 (RLS):
```sql
-- Users can upload their own files
CREATE POLICY "Users can upload own files" ON storage.objects
FOR INSERT WITH CHECK (auth.uid()::text = (storage.foldername(name))[1]);

-- Users can view their own files
CREATE POLICY "Users can view own files" ON storage.objects
FOR SELECT USING (auth.uid()::text = (storage.foldername(name))[1]);

-- Users can update their own files
CREATE POLICY "Users can update own files" ON storage.objects
FOR UPDATE USING (auth.uid()::text = (storage.foldername(name))[1]);

-- Users can delete their own files
CREATE POLICY "Users can delete own files" ON storage.objects
FOR DELETE USING (auth.uid()::text = (storage.foldername(name))[1]);
```

## 데이터베이스 구조

### 핵심 테이블

#### 1. users
사용자 기본 정보 (Supabase auth.users 확장)
- 개인정보, 온보딩 상태, 동의 여부 등

#### 2. photos
사용자 업로드 사진 관리
- 파일 정보, 메타데이터, 태그, 위치 정보 등

#### 3. sessions
회상 대화 세션
- 세션 상태, 사용된 사진, CIST 점수 등

#### 4. conversations
개별 대화 기록
- 질문-답변 쌍, AI 분석 결과, CIST 분류 등

#### 5. cist_responses
CIST 평가 응답 상세
- 카테고리별 점수, 정답 여부, 응답 시간 등

#### 6. session_reports
세션 요약 리포트
- 총점, 인지 상태, 인사이트, 권장사항 등

### 데이터베이스 다이어그램

```mermaid
erDiagram
    users ||--o{ photos : "owns"
    users ||--o{ sessions : "participates"
    sessions ||--o{ conversations : "contains"
    photos ||--o{ conversations : "referenced_in"
    conversations ||--o{ cist_responses : "generates"
    sessions ||--|| session_reports : "summarized_by"
    
    users {
        uuid id PK
        string email
        string full_name
        date birth_date
        boolean onboarding_completed
        timestamp created_at
    }
    
    photos {
        uuid id PK
        uuid user_id FK
        string file_path
        string[] tags
        boolean is_favorite
        timestamp created_at
    }
    
    sessions {
        uuid id PK
        uuid user_id FK
        uuid[] selected_photos
        string status
        integer cist_score
        timestamp started_at
    }
    
    conversations {
        uuid id PK
        uuid session_id FK
        uuid photo_id FK
        string question_type
        text user_response_text
        integer cist_score
        boolean is_cist_item
    }
    
    cist_responses {
        uuid id PK
        uuid session_id FK
        string cist_category
        boolean is_correct
        decimal partial_score
        integer response_time_seconds
    }
    
    session_reports {
        uuid id PK
        uuid session_id FK
        integer total_cist_score
        string cognitive_status
        jsonb category_scores
        text[] insights
    }
```

## 보안 설정 (Row Level Security)

모든 테이블에 RLS가 적용되어 있어 사용자는 자신의 데이터만 접근 가능:
- 사용자는 자신의 프로필, 사진, 세션, 대화 기록만 조회/수정 가능
- JWT 토큰 기반 인증으로 API 접근 제어
- Storage 파일도 사용자별 폴더 구조로 격리

## 성능 최적화

### 인덱스
주요 쿼리 패턴을 고려한 인덱스가 설정됨:
- 사용자별 데이터 조회: `user_id` 인덱스
- 시간순 정렬: `created_at DESC` 인덱스  
- 태그 검색: GIN 인덱스 (photos.tags)
- CIST 카테고리별 분석: `cist_category` 인덱스

### 뷰 (Views)
자주 사용되는 집계 쿼리를 위한 뷰:
- `user_session_summary`: 사용자별 세션 요약
- `cist_performance_by_category`: 카테고리별 CIST 성과

## 개발/테스트용 데이터

`database/seed_data.sql`을 실행하여 개발에 필요한 기본 데이터 삽입:
- CIST 질문 템플릿
- 대화 시작 문구들
- 앱 설정값들

## 다음 단계

1. **API 개발**: FastAPI를 사용하여 데이터베이스 연동 API 개발
2. **Flutter 연동**: Supabase Flutter SDK를 사용하여 클라이언트 연동
3. **실시간 기능**: Supabase Realtime을 활용한 세션 상태 동기화
4. **백업/복구**: 정기적인 데이터베이스 백업 체계 구축

## 트러블슈팅

### 일반적인 문제들

1. **RLS 정책 오류**
   - 정책이 올바르게 설정되었는지 확인
   - `auth.uid()`가 null이 아닌지 확인

2. **Storage 업로드 실패**
   - 버킷 권한 설정 확인
   - 파일 크기 제한 확인 (기본 50MB)

3. **성능 이슈**
   - 쿼리 실행 계획 확인
   - 필요시 추가 인덱스 생성

## 참고 자료

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)