import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AIFeedbackModule:
    """GPT 기반 면접 답변 피드백 모듈"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    def get_feedback(
        self,
        question: str,
        answer: str,
        company: str = "",
        position: str = ""
    ) -> dict:
        """면접 답변에 대한 종합 피드백 생성"""

        context = ""
        if company and position:
            context = f"지원 회사: {company}, 지원 직무: {position}\n"

        prompt = f"""당신은 경험 많은 면접관입니다. 다음 면접 답변을 평가해주세요.

{context}
면접 질문: {question}
지원자 답변: {answer}

다음 기준으로 평가하고 JSON 형식으로 응답해주세요:

{{
  "score": 0~100 점수,
  "logic_score": 0~100 논리성 점수,
  "specificity_score": 0~100 구체성 점수,
  "relevance_score": 0~100 질문 적합성 점수,
  "overall_feedback": "전체적인 피드백 (2~3문장)",
  "strengths": ["강점1", "강점2"],
  "improvements": ["개선점1", "개선점2"],
  "logic_analysis": "논리적 흐름 분석",
  "specificity_analysis": "구체성 분석",
  "suggested_answer_structure": "더 나은 답변 구조 제안",
  "star_method_check": true/false (STAR 기법 사용 여부),
  "key_missing_points": ["빠진 핵심 내용1", "빠진 핵심 내용2"]
}}

JSON만 반환하고 다른 텍스트는 포함하지 마세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 전문 면접 코치입니다. 반드시 유효한 JSON만 반환하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()
            # JSON 파싱
            import json
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            feedback = json.loads(content)
            return feedback

        except Exception as e:
            return {
                "score": 50,
                "logic_score": 50,
                "specificity_score": 50,
                "relevance_score": 50,
                "overall_feedback": f"피드백 생성 중 오류가 발생했습니다: {str(e)}",
                "strengths": [],
                "improvements": ["API 연결을 확인해주세요"],
                "logic_analysis": "",
                "specificity_analysis": "",
                "suggested_answer_structure": "",
                "star_method_check": False,
                "key_missing_points": []
            }

    def analyze_overall_performance(self, answers: list[dict]) -> dict:
        """전체 면접 성과 종합 분석"""

        if not answers:
            return {}

        qa_text = ""
        for i, item in enumerate(answers, 1):
            qa_text += f"\n[질문 {i}] {item.get('question', '')}\n"
            qa_text += f"[답변 {i}] {item.get('answer', '')}\n"
            qa_text += f"[점수 {i}] {item.get('feedback', {}).get('score', 0)}점\n"

        prompt = f"""다음 면접 전체 Q&A를 분석하고 종합 평가를 JSON으로 제공해주세요:

{qa_text}

{{
  "overall_score": 전체 평균 점수,
  "performance_level": "우수/양호/보통/미흡 중 하나",
  "strongest_area": "가장 잘한 영역",
  "weakest_area": "가장 개선이 필요한 영역",
  "consistency": "답변 일관성 평가",
  "communication_style": "의사소통 스타일 분석",
  "final_recommendation": "최종 합격 가능성 및 조언",
  "improvement_plan": ["개선 계획1", "개선 계획2", "개선 계획3"],
  "interview_readiness": 0~100 면접 준비도
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "면접 종합 평가 전문가입니다. 유효한 JSON만 반환하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            import json
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception:
            return {}
