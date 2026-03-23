import os
from datetime import datetime


class ReportGenerator:
    """면접 결과 PDF 리포트 생성 모듈"""

    def __init__(self):
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_pdf(self, session_id: str, session_data: dict) -> str:
        """면접 결과 PDF 생성"""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()

            # 기본 폰트 설정 (유니코드 지원을 위해 별도 폰트 필요)
            pdf.set_font("Helvetica", size=12)

            self._add_header(pdf, session_data)
            self._add_overall_score(pdf, session_data)
            self._add_qa_section(pdf, session_data)
            self._add_speech_analysis(pdf, session_data)
            self._add_improvement_plan(pdf, session_data)

            output_path = os.path.join(self.reports_dir, f"report_{session_id}.pdf")
            pdf.output(output_path)
            return output_path

        except Exception as e:
            raise Exception(f"PDF 생성 실패: {str(e)}")

    def _add_header(self, pdf, session_data: dict):
        """헤더 섹션 추가"""
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 15, "AI Interview Practice Report", ln=True, align="C")

        pdf.set_font("Helvetica", size=11)
        company = session_data.get("company", "Unknown")
        position = session_data.get("position", "Unknown")
        date = session_data.get("start_time", datetime.now().isoformat())[:10]

        pdf.cell(0, 8, f"Company: {company} | Position: {position} | Date: {date}", ln=True, align="C")
        pdf.ln(8)

    def _add_overall_score(self, pdf, session_data: dict):
        """전체 점수 섹션"""
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Overall Score", ln=True)
        pdf.set_font("Helvetica", size=11)

        total_score = session_data.get("total_score", 0)
        pdf.cell(0, 8, f"Total Score: {total_score}/100", ln=True)

        speech_summary = session_data.get("speech_summary", {})
        if speech_summary:
            speech_score = speech_summary.get("overall_speech_score", 0)
            pdf.cell(0, 8, f"Speech Score: {speech_score}/100", ln=True)

        face_summary = session_data.get("face_summary", {})
        if face_summary:
            face_score = face_summary.get("overall_score", 0)
            pdf.cell(0, 8, f"Face/Posture Score: {face_score}/100", ln=True)

        pdf.ln(5)

    def _add_qa_section(self, pdf, session_data: dict):
        """Q&A 피드백 섹션"""
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Q&A Feedback", ln=True)

        answers = session_data.get("answers", [])
        for i, item in enumerate(answers, 1):
            pdf.set_font("Helvetica", "B", 11)
            question = item.get("question", "")[:80]
            pdf.multi_cell(0, 7, f"Q{i}: {question}")

            pdf.set_font("Helvetica", size=10)
            feedback = item.get("feedback", {})
            score = feedback.get("score", 0)
            overall = feedback.get("overall_feedback", "")[:120]

            pdf.cell(0, 6, f"Score: {score}/100", ln=True)
            if overall:
                pdf.multi_cell(0, 6, f"Feedback: {overall}")
            pdf.ln(3)

    def _add_speech_analysis(self, pdf, session_data: dict):
        """음성 분석 섹션"""
        speech_summary = session_data.get("speech_summary", {})
        if not speech_summary:
            return

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Speech Analysis", ln=True)
        pdf.set_font("Helvetica", size=11)

        filler = speech_summary.get("filler_analysis", {})
        if filler:
            pdf.cell(0, 7, f"Filler Words: {filler.get('total_count', 0)} ({filler.get('severity', '')})", ln=True)

        speed = speech_summary.get("speed_analysis", {})
        if speed:
            pdf.cell(0, 7, f"Speaking Speed: {speed.get('speed_level', '')} ({speed.get('words_per_minute', 0)} wpm)", ln=True)

        confidence = speech_summary.get("confidence_analysis", {})
        if confidence:
            pdf.cell(0, 7, f"Confidence: {confidence.get('confidence_level', '')} ({confidence.get('confidence_score', 0)}/100)", ln=True)

        pdf.ln(5)

    def _add_improvement_plan(self, pdf, session_data: dict):
        """개선 계획 섹션"""
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Improvement Plan", ln=True)
        pdf.set_font("Helvetica", size=11)

        answers = session_data.get("answers", [])
        all_improvements: list[str] = []
        for item in answers:
            feedback = item.get("feedback", {})
            improvements = feedback.get("improvements", [])
            all_improvements.extend(improvements[:2])

        seen: set[str] = set()
        unique_improvements = []
        for imp in all_improvements:
            if imp not in seen:
                seen.add(imp)
                unique_improvements.append(imp)

        for i, imp in enumerate(unique_improvements[:5], 1):
            pdf.multi_cell(0, 7, f"{i}. {imp[:100]}")

        pdf.ln(5)
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 7, f"Generated by AI Interviewer - {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
