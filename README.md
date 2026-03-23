# 🤖 AI 스마트 면접관

GPT + MediaPipe 기반 실시간 AI 면접 연습 시스템

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 📹 실시간 얼굴 분석 | MediaPipe로 시선, 자세, 표정 실시간 분석 |
| 🎤 음성 인식 | Web Speech API로 실제 면접처럼 마이크 답변 |
| ⚠️ 습관어 감지 | "음", "어", "아", "um", "uh" 등 자동 감지 |
| 🎵 음성 톤 분석 | librosa로 피치, 볼륨, 단조로움 분석 |
| 🧠 GPT 실시간 피드백 | 논리성·구체성·적합성 즉각 평가 |
| 📊 상세 리포트 | 점수와 함께 PDF 다운로드 제공 |
| 🎯 맞춤형 질문 | 회사/직무 입력 → AI 예상 질문 자동 생성 |

## 📁 프로젝트 구조

```
AI Interviwer/
├── .env                        # OpenAI API 키 및 환경 설정
├── requirements.txt            # Python 패키지 목록
├── app.py                      # Flask 메인 서버 + WebSocket
├── run.py                      # 실행 스크립트 (환경 검사 포함)
├── modules/
│   ├── ai_feedback.py          # GPT 기반 답변 피드백 모듈
│   ├── speech_analyzer.py      # 음성 분석 (습관어, 속도, 톤)
│   ├── face_analyzer.py        # MediaPipe 얼굴 인식
│   ├── question_generator.py   # 회사/직무 맞춤형 질문 생성
│   └── report_generator.py     # PDF 리포트 생성
├── templates/
│   ├── index.html              # 메인 페이지 (회사/직무 설정)
│   ├── interview.html          # 면접 진행 페이지
│   └── report.html             # 결과 리포트 페이지
├── static/
│   ├── css/style.css           # 전체 스타일
│   └── js/main.js              # 카메라/마이크/WebSocket 제어
└── reports/                    # 생성된 PDF 리포트 저장 폴더
```

## 🔧 API 엔드포인트

### HTTP REST
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 메인 페이지 |
| GET | `/interview` | 면접 진행 페이지 |
| GET | `/report/<session_id>` | 리포트 페이지 |
| POST | `/api/generate-questions` | 맞춤형 질문 생성 |
| GET | `/api/get-report/<session_id>` | 세션 리포트 데이터 반환 |
| GET | `/api/download-report/<session_id>` | PDF 리포트 다운로드 |

### WebSocket 이벤트
| 이벤트 | 방향 | 설명 |
|--------|------|------|
| `connect` | 클라이언트→서버 | 세션 초기화 |
| `analyze_frame` | 클라이언트→서버 | 카메라 프레임 얼굴 분석 |
| `analyze_speech` | 클라이언트→서버 | 음성 텍스트 분석 |
| `get_feedback` | 클라이언트→서버 | GPT 답변 피드백 요청 |
| `save_session_data` | 클라이언트→서버 | 면접 세션 최종 저장 |

## 🔐 인증 시스템 (Supabase Auth)

회원가입한 사용자만 서비스를 이용할 수 있습니다.

| 경로 | 설명 |
|------|------|
| `/login` | 로그인 페이지 |
| `/signup` | 회원가입 페이지 |
| `/logout` | 로그아웃 |

- Supabase Auth (이메일/비밀번호) 기반
- JWT 토큰을 Flask 세션에 저장
- 모든 페이지 및 API에 `@login_required` 데코레이터 적용
- 프로젝트: `login_test` (ap-northeast-2)

## 🔌 주요 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| flask | 3.0.3 | 웹 서버 |
| flask-socketio | 5.3.6 | WebSocket 실시간 통신 |
| openai | 1.35.3 | GPT 피드백 생성 |
| mediapipe | 0.10.14 | 얼굴 분석 |
| librosa | 0.10.2 | 음성 톤 분석 |
| fpdf2 | 2.7.9 | PDF 리포트 생성 |
| eventlet | 0.36.1 | 비동기 처리 |
| supabase | 2.0.0+ | 인증 (회원가입/로그인) |

## ⚙️ 환경 요구사항

- Python 3.10+
- Chrome 브라우저 (Web Speech API 지원)
- 웹캠 및 마이크
- OpenAI API 키

## 📝 .env 설정

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
APP_URL=http://localhost:5000
FLASK_SECRET_KEY=my-secret-key-2024
FLASK_DEBUG=False
FLASK_PORT=5000
```

## 🎯 사용 방법

1. **회사/직무 설정** — 지원 회사와 직무 입력 시 AI가 맞춤형 질문 생성
2. **면접 시작** — 카메라와 마이크 접근 권한 허용
3. **답변 녹음** — 🎤 버튼을 눌러 답변 시작
4. **실시간 피드백** — 답변 중 얼굴·음성 분석 실시간 표시
5. **AI 피드백** — 답변 완료 후 GPT가 논리성·구체성·적합성 평가
6. **리포트 확인** — 모든 질문 완료 후 상세 리포트 및 PDF 다운로드

> 자세한 실행 방법은 [run.md](run.md) 참고
