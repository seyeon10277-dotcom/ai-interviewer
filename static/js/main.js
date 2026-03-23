/**
 * AI 면접관 - 메인 JavaScript
 * 카메라(MediaPipe), 마이크(Web Speech API), WebSocket 통합 제어
 */

// ===== 전역 상태 =====
const state = {
  socket: null,
  sessionId: null,
  questions: [],
  currentIndex: 0,
  isRecording: false,
  transcript: "",
  finalTranscript: "",
  recognition: null,
  cameraStream: null,
  frameAnalysisInterval: null,
  timerInterval: null,
  timeLeft: 180,
  speechDataAccum: {
    fillerTotal: 0,
    wordCount: 0,
    speedSamples: []
  },
  faceDataAccum: {
    eyeScores: [],
    postureScores: []
  },
  sessionAnswers: []
};

// ===== 초기화 =====
document.addEventListener("DOMContentLoaded", () => {
  initSocketIO();
  loadQuestions();
  initCamera();
  initSpeechRecognition();
  updateCompanyDisplay();
});

// ===== WebSocket 초기화 =====
function initSocketIO() {
  state.socket = io();

  state.socket.on("connected", (data) => {
    state.sessionId = data.session_id;
  });

  // 얼굴 분석 결과 수신
  state.socket.on("face_analysis_result", (data) => {
    updateFaceMetrics(data);
  });

  // 음성 분석 결과 수신
  state.socket.on("speech_analysis_result", (data) => {
    updateSpeechMetrics(data);
  });

  // GPT 피드백 결과 수신
  state.socket.on("feedback_result", (data) => {
    renderFeedback(data);
    enableNextButton();
  });

  // 세션 저장 완료
  state.socket.on("session_saved", (data) => {
    // 리포트 페이지로 이동
    const reportData = buildReportData();
    sessionStorage.setItem("reportData", JSON.stringify(reportData));
    window.location.href = `/report/${data.session_id}`;
  });

  state.socket.on("error", (data) => {
    console.error("서버 오류:", data.message);
  });
}

// ===== 질문 로드 =====
function loadQuestions() {
  const raw = sessionStorage.getItem("questions");
  if (!raw) {
    // 기본 질문으로 대체
    state.questions = getDefaultQuestions();
  } else {
    state.questions = JSON.parse(raw);
  }
  displayQuestion(0);
}

function displayQuestion(index) {
  if (index >= state.questions.length) {
    endInterview();
    return;
  }

  const q = state.questions[index];
  document.getElementById("question-text").textContent = q.question || "질문을 불러올 수 없습니다.";
  document.getElementById("q-category").textContent = q.category || "일반";
  document.getElementById("q-difficulty").textContent = q.difficulty || "보통";
  document.getElementById("q-number").textContent = `Q${index + 1}`;

  // 팁 표시
  const tipsEl = document.getElementById("question-tips");
  if (q.tips) {
    document.getElementById("tips-text").textContent = q.tips;
    tipsEl.style.display = "flex";
  } else {
    tipsEl.style.display = "none";
  }

  // 진행 표시 업데이트
  const total = state.questions.length;
  document.getElementById("question-counter").textContent = `${index + 1} / ${total}`;
  const pct = ((index + 1) / total) * 100;
  document.getElementById("progress-fill").style.width = pct + "%";

  // 타이머 초기화
  resetTimer(q.time_limit || 180);

  // 트랜스크립트 초기화
  state.transcript = "";
  state.finalTranscript = "";
  document.getElementById("transcript-text").textContent = "답변을 시작하면 여기에 텍스트가 표시됩니다...";

  // 피드백 초기화
  resetFeedbackPanel();

  // 다음 버튼 비활성화
  document.getElementById("btn-next").disabled = true;
}

// ===== 카메라 초기화 =====
async function initCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: "user" },
      audio: false
    });

    state.cameraStream = stream;
    const video = document.getElementById("camera-feed");
    video.srcObject = stream;

    // 카메라 연결 후 프레임 분석 시작
    video.addEventListener("loadeddata", () => {
      startFrameAnalysis();
    });

  } catch (err) {
    console.error("카메라 접근 오류:", err);
    document.getElementById("camera-feedback").textContent =
      "카메라 접근 권한이 없습니다. 브라우저 설정을 확인하세요.";
  }
}

// ===== 실시간 프레임 분석 (2초마다) =====
function startFrameAnalysis() {
  state.frameAnalysisInterval = setInterval(() => {
    captureAndAnalyzeFrame();
  }, 2000);
}

function captureAndAnalyzeFrame() {
  const video = document.getElementById("camera-feed");
  const canvas = document.getElementById("face-canvas");

  if (!video.videoWidth) return;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);

  const imageData = canvas.toDataURL("image/jpeg", 0.7);

  if (state.socket && state.socket.connected) {
    state.socket.emit("analyze_frame", { image: imageData });
  }
}

// ===== 얼굴 분석 결과 업데이트 =====
function updateFaceMetrics(data) {
  if (!data) return;

  const eyeScore = data.eye_contact?.score || 70;
  const postureScore = data.posture?.score || 70;
  const expressionScore = data.expression?.score || 70;

  // 게이지 업데이트
  animateBar("eye-fill", eyeScore);
  animateBar("posture-fill", postureScore);
  animateBar("expression-fill", expressionScore);

  document.getElementById("eye-score").textContent = eyeScore;
  document.getElementById("posture-score").textContent = postureScore;
  document.getElementById("expression-score").textContent = expressionScore;

  // 얼굴 감지 상태
  const statusEl = document.getElementById("face-status");
  if (data.face_detected) {
    statusEl.innerHTML = '<span class="status-dot green"></span><span>얼굴 감지됨</span>';
  } else {
    statusEl.innerHTML = '<span class="status-dot red"></span><span>얼굴 감지 안됨</span>';
  }

  // 피드백 메시지
  if (data.feedback) {
    document.getElementById("camera-feedback").textContent = data.feedback;
  }

  // 누적 저장
  state.faceDataAccum.eyeScores.push(eyeScore);
  state.faceDataAccum.postureScores.push(postureScore);
}

// ===== 음성 인식 초기화 (Web Speech API) =====
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    document.getElementById("speech-status-text").textContent =
      "이 브라우저는 음성 인식을 지원하지 않습니다. Chrome을 사용해주세요.";
    return;
  }

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
  state.recognition.lang = "ko-KR";
  state.recognition.maxAlternatives = 1;

  state.recognition.onstart = () => {
    document.getElementById("speech-status-text").textContent = "🔴 음성 인식 중...";
    document.getElementById("speech-wave").classList.add("active");
    document.getElementById("recording-badge").style.display = "flex";
  };

  state.recognition.onresult = (event) => {
    let interim = "";
    let final = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const text = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        final += text;
      } else {
        interim += text;
      }
    }

    if (final) {
      state.finalTranscript += final;
      // 음성 분석 요청 (최종 텍스트)
      requestSpeechAnalysis(state.finalTranscript);
    }

    state.transcript = state.finalTranscript + interim;
    document.getElementById("transcript-text").textContent =
      state.transcript || "답변을 말해주세요...";
  };

  state.recognition.onerror = (event) => {
    if (event.error !== "no-speech") {
      console.error("음성 인식 오류:", event.error);
    }
  };

  state.recognition.onend = () => {
    if (state.isRecording) {
      // 녹음 중이면 자동 재시작
      try { state.recognition.start(); } catch {}
    } else {
      document.getElementById("speech-wave").classList.remove("active");
      document.getElementById("recording-badge").style.display = "none";
      document.getElementById("speech-status-text").textContent = "마이크 버튼을 눌러 답변하세요";
    }
  };
}

// ===== 마이크 토글 =====
function toggleMic() {
  if (!state.recognition) {
    alert("이 브라우저는 음성 인식을 지원하지 않습니다. Chrome을 사용해주세요.");
    return;
  }

  if (!state.isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
}

function startRecording() {
  state.isRecording = true;
  state.transcript = "";
  state.finalTranscript = "";

  document.getElementById("btn-mic").classList.add("recording");
  document.getElementById("mic-text").textContent = "답변 중지";
  document.getElementById("transcript-text").textContent = "듣고 있습니다...";

  try {
    state.recognition.start();
  } catch {}

  // 타이머 시작
  startTimer();
}

function stopRecording() {
  state.isRecording = false;

  document.getElementById("btn-mic").classList.remove("recording");
  document.getElementById("mic-text").textContent = "답변 시작";

  try {
    state.recognition.stop();
  } catch {}

  stopTimer();

  // 답변이 있으면 피드백 요청
  if (state.finalTranscript.trim()) {
    requestGPTFeedback();
    document.getElementById("btn-next").disabled = false;
  }
}

// ===== 음성 분석 요청 =====
function requestSpeechAnalysis(transcript) {
  if (!state.socket || !transcript) return;

  state.socket.emit("analyze_speech", {
    transcript: transcript
  });
}

// ===== 음성 분석 결과 업데이트 =====
function updateSpeechMetrics(data) {
  if (!data) return;

  const speed = data.speed_analysis || {};
  const filler = data.filler_analysis || {};
  const confidence = data.confidence_analysis || {};
  const tone = data.tone_analysis || {};

  document.getElementById("speed-display").textContent =
    speed.speed_level || "분석 중";

  const fillerCount = filler.total_count || 0;
  const fillerEl = document.getElementById("filler-display");
  fillerEl.textContent = `${fillerCount}회`;
  if (fillerCount > 5) {
    fillerEl.style.color = "#ef4444";
  } else if (fillerCount > 2) {
    fillerEl.style.color = "#f59e0b";
  } else {
    fillerEl.style.color = "#10b981";
  }

  document.getElementById("confidence-display").textContent =
    confidence.confidence_level || "분석 중";

  document.getElementById("tone-display").textContent =
    tone.tone_type || "분석 중";

  // 누적 데이터 저장
  state.speechDataAccum.fillerTotal = fillerCount;
  state.speechDataAccum.wordCount = data.word_count || 0;
  if (speed.words_per_minute) {
    state.speechDataAccum.speedSamples.push(speed.words_per_minute);
  }
}

// ===== GPT 피드백 요청 =====
function requestGPTFeedback() {
  if (!state.socket || !state.finalTranscript.trim()) return;

  const q = state.questions[state.currentIndex] || {};

  // 로딩 상태 표시
  document.getElementById("feedback-content").innerHTML = `
    <div class="feedback-loading">
      <div class="loading-spinner-lg"></div>
      <p>AI가 분석 중입니다...</p>
    </div>
  `;

  state.socket.emit("get_feedback", {
    question: q.question || "",
    transcript: state.finalTranscript,
    company: sessionStorage.getItem("company") || "",
    position: sessionStorage.getItem("position") || ""
  });
}

// ===== 피드백 렌더링 =====
function renderFeedback(data) {
  if (!data) return;

  const score = data.score || 0;
  const scoreColor = score >= 80 ? "#10b981" : score >= 60 ? "#3b82f6" : "#ef4444";

  // 점수 배지
  document.getElementById("feedback-score").textContent = `${score}점`;
  document.getElementById("feedback-score").style.background = scoreColor;

  // 전체 피드백 텍스트
  document.getElementById("feedback-content").innerHTML = `
    <div class="feedback-text">${data.overall_feedback || ""}</div>
    ${data.suggested_answer_structure ? `
      <div class="feedback-structure">
        <strong>💡 개선 답변 구조:</strong>
        <p>${data.suggested_answer_structure}</p>
      </div>
    ` : ""}
  `;

  // 점수 게이지 표시
  document.getElementById("score-gauges").style.display = "block";
  setTimeout(() => {
    animateBar("logic-gauge", data.logic_score || 0);
    animateBar("specific-gauge", data.specificity_score || 0);
    animateBar("relevance-gauge", data.relevance_score || 0);
  }, 100);

  document.getElementById("logic-val").textContent = data.logic_score || 0;
  document.getElementById("specific-val").textContent = data.specificity_score || 0;
  document.getElementById("relevance-val").textContent = data.relevance_score || 0;

  // 강점/개선점
  document.getElementById("strengths-section").style.display = "block";
  const strengthsList = document.getElementById("strengths-list");
  const improvementsList = document.getElementById("improvements-list");

  strengthsList.innerHTML = (data.strengths || []).map(s => `<li>${s}</li>`).join("");
  improvementsList.innerHTML = (data.improvements || []).map(s => `<li>${s}</li>`).join("");

  // 세션에 저장
  const q = state.questions[state.currentIndex] || {};
  state.sessionAnswers.push({
    question: q.question || "",
    answer: state.finalTranscript,
    feedback: data
  });
}

// ===== 답변 제출 & 다음 질문 =====
function submitAnswer() {
  // 녹음 중이면 중지
  if (state.isRecording) {
    stopRecording();
    setTimeout(() => {
      moveToNextQuestion();
    }, 1500);
    return;
  }
  moveToNextQuestion();
}

function moveToNextQuestion() {
  state.currentIndex++;

  if (state.currentIndex >= state.questions.length) {
    endInterview();
    return;
  }

  displayQuestion(state.currentIndex);
}

// ===== 타이머 =====
function resetTimer(seconds) {
  stopTimer();
  state.timeLeft = seconds;
  updateTimerDisplay();
}

function startTimer() {
  stopTimer();
  state.timerInterval = setInterval(() => {
    state.timeLeft--;
    updateTimerDisplay();

    if (state.timeLeft <= 0) {
      stopRecording();
    }
  }, 1000);
}

function stopTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
}

function updateTimerDisplay() {
  const m = Math.floor(state.timeLeft / 60).toString().padStart(2, "0");
  const s = (state.timeLeft % 60).toString().padStart(2, "0");
  const el = document.getElementById("timer-display");
  el.textContent = `${m}:${s}`;
  el.className = "timer-display" + (state.timeLeft <= 30 ? " timer-warning" : "");
}

// ===== 면접 종료 =====
function endInterview() {
  stopRecording();
  stopTimer();

  if (state.frameAnalysisInterval) {
    clearInterval(state.frameAnalysisInterval);
  }

  // 카메라 스트림 종료
  if (state.cameraStream) {
    state.cameraStream.getTracks().forEach(t => t.stop());
  }

  // 평균 점수 계산
  const avgEye = average(state.faceDataAccum.eyeScores);
  const avgPosture = average(state.faceDataAccum.postureScores);

  // 세션 데이터 저장
  if (state.socket) {
    state.socket.emit("save_session_data", {
      company: sessionStorage.getItem("company") || "",
      position: sessionStorage.getItem("position") || "",
      speech_summary: buildSpeechSummary(),
      face_summary: { overall_score: Math.round((avgEye + avgPosture) / 2) }
    });
  }
}

// ===== 유틸리티 함수 =====
function animateBar(elementId, value) {
  const el = document.getElementById(elementId);
  if (el) {
    el.style.transition = "width 0.8s ease";
    el.style.width = Math.min(100, Math.max(0, value)) + "%";
  }
}

function average(arr) {
  if (!arr.length) return 70;
  return Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
}

function enableNextButton() {
  document.getElementById("btn-next").disabled = false;
}

function resetFeedbackPanel() {
  document.getElementById("feedback-content").innerHTML = `
    <div class="feedback-placeholder">
      <div class="placeholder-icon">💬</div>
      <p>답변을 제출하면<br/>AI 피드백이 표시됩니다</p>
    </div>
  `;
  document.getElementById("feedback-score").textContent = "--점";
  document.getElementById("feedback-score").style.background = "";
  document.getElementById("score-gauges").style.display = "none";
  document.getElementById("strengths-section").style.display = "none";
}

function updateCompanyDisplay() {
  const company = sessionStorage.getItem("company") || "";
  const position = sessionStorage.getItem("position") || "";
  if (company && position) {
    document.getElementById("company-display").textContent = `${company} | ${position}`;
  }
}

function buildSpeechSummary() {
  return {
    overall_speech_score: 70,
    filler_analysis: {
      total_count: state.speechDataAccum.fillerTotal,
      severity: state.speechDataAccum.fillerTotal > 10 ? "개선 필요" :
                state.speechDataAccum.fillerTotal > 5 ? "주의" : "양호"
    },
    speed_analysis: {
      words_per_minute: average(state.speechDataAccum.speedSamples),
      speed_level: "보통"
    },
    confidence_analysis: {
      confidence_score: 70,
      confidence_level: "보통"
    },
    structure_analysis: {
      uses_star_method: false,
      sentence_count: 0
    }
  };
}

function buildReportData() {
  return {
    company: sessionStorage.getItem("company") || "",
    position: sessionStorage.getItem("position") || "",
    start_time: new Date().toISOString(),
    answers: state.sessionAnswers,
    total_score: state.sessionAnswers.length > 0
      ? Math.round(state.sessionAnswers.reduce((s, a) => s + (a.feedback?.score || 0), 0) / state.sessionAnswers.length)
      : 0,
    speech_summary: buildSpeechSummary(),
    face_summary: {
      overall_score: Math.round((
        average(state.faceDataAccum.eyeScores) +
        average(state.faceDataAccum.postureScores)
      ) / 2)
    }
  };
}

function getDefaultQuestions() {
  return [
    { id: 1, category: "인성/자기소개", question: "자기소개를 1분 내외로 해주세요.", difficulty: "쉬움", time_limit: 90, tips: "이름, 역량, 지원 동기 순으로 말하세요." },
    { id: 2, category: "직무 역량", question: "본인의 가장 큰 강점은 무엇인가요?", difficulty: "보통", time_limit: 120, tips: "구체적인 사례와 함께 설명하세요." },
    { id: 3, category: "경험/프로젝트", question: "가장 도전적이었던 경험을 말씀해주세요.", difficulty: "보통", time_limit: 180, tips: "STAR 기법(상황-과제-행동-결과)으로 답변하세요." },
    { id: 4, category: "회사 지원 동기", question: "왜 이 회사에 지원하셨나요?", difficulty: "보통", time_limit: 120, tips: "회사의 비전과 자신의 목표를 연결하세요." },
    { id: 5, category: "상황 판단/문제해결", question: "팀 내 갈등 상황을 어떻게 해결하셨나요?", difficulty: "어려움", time_limit: 180, tips: "실제 사례를 들어 구체적으로 설명하세요." }
  ];
}
