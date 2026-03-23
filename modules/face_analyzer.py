import base64
import tempfile
import os
import numpy as np


class FaceAnalyzer:
    """MediaPipe 기반 실시간 얼굴 분석 모듈"""

    def __init__(self):
        self._mp = None
        self._face_mesh = None
        self._face_detection = None
        self._mp_drawing = None
        self._initialized = False

    def _init_mediapipe(self):
        """MediaPipe 지연 초기화"""
        if self._initialized:
            return

        try:
            import mediapipe as mp
            self._mp = mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
            self._face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.5
            )
            self._mp_drawing = mp.solutions.drawing_utils
            self._initialized = True
        except ImportError:
            self._initialized = False

    def analyze(self, image_bytes: bytes) -> dict:
        """이미지 바이트에서 얼굴 분석"""
        self._init_mediapipe()

        if not self._initialized:
            return self._fallback_result()

        try:
            import cv2

            # 바이트 -> numpy 배열 변환
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return self._fallback_result()

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = rgb_img.shape[:2]

            # 얼굴 감지
            detection_result = self._face_detection.process(rgb_img)
            if not detection_result.detections:
                return {
                    "face_detected": False,
                    "feedback": "얼굴이 감지되지 않습니다. 카메라 정면을 보세요.",
                    "eye_contact_score": 0,
                    "posture_score": 0,
                    "face_position": "감지 안됨"
                }

            # 얼굴 메시 분석
            mesh_result = self._face_mesh.process(rgb_img)

            eye_contact = self._analyze_eye_contact(mesh_result, h, w)
            posture = self._analyze_posture(detection_result, h, w)
            expression = self._analyze_expression(mesh_result)

            overall_score = round(
                eye_contact["score"] * 0.4 +
                posture["score"] * 0.4 +
                expression["score"] * 0.2
            )

            feedback_messages = []
            if eye_contact["score"] < 70:
                feedback_messages.append("카메라를 더 바라보세요.")
            if posture["score"] < 70:
                feedback_messages.append(posture.get("recommendation", "자세를 바르게 하세요."))
            if not feedback_messages:
                feedback_messages.append("훌륭한 자세입니다!")

            return {
                "face_detected": True,
                "eye_contact": eye_contact,
                "posture": posture,
                "expression": expression,
                "overall_score": overall_score,
                "feedback": " ".join(feedback_messages)
            }

        except Exception as e:
            return self._fallback_result(str(e))

    def _analyze_eye_contact(self, mesh_result, h: int, w: int) -> dict:
        """시선 방향 분석 (눈이 카메라를 바라보는지)"""
        if not mesh_result or not mesh_result.multi_face_landmarks:
            return {"score": 50, "direction": "감지 불가"}

        landmarks = mesh_result.multi_face_landmarks[0].landmark

        # 코 끝(1)과 눈 중심 랜드마크로 시선 방향 추정
        nose_tip = landmarks[1]
        left_eye_center = landmarks[468]  # 왼쪽 눈 중심
        right_eye_center = landmarks[473]  # 오른쪽 눈 중심

        # 얼굴 중심 대비 코 위치로 좌우 기울기 측정
        face_center_x = (left_eye_center.x + right_eye_center.x) / 2
        nose_offset_x = abs(nose_tip.x - face_center_x)

        # 상하 기울기
        nose_offset_y = abs(nose_tip.y - 0.5)

        # 정면 응시 점수 계산
        if nose_offset_x < 0.05 and nose_offset_y < 0.1:
            score = 95
            direction = "정면"
        elif nose_offset_x < 0.1 and nose_offset_y < 0.15:
            score = 75
            direction = "약간 측면"
        else:
            score = 50
            direction = "측면"

        return {
            "score": score,
            "direction": direction,
            "horizontal_offset": round(nose_offset_x, 3),
            "vertical_offset": round(nose_offset_y, 3)
        }

    def _analyze_posture(self, detection_result, h: int, w: int) -> dict:
        """얼굴 위치로 자세 분석"""
        detection = detection_result.detections[0]
        bbox = detection.location_data.relative_bounding_box

        face_center_x = bbox.xmin + bbox.width / 2
        face_center_y = bbox.ymin + bbox.height / 2
        face_size = bbox.width * bbox.height

        # 얼굴 크기 (너무 가깝거나 멀리 있는지)
        if face_size < 0.05:
            size_feedback = "카메라에 더 가까이 앉으세요."
            size_score = 60
        elif face_size > 0.4:
            size_feedback = "카메라에서 조금 멀어지세요."
            size_score = 60
        else:
            size_feedback = "적절한 거리입니다."
            size_score = 90

        # 얼굴 중앙 위치
        h_offset = abs(face_center_x - 0.5)
        if h_offset < 0.1:
            position_feedback = "화면 중앙에 잘 위치해 있습니다."
            position_score = 95
        elif h_offset < 0.2:
            position_feedback = "카메라 정면 중앙을 유지하세요."
            position_score = 75
        else:
            position_feedback = "화면 가운데에 얼굴을 위치시키세요."
            position_score = 50

        overall_score = round((size_score + position_score) / 2)

        return {
            "score": overall_score,
            "face_size": round(face_size, 3),
            "face_center_x": round(face_center_x, 3),
            "face_center_y": round(face_center_y, 3),
            "recommendation": f"{size_feedback} {position_feedback}"
        }

    def _analyze_expression(self, mesh_result) -> dict:
        """표정 분석 (긴장감, 자연스러움)"""
        if not mesh_result or not mesh_result.multi_face_landmarks:
            return {"score": 70, "expression": "감지 불가"}

        landmarks = mesh_result.multi_face_landmarks[0].landmark

        # 입꼬리 랜드마크로 미소 감지
        left_mouth = landmarks[61]
        right_mouth = landmarks[291]
        mouth_top = landmarks[13]
        mouth_bottom = landmarks[14]

        # 입 열림 정도
        mouth_open = abs(mouth_top.y - mouth_bottom.y)

        # 입꼬리 높이 차이 (미소 지표)
        mouth_symmetry = abs(left_mouth.y - right_mouth.y)

        if mouth_symmetry < 0.02 and mouth_open < 0.05:
            expression = "자연스러운 표정"
            score = 85
        elif mouth_open > 0.08:
            expression = "입을 크게 벌리고 있음"
            score = 70
        else:
            expression = "보통"
            score = 75

        return {
            "score": score,
            "expression": expression,
            "mouth_open_ratio": round(mouth_open, 3)
        }

    def _fallback_result(self, error: str = "") -> dict:
        """MediaPipe 사용 불가 시 기본 결과"""
        return {
            "face_detected": True,
            "eye_contact": {"score": 70, "direction": "분석 중"},
            "posture": {"score": 70, "recommendation": "자세를 바르게 유지하세요."},
            "expression": {"score": 70, "expression": "분석 중"},
            "overall_score": 70,
            "feedback": "카메라 정면을 바라보고 바른 자세를 유지하세요.",
            "error": error
        }
