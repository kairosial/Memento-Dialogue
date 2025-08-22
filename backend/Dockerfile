# Python 3.11을 기반으로 하는 멀티스테이지 빌드
FROM python:3.11-slim as base

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry==1.6.1

# Poetry 설정
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 작업 디렉토리 설정
WORKDIR /app

# Poetry 설정 파일 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# 프로덕션 스테이지
FROM python:3.11-slim as production

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Poetry 가상환경을 시스템에 복사
COPY --from=base /app/.venv /app/.venv

# PATH에 가상환경 추가
ENV PATH="/app/.venv/bin:$PATH"

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 개발 스테이지
FROM base as development

# 개발용 의존성 포함하여 설치
RUN poetry install

# 작업 디렉토리의 모든 파일 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 개발 환경에서는 리로드 모드로 실행
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]