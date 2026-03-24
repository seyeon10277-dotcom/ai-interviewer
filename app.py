import os
import json
import base64
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

from modules.ai_feedback import AIFeedbackModule
from modules.question_generator import QuestionGenerator
from modules.report_generator import ReportGenerator
from modules.auth import AuthModule, login_required

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ai-interviewer-secret-2024")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# 가벼운 모듈만 서버 시작시 초기화
ai_feedback = AIFeedbackModule()
question_generator = QuestionGenerator()
report_generator = ReportGenerator()
auth_module = AuthModule()

# 무거운 모듈은 None으로 초기화 (첫 요청시 로딩)
_speech_analyzer = None
_face_analyzer = None


def get_speech_analyzer():
    global _speech_analyzer
    if _speech_analyzer is None:
        from modules.speech_analyzer import SpeechAnalyzer
        _speech_analyzer = SpeechAnalyzer()
    return _speech_analyzer


def get_face_analyzer():
    global _face_analyzer
    if _face_analyzer is None:
        from modules.face_analyzer import FaceAnalyzer
        _face_analyzer = FaceAnalyzer()
    return _face_analyzer


# 세션별 면접 데이터 저장
interview_sessions: dict[str, dict] = {}


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("access_token"):
        return redirect("/")
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        try:
            result = auth_module.sign_in(email, password)
            session["access_token"] = result.session.access_token
            session["user_email"] = result.user.email
            return redirect("/")
        except Exception as e:
            error = "이메일 또는 비밀번호가 올바르지 않습니다."
            return render_template("login.html", error=error)
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("access_token"):
        return redirect("/")
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        if password != password_confirm:
            return render_template("signup.html", error="비밀번호가 일치하지 않습니다.")
        if len(password) < 6:
            return render_template("signup.html", error="비밀번호는 6자 이상이어야 합니다.")
        try:
            redirect_url = url_for("login", _external=True)
            result = auth_module.sign_up(email, password, redirect_url=redirect_url)
            if result.session:
                session["access_token"] = result.session.access_token
                session["user_email"] = result.user.email
                return redirect("/")
            return render_template("login.html", message="회원가입 완료! 이메일을 확인한 후 로그인해주세요.")
        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg:
                error = "이미 가입된 이메일입니다."
            else:
                error = f"회원가입 오류: {error_msg}"
            return render_template("signup.html", error=error)
    return render_template("signup.html")


@app.route("/logout")
def logout():
    try:
        auth_module.sign_out()
    except Exception:
        pass
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def index() -> str:
    return render_template("index.html", user_email=session.get("user_email", ""))


@app.route("/interview")
@login_required
def interview() -> str:
    return render_template("interview.html", user_email=session.get("user_email", ""))


@app.route("/report/<session_id>")
@login_required
def report(session_id: str) -> str:
    session_data = interview_sessions.get(session_id, {})
    return render_template("report.html", session_id=session_id, data=session_data, user_email=session.get("user_email", ""))


@app.route("/api/generate-questions", methods=["POST"])
@login_required
def generate_questions():
    data = request.get_json()
    company = data.get("company", "")
    position = data.get("position", "")
    job_type = data.get("job_type", "")
    try:
        questions = question_generator.generate(company, position, job_type)
        return jsonify({"success": True, "questions": questions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/get-report/<session_id>")
@login_required
def get_report(session_id: str):
    session_data = interview_sessions.get(session_id)
    if not session_data:
        return jsonify({"success": False, "error": "세션을 찾을 수 없습니다."}), 404
    return jsonify({"success": True, "report": session_data})


@app.route("/api/download-report/<session_id>")
@login_required
def download_report(session_id: str):
    session_data = interview_sessions.get(session_id)
    if not session_data:
        return jsonify({"success": False, "error": "세션을 찾을 수 없습니다."}), 404
    try:
        pdf_path = report_generator.generate_pdf(session_id, session_data)
        return send_file(pdf_path, as_attachment=True, download_name=f"면접리포트_{session_id}.pdf")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@socketio.on("connect")
def handle_connect():
    session_id = request.sid
    interview_sessions[session_id] = {
        "start_time": datetime.now().isoformat(),
        "questions": [],
        "answers": [],
        "feedback_list": [],
        "total_score": 0,
        "face_analysis": [],
        "speech_analysis": [],
    }
    emit("connected", {"session_id": session_id})


@socketio.on("disconnect")
def handle_disconnect():
    pass


@socketio.on("analyze_frame")
def handle_analyze_frame(data: dict):
    try:
        image_data = data.get("image", "")
        if not image_data:
            return
        if "," in image_data:
            image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        analysis = get_face_analyzer().analyze(image_bytes)
        emit("face_analysis_result", analysis)
    except Exception as e:
        emit("error", {"message": f"얼굴 분석 오류: {str(e)}"})


@socketio.on("analyze_speech")
def handle_analyze_speech(data: dict):
    try:
        audio_data = data.get("audio", "")
        transcript = data.get("transcript", "")
        if not transcript:
            return
        analysis = get_speech_analyzer().analyze(transcript, audio_data)
        emit("speech_analysis_result", analysis)
    except Exception as e:
        emit("error", {"message": f"음성 분석 오류: {str(e)}"})


@socketio.on("get_feedback")
def handle_get_feedback(data: dict):
    try:
        session_id = request.sid
        question = data.get("question", "")
        answer = data.get("transcript", "")
        company = data.get("company", "")
        position = data.get("position", "")
        if not answer:
            emit("feedback_result", {"error": "답변 내용이 없습니다.", "score": 0})
            return
        feedback = ai_feedback.get_feedback(question, answer, company, position)
        if session_id in interview_sessions:
            interview_sessions[session_id]["answers"].append({
                "question": question,
                "answer": answer,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            })
        emit("feedback_result", feedback)
    except Exception as e:
        emit("error", {"message": f"피드백 생성 오류: {str(e)}"})


@socketio.on("save_session_data")
def handle_save_session(data: dict):
    try:
        session_id = request.sid
        if session_id in interview_sessions:
            interview_sessions[session_id].update({
                "end_time": datetime.now().isoformat(),
                "company": data.get("company", ""),
                "position": data.get("position", ""),
                "speech_summary": data.get("speech_summary", {}),
                "face_summary": data.get("face_summary", {}),
            })
            answers = interview_sessions[session_id].get("answers", [])
            if answers:
                scores = [a["feedback"].get("score", 0) for a in answers if "feedback" in a]
                if scores:
                    interview_sessions[session_id]["total_score"] = round(sum(scores) / len(scores), 1)
        emit("session_saved", {"session_id": session_id})
    except Exception as e:
        emit("error", {"message": f"세션 저장 오류: {str(e)}"})


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    socketio.run(app, host="0.0.0.0", port=port, debug=debug)