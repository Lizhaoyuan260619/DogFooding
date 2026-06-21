import re
import hashlib
import secrets
import os
import requests
from urllib.parse import urlencode
from models.database import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    get_user_by_provider,
    create_session,
    get_session_by_token,
    delete_session,
    delete_all_user_sessions,
    update_user
)


def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f'{salt}${password_hash.hex()}'


def verify_password(password, password_hash):
    try:
        salt, hash_part = password_hash.split('$', 1)
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return computed_hash == hash_part
    except (ValueError, AttributeError):
        return False


def validate_username(username):
    if not username or len(username.strip()) < 3:
        return False, '用户名至少需要3个字符'
    if len(username) > 20:
        return False, '用户名不能超过20个字符'
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
        return False, '用户名只能包含字母、数字、下划线和中文字符'
    if get_user_by_username(username):
        return False, '该用户名已被注册'
    return True, ''


def validate_email(email):
    if not email:
        return False, '请输入电子邮箱'
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, '请输入有效的电子邮箱地址'
    if get_user_by_email(email):
        return False, '该邮箱已被注册'
    return True, ''


def validate_password(password):
    if not password or len(password) < 8:
        return False, '密码至少需要8个字符'
    if len(password) > 128:
        return False, '密码不能超过128个字符'
    if not re.search(r'[A-Za-z]', password):
        return False, '密码必须包含至少一个字母'
    if not re.search(r'[0-9]', password):
        return False, '密码必须包含至少一个数字'
    return True, ''


def validate_confirm_password(password, confirm_password):
    if not confirm_password:
        return False, '请确认密码'
    if password != confirm_password:
        return False, '两次输入的密码不一致'
    return True, ''


def register_user(username, email, password, confirm_password):
    errors = {}

    is_valid, msg = validate_username(username)
    if not is_valid:
        errors['username'] = msg

    is_valid, msg = validate_email(email)
    if not is_valid:
        errors['email'] = msg

    is_valid, msg = validate_password(password)
    if not is_valid:
        errors['password'] = msg

    is_valid, msg = validate_confirm_password(password, confirm_password)
    if not is_valid:
        errors['confirm_password'] = msg

    if errors:
        return None, errors

    password_hash = hash_password(password)
    user = create_user(username, email, password_hash)

    return user, None


def login_user(identifier, password, ip_address=None, user_agent=None, remember_me=False):
    errors = {}

    if not identifier:
        errors['identifier'] = '请输入用户名或邮箱'
        return None, None, errors

    if not password:
        errors['password'] = '请输入密码'
        return None, None, errors

    user = get_user_by_username(identifier)
    if not user:
        user = get_user_by_email(identifier)

    if not user:
        errors['identifier'] = '用户名或密码错误'
        return None, None, errors

    if not user['is_active']:
        errors['identifier'] = '该账号已被禁用'
        return None, None, errors

    if not verify_password(password, user['password_hash']):
        errors['password'] = '用户名或密码错误'
        return None, None, errors

    duration_hours = 24 * 7 if remember_me else 24
    session = create_session(user['id'], ip_address, user_agent, duration_hours)

    return user, session, None


def logout_user(token):
    return delete_session(token)


def logout_all_sessions(user_id):
    delete_all_user_sessions(user_id)


def get_current_user(token):
    if not token:
        return None

    session = get_session_by_token(token)
    if not session:
        return None

    user = get_user_by_id(session['user_id'])
    if not user or not user['is_active']:
        return None

    return dict(user)


def user_to_dict(user):
    return {
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'avatar': user['avatar'],
        'bio': user['bio'],
        'is_verified': bool(user['is_verified']),
        'provider': user['provider'],
        'created_at': user['created_at']
    }


class GitHubOAuth:
    def __init__(self):
        self.client_id = os.environ.get('GITHUB_CLIENT_ID', '')
        self.client_secret = os.environ.get('GITHUB_CLIENT_SECRET', '')
        self.redirect_uri = os.environ.get('GITHUB_REDIRECT_URI', 'http://localhost:5000/auth/github/callback')
        self.auth_url = 'https://github.com/login/oauth/authorize'
        self.token_url = 'https://github.com/login/oauth/access_token'
        self.user_url = 'https://api.github.com/user'

    def get_authorization_url(self):
        if not self.client_id:
            return None
        state = secrets.token_urlsafe(32)
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'read:user user:email',
            'state': state
        }
        return f'{self.auth_url}?{urlencode(params)}', state

    def get_access_token(self, code):
        if not self.client_id or not self.client_secret:
            return None
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        headers = {'Accept': 'application/json'}
        response = requests.post(self.token_url, data=data, headers=headers)
        if response.status_code == 200:
            return response.json().get('access_token')
        return None

    def get_user_info(self, access_token):
        if not access_token:
            return None
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(self.user_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    def get_user_email(self, access_token):
        if not access_token:
            return None
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        response = requests.get('https://api.github.com/user/emails', headers=headers)
        if response.status_code == 200:
            emails = response.json()
            for email in emails:
                if email.get('primary') and email.get('verified'):
                    return email['email']
        return None


def github_login_or_register(github_user, ip_address=None, user_agent=None):
    if not github_user:
        return None, None, {'oauth': 'GitHub 认证失败'}

    provider_id = str(github_user.get('id'))
    username = github_user.get('login')
    avatar = github_user.get('avatar_url')
    email = github_user.get('email')

    user = get_user_by_provider('github', provider_id)

    if user:
        session = create_session(user['id'], ip_address, user_agent, 24)
        return user, session, None

    if not email:
        github_oauth = GitHubOAuth()
        access_token = github_user.get('access_token')
        if access_token:
            email = github_oauth.get_user_email(access_token)

    if not email:
        return None, None, {'oauth': '无法获取 GitHub 邮箱，请确保您的 GitHub 邮箱已公开'}

    existing_user = get_user_by_email(email)
    if existing_user:
        update_user(existing_user['id'], provider='github', provider_id=provider_id, avatar=avatar)
        session = create_session(existing_user['id'], ip_address, user_agent, 24)
        return existing_user, session, None

    base_username = username
    suffix = 1
    while get_user_by_username(username):
        username = f'{base_username}_{suffix}'
        suffix += 1

    password_hash = hash_password(secrets.token_urlsafe(32))
    user = create_user(username, email, password_hash, 'github', provider_id, avatar)

    session = create_session(user['id'], ip_address, user_agent, 24)
    return user, session, None
