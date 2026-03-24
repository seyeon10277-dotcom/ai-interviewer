import os
from functools import wraps
from flask import session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

APP_URL = os.getenv("APP_URL", "http://localhost:5000")

_supabase: Client = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
    return _supabase


class AuthModule:

    def sign_up(self, email: str, password: str):
        return get_supabase().auth.sign_up({
            "email": email,
            "password": password,
            "options": {"email_redirect_to": f"{APP_URL}/login"}
        })

    def sign_in(self, email: str, password: str):
        return get_supabase().auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        get_supabase().auth.sign_out()

    def get_user(self, access_token: str):
        return get_supabase().auth.get_user(access_token)


def login_required(f):
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
