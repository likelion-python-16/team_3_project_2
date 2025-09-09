# Python 런타임 환경을 기반으로 이미지를 빌드합니다.
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일을 먼저 복사하고 설치합니다.
# (소스 코드가 변경되어도 의존성이 동일하면 이 레이어는 캐시를 사용합니다.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 소스 코드를 복사합니다.
COPY . .

# 8000번 포트를 외부에 노출합니다.
EXPOSE 8000

# 컨테이너가 시작될 때 실행할 기본 명령어를 설정합니다.
# 데이터베이스 마이그레이션을 적용하고 개발 서버를 실행합니다.
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
