"""
AI 스마트 면접관 실행 스크립트
사용 전 .env 파일에 OPENAI_API_KEY를 입력하세요.
"""
import subprocess
import sys
import os


def check_env():
    """환경 변수 확인"""
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your_openai_api_key_here":
        print("=" * 60)
        print("⚠️  OpenAI API 키가 설정되지 않았습니다!")
        print("   .env 파일에서 OPENAI_API_KEY를 설정해주세요.")
        print("=" * 60)
        return False
    return True


def install_requirements():
    """패키지 설치"""
    print("📦 패키지를 설치합니다...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        check=True
    )
    print("✅ 패키지 설치 완료")


if __name__ == "__main__":
    print("🤖 AI 스마트 면접관을 시작합니다...")

    # 환경 변수 확인
    try:
        from dotenv import load_dotenv
    except ImportError:
        install_requirements()

    if not check_env():
        input("Enter를 눌러 종료하세요...")
        sys.exit(1)

    # 앱 실행
    print("🌐 서버 시작: http://localhost:5000")
    print("   브라우저에서 위 주소를 여세요.")
    print("   종료하려면 Ctrl+C를 누르세요.\n")

    from app import app, socketio
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
