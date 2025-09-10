# Team3 Cafe Analysis API 가이드

## 개요

Team3 Cafe Analysis API는 카페 창업 및 투자 분석을 위한 종합적인 데이터 서비스를 제공합니다. 이 API를 통해 전국 카페 데이터, 매출 분석, 프랜차이즈 정보, 지역별 통계 등을 조회할 수 있습니다.

### 기본 정보
- **Base URL**: `https://team3-project-2-app.fly.dev`
- **API 버전**: 1.0.0
- **데이터 포맷**: JSON
- **문자 인코딩**: UTF-8

### 주요 기능
- 🏪 **카페 데이터 조회**: 전국 41,199개 카페 정보
- 📊 **매출 분석**: 10,361개 매출 데이터 기반 분석
- 🔍 **비즈니스 분석**: 창업 위험도, 성장률, 상권 분석
- 🏢 **프랜차이즈 분석**: 브랜드별 매출, 성장률, 카페 수 분석
- 📈 **트렌드 분석**: 신규 사업자, 생존율, 3년 성장률 트렌드
- 🗺️ **지역별 통계**: 시/구별 카페 현황 및 통계
- 👤 **사용자 관리**: 회원가입, 로그인, 구독 관리

## 인증

### 1. 세션 기반 인증 (권장)
API는 Django 세션 기반 인증을 사용합니다.

#### 로그인
```http
POST /api/accounts/users/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

성공 시 세션 쿠키(`sessionid`)가 설정됩니다. 이후 모든 요청에 이 쿠키가 자동으로 포함됩니다.

#### 로그아웃
```http
POST /api/accounts/users/logout/
```

### 2. Basic 인증
HTTP Basic 인증도 지원합니다:
```http
Authorization: Basic <base64(username:password)>
```

### 3. 익명 접근
일부 엔드포인트는 인증 없이 접근 가능합니다:
- `/cafes/map_markers/` - 지도 마커용 카페 데이터
- `/health/` - 헬스 체크

## 엔드포인트

### 사용자 관리 (accounts)

#### 회원가입
```http
POST /api/accounts/users/register/
```

#### 사용자 목록 조회
```http
GET /api/accounts/users/
```

#### 현재 사용자 정보
```http
GET /api/accounts/users/me/
```

#### 사용자 상세 조회/수정/삭제
```http
GET|PUT|PATCH|DELETE /api/accounts/users/{user_id}/
```

### 카페 데이터 (cafes)

#### 카페 목록 조회
```http
GET /api/cafes/cafes/
```

#### 카페 상세 정보
```http
GET /api/cafes/cafes/{id}/
```

#### 지도 마커용 데이터 (인증 불필요)
```http
GET /api/cafes/cafes/map_markers/
```

#### 필터링된 카페 데이터 (인증 필요)
```http
GET /api/cafes/cafes/filtered_data/
```

### 비즈니스 분석

#### 사업자 상세 분석
```http
GET /api/cafes/cafes/business_analysis/
```

#### 성장률 분석
```http
GET /api/cafes/cafes/growth_rate_analysis/
```

#### 위험 지역 분석
```http
GET /api/cafes/cafes/risk_area_analysis/
```

#### 상권 수 분석
```http
GET /api/cafes/cafes/store_count_analysis/
```

### 프랜차이즈 분석

#### 프랜차이즈 매출 분석
```http
GET /api/cafes/cafes/franchise_sales_analysis/
```

#### 프랜차이즈 성장률 분석
```http
GET /api/cafes/cafes/franchise_growth_analysis/
```

#### 프랜차이즈 카페 수 분석
```http
GET /api/cafes/cafes/franchise_cafe_count_analysis/
```

#### 프랜차이즈 타입별 브랜드 분석
```http
GET /api/cafes/cafes/franchise_type_analysis/
```

### 트렌드 분석

#### 신규 사업자 현황 분석
```http
GET /api/cafes/cafes/trend_new_business_analysis/
```

#### 매출 지수 분석
```http
GET /api/cafes/cafes/trend_sales_index_analysis/
```

#### 카페 생존율 분석
```http
GET /api/cafes/cafes/trend_survival_rate_analysis/
```

#### 3년 성장률 트렌드 분석
```http
GET /api/cafes/cafes/trend_three_year_growth_analysis/
```

### 지역별 데이터

#### 지역별 통계
```http
GET /api/cafes/cafes/region_stats/
```

## 에러 포맷

API는 표준 HTTP 상태 코드와 JSON 형식의 에러 응답을 제공합니다.

### 에러 응답 구조
```json
{
  "error": "에러 유형",
  "message": "에러 상세 메시지",
  "code": "API_ERROR_CODE",
  "details": {
    "field": ["필드별 에러 메시지"]
  }
}
```

### 주요 HTTP 상태 코드

#### 2xx 성공
- **200 OK**: 요청 성공
- **201 Created**: 리소스 생성 성공
- **204 No Content**: 삭제 성공

#### 4xx 클라이언트 에러
- **400 Bad Request**: 잘못된 요청 형식
```json
{
  "error": "Bad Request",
  "message": "요청 데이터가 올바르지 않습니다",
  "details": {
    "username": ["이 필드는 필수입니다."],
    "email": ["올바른 이메일 주소를 입력하세요."]
  }
}
```

- **401 Unauthorized**: 인증 필요
```json
{
  "error": "Unauthorized",
  "message": "Authentication credentials were not provided.",
  "code": "not_authenticated"
}
```

- **403 Forbidden**: 권한 없음
```json
{
  "error": "Forbidden",
  "message": "You do not have permission to perform this action.",
  "code": "permission_denied"
}
```

- **404 Not Found**: 리소스 없음
```json
{
  "error": "Not Found",
  "message": "요청한 리소스를 찾을 수 없습니다.",
  "code": "not_found"
}
```

- **429 Too Many Requests**: 요청 한도 초과
```json
{
  "error": "Too Many Requests",
  "message": "Request was throttled. Expected available in 60 seconds.",
  "code": "throttled"
}
```

#### 5xx 서버 에러
- **500 Internal Server Error**: 서버 내부 오류
```json
{
  "error": "Internal Server Error",
  "message": "서버에서 요청을 처리하는 중 오류가 발생했습니다.",
  "code": "server_error"
}
```

- **503 Service Unavailable**: 서비스 일시 중단
```json
{
  "error": "Service Unavailable",
  "message": "서비스가 일시적으로 사용할 수 없습니다.",
  "code": "service_unavailable"
}
```

### 유효성 검사 에러 예시
```json
{
  "error": "Validation Error",
  "message": "입력 데이터에 오류가 있습니다.",
  "details": {
    "username": [
      "이 필드는 필수입니다.",
      "사용자명은 50자 이하로 입력해주세요."
    ],
    "email": [
      "올바른 이메일 주소를 입력하세요."
    ],
    "password": [
      "비밀번호는 8자 이상이어야 합니다."
    ]
  }
}
```

## 추가 리소스

- **Swagger UI**: https://team3-project-2-app.fly.dev/docs/
- **ReDoc**: https://team3-project-2-app.fly.dev/redoc/
- **OpenAPI Schema**: https://team3-project-2-app.fly.dev/api/schema/

## 지원

API 사용 중 문제가 있거나 질문이 있으시면 다음을 참고하세요:

1. **API 문서**: 위의 Swagger UI나 ReDoc에서 상세한 API 명세 확인
2. **헬스 체크**: `/health/` 엔드포인트로 API 서버 상태 확인
3. **에러 로그**: 응답의 에러 메시지와 코드를 확인하여 문제 진단