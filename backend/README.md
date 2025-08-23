# Memento Box Backend API

FastAPI 기반 백엔드 서버로 사진 기반 회상 대화 및 CIST 인지 평가를 지원합니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd backend
poetry install
```

### 2. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 Supabase 설정을 입력하세요:

```bash
cp .env.example .env
```

필수 환경 변수:
- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_ANON_KEY`: Supabase 익명 키  
- `SUPABASE_SERVICE_KEY`: Supabase 서비스 키
- `JWT_SECRET_KEY`: JWT 토큰 암호화 키

### 3. 서버 실행

```bash
# Poetry 가상환경에서 개발 모드 실행
poetry run python run_server.py

# 또는 가상환경 활성화 후 실행
poetry shell
python run_server.py

# 또는 직접 실행
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. API 테스트

```bash
# 기본 엔드포인트 테스트
poetry run python test_api.py
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🏗️ 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 설정 관리
│   │   ├── database.py      # Supabase 클라이언트
│   │   ├── security.py      # JWT 및 보안 유틸리티
│   │   └── deps.py          # 의존성 주입
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # 사용자 관련 Pydantic 모델
│   │   ├── photo.py         # 사진 관련 Pydantic 모델  
│   │   ├── session.py       # 세션 관련 Pydantic 모델
│   │   └── common.py        # 공통 응답 모델
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # 인증 엔드포인트
│       ├── users.py         # 사용자 관리 엔드포인트
│       ├── photos.py        # 사진 관리 엔드포인트
│       └── sessions.py      # 대화 세션 엔드포인트
├── .env.example             # 환경 변수 예제
├── pyproject.toml          # Poetry 의존성 및 프로젝트 설정
├── poetry.lock             # Poetry 잠금 파일
├── run_server.py           # 서버 실행 스크립트
├── test_api.py             # API 테스트 스크립트
└── README.md               # 이 파일
```

## 🔧 주요 기능

### 인증 시스템
- JWT 토큰 기반 인증
- Supabase Auth 연동
- 회원가입/로그인/로그아웃
- 토큰 갱신

### 사용자 관리
- 프로필 조회/수정
- 온보딩 프로세스
- 사용자 권한 관리

### 사진 관리
- 멀티파트 파일 업로드
- Supabase Storage 연동
- 이미지 메타데이터 추출
- 앨범 관리
- 태그 및 즐겨찾기 기능

### 대화 세션
- 회상 대화 세션 생성
- 대화 기록 저장
- CIST 평가 문항 관리
- 세션 상태 추적

## 🔒 보안 기능

- CORS 설정
- JWT 토큰 검증
- Row Level Security (RLS)
- 파일 업로드 검증
- 입력 데이터 유효성 검사

## 🧪 테스트

```bash
# 기본 API 테스트
poetry run python test_api.py

# pytest 실행
poetry run pytest tests/
```

## 🔄 개발 워크플로우

1. **의존성 관리**: `poetry add [package]`로 새 패키지 추가, `poetry remove [package]`로 제거
2. **가상환경**: `poetry shell`로 활성화, `exit`로 비활성화
3. **코드 변경**: 파일 수정 시 자동으로 서버가 재시작됩니다 (`--reload` 옵션)
4. **API 테스트**: Swagger UI에서 직접 테스트하거나 `poetry run python test_api.py` 실행
5. **로그 확인**: 터미널에서 실시간 로그 모니터링

### Poetry 주요 명령어
```bash
poetry install          # 의존성 설치
poetry add [package]    # 새 패키지 추가
poetry add --group dev [package]  # 개발용 패키지 추가
poetry remove [package] # 패키지 제거
poetry shell           # 가상환경 활성화
poetry run [command]   # 가상환경에서 명령 실행
poetry show           # 설치된 패키지 목록
poetry update         # 의존성 업데이트
```

## 📋 API 엔드포인트

### 인증 (`/api/v1/auth/`)
- `POST /signup` - 회원가입
- `POST /login` - 로그인  
- `POST /logout` - 로그아웃
- `POST /refresh` - 토큰 갱신

### 사용자 (`/api/v1/users/`)
- `GET /profile` - 프로필 조회
- `PUT /profile` - 프로필 수정
- `POST /onboarding` - 온보딩 완료

### 사진 (`/api/v1/photos/`)
- `GET /` - 사진 목록 조회 (페이지네이션, 필터링)
- `POST /upload` - 사진 업로드
- `GET /{photo_id}` - 특정 사진 조회
- `PUT /{photo_id}` - 사진 정보 수정
- `DELETE /{photo_id}` - 사진 삭제
- `POST /albums` - 앨범 생성
- `GET /albums` - 앨범 목록 조회

### 세션 (`/api/v1/sessions/`)
- `POST /` - 새 세션 생성
- `GET /` - 세션 목록 조회
- `GET /{session_id}` - 특정 세션 조회
- `PUT /{session_id}` - 세션 상태 업데이트
- `POST /{session_id}/conversations` - 대화 생성
- `PUT /{session_id}/conversations/{conversation_id}` - 대화 응답 업데이트
- `GET /{session_id}/conversations` - 세션의 모든 대화 조회

## 🚨 트러블슈팅

### 서버가 시작되지 않는 경우
1. `.env` 파일이 올바르게 설정되었는지 확인
2. 모든 의존성이 설치되었는지 확인: `poetry install`
3. Python 버전 확인 (3.11+)
4. Poetry 가상환경 활성화: `poetry shell`

### Supabase 연결 오류
1. Supabase URL과 키가 정확한지 확인
2. Supabase 프로젝트가 활성 상태인지 확인
3. 네트워크 연결 상태 확인

### 파일 업로드 오류
1. Supabase Storage 버킷이 생성되었는지 확인
2. 파일 크기 제한 확인 (50MB)
3. 지원되는 파일 형식인지 확인

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. 로그 메시지 확인
2. API 문서에서 요청 형식 확인
3. 환경 변수 설정 재확인