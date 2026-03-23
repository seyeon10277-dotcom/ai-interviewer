import os
import json
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class QuestionGenerator:
    """회사/직무 기반 맞춤형 면접 질문 생성 모듈"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    def generate(self, company: str, position: str, job_type: str = "") -> list[dict]:
        """회사와 직무에 맞는 면접 질문 생성"""

        # 실제 면접 질문 수집 시도
        real_questions = self._collect_real_questions(company, position)

        # AI로 예상 질문 생성
        ai_questions = self._generate_ai_questions(company, position, job_type, real_questions)

        return ai_questions

    def _collect_real_questions(self, company: str, position: str) -> list[str]:
        """웹에서 실제 면접 질문 수집 (공개 데이터 기반)"""
        real_questions = []
        try:
            # 잡플래닛, 링크드인 등 공개 데이터 검색
            search_query = f"{company} {position} 면접 질문"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            # 공개 검색 API 사용 (실제 서비스에서는 API 키 필요)
            response = requests.get(
                f"https://www.google.com/search?q={search_query}&hl=ko",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # 검색 결과에서 질문 패턴 추출
                texts = soup.get_text()
                lines = [line.strip() for line in texts.split("\n") if "?" in line and len(line) > 10]
                real_questions = lines[:5]
        except Exception:
            pass

        return real_questions

    def _generate_ai_questions(
        self,
        company: str,
        position: str,
        job_type: str,
        real_questions: list[str]
    ) -> list[dict]:
        """GPT로 맞춤형 면접 질문 생성"""

        real_q_text = ""
        if real_questions:
            real_q_text = f"\n실제 수집된 질문 참고:\n" + "\n".join(real_questions[:5])

        job_context = f"직무 분야: {job_type}" if job_type else ""

        prompt = f"""당신은 {company}의 시니어 면접관입니다.
지원 직무: {position}
{job_context}
{real_q_text}

다음 카테고리별로 총 10개의 면접 질문을 JSON 배열로 생성해주세요.
각 질문은 실제 면접에서 자주 나오는 수준으로 구체적이고 심층적이어야 합니다.

[
  {{
    "id": 1,
    "category": "인성/자기소개",
    "question": "질문 내용",
    "difficulty": "쉬움/보통/어려움",
    "key_points": ["평가 포인트1", "평가 포인트2"],
    "time_limit": 120,
    "tips": "답변 팁"
  }},
  ...
]

카테고리 배분:
- 인성/자기소개: 2개
- 직무 역량: 3개  
- 경험/프로젝트: 2개
- 회사 지원 동기: 1개
- 상황 판단/문제해결: 2개

JSON 배열만 반환하세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "면접 질문 전문가입니다. 유효한 JSON 배열만 반환하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2500
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            questions = json.loads(content)
            return questions

        except Exception as e:
            # 기본 질문 반환
            return self._get_default_questions(company, position)

    def _get_default_questions(self, company: str, position: str) -> list[dict]:
        """API 오류 시 기본 질문 제공"""
        return [
            {
                "id": 1,
                "category": "인성/자기소개",
                "question": f"자기소개를 1분 내외로 해주세요.",
                "difficulty": "쉬움",
                "key_points": ["명확한 구조", "핵심 역량 강조"],
                "time_limit": 90,
                "tips": "이름, 학력/경력, 핵심 역량, 지원 동기 순으로 말하세요."
            },
            {
                "id": 2,
                "category": "회사 지원 동기",
                "question": f"{company}에 지원한 이유가 무엇인가요?",
                "difficulty": "보통",
                "key_points": ["회사 이해도", "진정성"],
                "time_limit": 120,
                "tips": "회사의 비전과 자신의 목표를 연결하세요."
            },
            {
                "id": 3,
                "category": "직무 역량",
                "question": f"{position} 직무에서 가장 중요한 역량은 무엇이라고 생각하나요?",
                "difficulty": "보통",
                "key_points": ["직무 이해도", "본인 역량 연결"],
                "time_limit": 120,
                "tips": "구체적인 사례와 함께 설명하세요."
            },
            {
                "id": 4,
                "category": "경험/프로젝트",
                "question": "가장 도전적이었던 프로젝트나 업무 경험을 말씀해주세요.",
                "difficulty": "보통",
                "key_points": ["문제 해결 능력", "성장"],
                "time_limit": 180,
                "tips": "STAR 기법(상황-과제-행동-결과)으로 답변하세요."
            },
            {
                "id": 5,
                "category": "상황 판단/문제해결",
                "question": "팀원과 의견 충돌이 발생했을 때 어떻게 해결하셨나요?",
                "difficulty": "보통",
                "key_points": ["협업 능력", "갈등 해결"],
                "time_limit": 120,
                "tips": "실제 사례를 들어 구체적으로 설명하세요."
            }
        ]
