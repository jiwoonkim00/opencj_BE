# 사용할 기본 이미지 (Python 3.10 버전)
FROM python:3.10-slim

# 작업 디렉터리를 /app으로 설정
WORKDIR /app

# 현재 디렉터리의 requirements.txt를 컨테이너 안으로 복사
# 캐싱을 위해 먼저 복사
COPY requirements.txt .

# requirements.txt에 명시된 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 현재 디렉터리의 모든 파일을 컨테이너의 작업 디렉터리로 복사
COPY . .

# FastAPI 애플리케이션을 실행할 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]