import re
import base64
import tempfile
import os
from typing import Optional


class SpeechAnalyzer:
    """음성 분석 모듈 - 습관어, 말하기 속도, 톤, 자신감 분석"""

    # 한국어/영어 습관어 목록
    FILLER_WORDS_KO = [
        "음", "어", "아", "그", "뭐", "저", "에", "그러니까", "그냥",
        "일단", "뭔가", "약간", "사실", "근데", "그게", "이게"
    ]
    FILLER_WORDS_EN = ["um", "uh", "ah", "er", "like", "you know", "so", "basically", "literally"]

    def analyze(self, transcript: str, audio_data: str = "") -> dict:
        """텍스트 기반 음성 분석 (전사 텍스트 + 오디오 데이터)"""

        if not transcript:
            return self._empty_result()

        # 습관어 분석
        filler_analysis = self._analyze_fillers(transcript)

        # 말하기 속도 분석
        speed_analysis = self._analyze_speed(transcript, audio_data)

        # 문장 구조 분석
        structure_analysis = self._analyze_structure(transcript)

        # 자신감 지표 분석
        confidence_analysis = self._analyze_confidence(transcript)

        # 음성 톤 분석 (오디오 데이터가 있는 경우)
        tone_analysis = {}
        if audio_data:
            tone_analysis = self._analyze_tone(audio_data)

        overall_speech_score = self._calculate_speech_score(
            filler_analysis, speed_analysis, confidence_analysis
        )

        return {
            "filler_analysis": filler_analysis,
            "speed_analysis": speed_analysis,
            "structure_analysis": structure_analysis,
            "confidence_analysis": confidence_analysis,
            "tone_analysis": tone_analysis,
            "overall_speech_score": overall_speech_score,
            "transcript_length": len(transcript),
            "word_count": len(transcript.split())
        }

    def _analyze_fillers(self, transcript: str) -> dict:
        """습관어 빈도 분석"""
        text_lower = transcript.lower()
        found_fillers: dict[str, int] = {}

        # 한국어 습관어 검사
        for filler in self.FILLER_WORDS_KO:
            pattern = re.compile(r'\b' + re.escape(filler) + r'\b', re.IGNORECASE)
            count = len(pattern.findall(text_lower))
            if count > 0:
                found_fillers[filler] = count

        # 영어 습관어 검사
        for filler in self.FILLER_WORDS_EN:
            pattern = re.compile(r'\b' + re.escape(filler) + r'\b', re.IGNORECASE)
            count = len(pattern.findall(text_lower))
            if count > 0:
                found_fillers[filler] = count

        total_fillers = sum(found_fillers.values())
        word_count = max(len(transcript.split()), 1)
        filler_ratio = round((total_fillers / word_count) * 100, 1)

        # 습관어 심각도 평가
        if filler_ratio < 3:
            severity = "양호"
            severity_color = "green"
        elif filler_ratio < 7:
            severity = "주의"
            severity_color = "yellow"
        else:
            severity = "개선 필요"
            severity_color = "red"

        return {
            "found_fillers": found_fillers,
            "total_count": total_fillers,
            "filler_ratio": filler_ratio,
            "severity": severity,
            "severity_color": severity_color,
            "recommendation": self._get_filler_recommendation(found_fillers, filler_ratio)
        }

    def _analyze_speed(self, transcript: str, audio_data: str = "") -> dict:
        """말하기 속도 분석"""
        word_count = len(transcript.split())

        # 오디오 길이 추정 (데이터가 없는 경우 평균 속도 기반)
        estimated_duration = word_count / 3.5  # 한국어 평균 3.5 음절/초 기준

        words_per_minute = round((word_count / estimated_duration) * 60) if estimated_duration > 0 else 0

        # 적정 속도 판정 (한국어 면접 기준: 150~200 음절/분)
        if words_per_minute < 100:
            speed_level = "너무 느림"
            speed_score = 60
            speed_recommendation = "조금 더 빠르게 말해보세요. 너무 느리면 자신감이 부족해 보일 수 있습니다."
        elif words_per_minute <= 180:
            speed_level = "적정"
            speed_score = 95
            speed_recommendation = "말하기 속도가 적절합니다. 현재 페이스를 유지하세요."
        elif words_per_minute <= 220:
            speed_level = "약간 빠름"
            speed_score = 80
            speed_recommendation = "조금 천천히 말하면 더 명확하게 전달될 것입니다."
        else:
            speed_level = "너무 빠름"
            speed_score = 60
            speed_recommendation = "말하기 속도가 너무 빠릅니다. 면접관이 이해하기 어려울 수 있습니다."

        return {
            "words_per_minute": words_per_minute,
            "word_count": word_count,
            "speed_level": speed_level,
            "speed_score": speed_score,
            "recommendation": speed_recommendation
        }

    def _analyze_structure(self, transcript: str) -> dict:
        """답변 구조 분석 (STAR 기법, 논리적 구조)"""
        sentences = re.split(r'[.!?。]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]

        # STAR 기법 키워드 감지
        star_keywords = {
            "situation": ["상황", "당시", "그때", "배경"],
            "task": ["과제", "목표", "역할", "담당"],
            "action": ["했습니다", "진행했", "수행했", "해결했", "제가"],
            "result": ["결과", "성과", "달성", "개선", "향상"]
        }

        star_scores: dict[str, bool] = {}
        for key, keywords in star_keywords.items():
            star_scores[key] = any(kw in transcript for kw in keywords)

        star_count = sum(star_scores.values())
        uses_star = star_count >= 3

        # 문장 길이 분석
        avg_sentence_length = round(
            sum(len(s.split()) for s in sentences) / max(len(sentences), 1), 1
        )

        return {
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_length,
            "uses_star_method": uses_star,
            "star_components": star_scores,
            "structure_score": 90 if uses_star else 60
        }

    def _analyze_confidence(self, transcript: str) -> dict:
        """텍스트 기반 자신감 지표 분석"""
        # 자신감 있는 표현
        confident_patterns = [
            "확신", "반드시", "꼭", "분명히", "자신있게", "할 수 있",
            "경험이 있", "해왔습니다", "성공적으로"
        ]

        # 자신감 없는 표현
        uncertain_patterns = [
            "잘 모르겠", "아마도", "혹시", "그럴 것 같", "어쩌면",
            "잘못된 것 같", "틀릴 수도", "별로"
        ]

        confident_count = sum(1 for p in confident_patterns if p in transcript)
        uncertain_count = sum(1 for p in uncertain_patterns if p in transcript)

        # 자신감 점수 계산
        confidence_score = 70 + (confident_count * 5) - (uncertain_count * 10)
        confidence_score = max(0, min(100, confidence_score))

        if confidence_score >= 80:
            confidence_level = "높음"
        elif confidence_score >= 60:
            confidence_level = "보통"
        else:
            confidence_level = "낮음"

        return {
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "confident_expressions": confident_count,
            "uncertain_expressions": uncertain_count,
            "recommendation": self._get_confidence_recommendation(confidence_score)
        }

    def _analyze_tone(self, audio_data: str) -> dict:
        """오디오 데이터 기반 음성 톤 분석"""
        try:
            import numpy as np
            import librosa

            # base64 오디오 데이터 디코딩
            audio_bytes = base64.b64decode(audio_data)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            y, sr = librosa.load(tmp_path, sr=None)
            os.unlink(tmp_path)

            # 피치 분석
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[magnitudes > np.max(magnitudes) * 0.1]
            avg_pitch = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0

            # 에너지/볼륨 분석
            rms = librosa.feature.rms(y=y)
            avg_volume = float(np.mean(rms))

            # 음성 변화율 (단조롭지 않은 정도)
            pitch_variation = float(np.std(pitch_values)) if len(pitch_values) > 0 else 0

            # 톤 평가
            if avg_pitch > 200:
                tone_type = "높음"
            elif avg_pitch > 130:
                tone_type = "보통"
            else:
                tone_type = "낮음"

            return {
                "avg_pitch": round(avg_pitch, 1),
                "tone_type": tone_type,
                "avg_volume": round(avg_volume * 100, 2),
                "pitch_variation": round(pitch_variation, 1),
                "monotone_risk": pitch_variation < 20,
                "recommendation": "목소리 변화를 주어 생동감 있게 말하세요." if pitch_variation < 20 else "자연스러운 톤 변화가 좋습니다."
            }

        except Exception:
            return {
                "avg_pitch": 0,
                "tone_type": "분석 불가",
                "avg_volume": 0,
                "pitch_variation": 0,
                "monotone_risk": False,
                "recommendation": "음성 파일을 다시 확인해주세요."
            }

    def _calculate_speech_score(
        self,
        filler_analysis: dict,
        speed_analysis: dict,
        confidence_analysis: dict
    ) -> int:
        """전체 말하기 점수 계산"""
        filler_score = max(0, 100 - filler_analysis.get("filler_ratio", 0) * 5)
        speed_score = speed_analysis.get("speed_score", 70)
        confidence_score = confidence_analysis.get("confidence_score", 70)

        return round((filler_score * 0.3 + speed_score * 0.3 + confidence_score * 0.4))

    def _get_filler_recommendation(self, found_fillers: dict, filler_ratio: float) -> str:
        """습관어 개선 권고사항"""
        if not found_fillers:
            return "습관어 사용이 없습니다. 훌륭합니다!"

        top_fillers = sorted(found_fillers.items(), key=lambda x: x[1], reverse=True)[:3]
        filler_list = ", ".join([f'"{f}"({c}회)' for f, c in top_fillers])

        return f"자주 사용하는 습관어: {filler_list}. 답변 전 3초간 생각하는 습관을 기르세요."

    def _get_confidence_recommendation(self, score: int) -> str:
        """자신감 개선 권고사항"""
        if score >= 80:
            return "자신감 있는 표현을 잘 사용하고 있습니다."
        elif score >= 60:
            return "조금 더 확신에 찬 표현을 사용해보세요. '~할 수 있습니다', '~한 경험이 있습니다'를 활용하세요."
        else:
            return "불확실한 표현을 줄이고, 경험과 역량에 대해 자신감 있게 말하세요."

    def _empty_result(self) -> dict:
        """빈 분석 결과"""
        return {
            "filler_analysis": {"total_count": 0, "filler_ratio": 0, "severity": "분석 불가"},
            "speed_analysis": {"words_per_minute": 0, "speed_level": "분석 불가"},
            "structure_analysis": {"uses_star_method": False},
            "confidence_analysis": {"confidence_score": 0},
            "tone_analysis": {},
            "overall_speech_score": 0,
            "word_count": 0
        }
