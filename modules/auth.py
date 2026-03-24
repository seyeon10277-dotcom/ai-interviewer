import os
from functools import wraps
from flask import session, redirect, url_for
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY"),
    options=ClientOptions(postgrest_client_timeout=30, storage_client_timeout=30)
)

APP_URL = os.getenv("APP_URL", "http://localhost:5000")


class AuthModule:
    """Supabase 기반 인증 모듈"""

    def sign_up(self, email: str, password: str):
        """회원가입"""
        return supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"email_redirect_to": f"{APP_URL}/login"}
        })

    def sign_in(self, email: str, password: str):
        """로그인"""
        return supabase.auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        """로그아웃"""
        supabase.auth.sign_out()

    def get_user(self, access_token: str):
        """토큰으로 유저 정보 조회 (토큰 유효성 검사)"""
        return supabase.auth.get_user(access_token)


def login_required(f):
    """로그인한 사용자만 접근 가능한 라우트 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("access_token")
        if not token:
            return redirect(url_for("login"))
        try:
            auth = AuthModule()
            auth.get_user(token)
        except Exception:
            session.clear()
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function
