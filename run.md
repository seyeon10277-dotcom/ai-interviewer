# 실행 가이드

## 빠른 시작

### 1. API 키 설정

`.env` 파일을 열어 키를 입력합니다:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
APP_URL=http://localhost:5000
FLASK_SECRET_KEY=my-secret-key-2024
FLASK_DEBUG=False
FLASK_PORT=5000
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
python run.py
```

> `run.py`는 실행 전 API 키 유무를 자동으로 검사합니다.
> 키가 없으면 경고 메시지를 출력하고 종료됩니다.

### 4. 브라우저 접속

```
http://localhost:5000
```

---

## 직접 실행 (app.py)

환경 검사를 생략하고 직접 서버를 실행할 경우:

```bash
python app.py
```

기본 포트: `5000` (`.env`의 `FLASK_PORT`로 변경 가능)

---

## 환경별 실행

### 개발 환경

```env
FLASK_DEBUG=True
FLASK_PORT=5000
```

```bash
python run.py
```

### 운영 환경

```env
FLASK_DEBUG=False
FLASK_PORT=8000
```

```bash
python run.py
```

---

## 인증 관련

### 이메일 확인 비활성화 (권장)
Supabase 대시보드 → Authentication → Providers → Email → "Confirm email" 비활성화 시
회원가입 즉시 로그인 가능합니다.

활성화 상태라면 회원가입 후 이메일 확인 링크를 클릭해야 로그인 가능합니다.

---

## 문제 해결

### API 키 오류
```
⚠️  OpenAI API 키가 설정되지 않았습니다!
```
→ `.env` 파일에서 `OPENAI_API_KEY` 값을 확인하세요.

### 패키지 설치 오류 (pyaudio)
Windows에서 `pyaudio` 설치 실패 시:
```bash
pip install pipwin
pipwin install pyaudio
```

### 포트 충돌
```
Address already in use
```
→ `.env`에서 `FLASK_PORT` 값을 변경하거나, 기존 프로세스를 종료하세요:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID번호> /F
```

### 카메라/마이크 오류
- Chrome 브라우저 사용 필수 (Web Speech API 지원)
- `http://localhost:5000` 접속 시 브라우저의 카메라/마이크 권한 허용 필요

---

## 종료

서버 종료: `Ctrl + C`
