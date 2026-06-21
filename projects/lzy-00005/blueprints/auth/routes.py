from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, g
from functools import wraps
from blueprints.auth.services import (
    register_user,
    login_user,
    logout_user,
    logout_all_sessions,
    get_current_user,
    user_to_dict,
    GitHubOAuth,
    github_login_or_register
)

auth_bp = Blueprint('auth', __name__, template_folder='templates')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('auth_token') or request.headers.get('X-Auth-Token')
        user = get_current_user(token)
        if not user:
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify({'error': '未登录或登录已过期'}), 401
            return redirect(url_for('auth.login_page', next=request.path))
        g.user = user
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.before_app_request
def load_user():
    token = request.cookies.get('auth_token') or request.headers.get('X-Auth-Token')
    if token:
        user = get_current_user(token)
        if user:
            g.user = user
        else:
            g.user = None
    else:
        g.user = None


@auth_bp.route('/register', methods=['GET'])
def register_page():
    if hasattr(g, 'user') and g.user:
        return redirect(url_for('index'))
    github_oauth = GitHubOAuth()
    github_auth_url, _ = github_oauth.get_authorization_url() if github_oauth.client_id else (None, None)
    return render_template('register.html', github_auth_url=github_auth_url)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    if hasattr(g, 'user') and g.user:
        return redirect(url_for('index'))
    github_oauth = GitHubOAuth()
    github_auth_url, _ = github_oauth.get_authorization_url() if github_oauth.client_id else (None, None)
    return render_template('login.html', github_auth_url=github_auth_url)


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() if request.is_json else request.form

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    user, errors = register_user(username, email, password, confirm_password)

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    user_data = user_to_dict(user)
    return jsonify({'success': True, 'user': user_data, 'redirect': url_for('auth.login_page')}), 201


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() if request.is_json else request.form

    identifier = data.get('identifier', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False) in [True, 'true', '1', 'on']

    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    user, session, errors = login_user(identifier, password, ip_address, user_agent, remember_me)

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    user_data = user_to_dict(user)

    response = jsonify({
        'success': True,
        'user': user_data,
        'redirect': request.args.get('next') or url_for('index')
    })

    max_age = 7 * 24 * 60 * 60 if remember_me else 24 * 60 * 60
    response.set_cookie(
        'auth_token',
        session['token'],
        max_age=max_age,
        httponly=True,
        secure=request.is_secure,
        samesite='Lax'
    )

    return response


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    token = request.cookies.get('auth_token') or request.headers.get('X-Auth-Token')

    if token:
        logout_user(token)

    response = jsonify({'success': True, 'redirect': url_for('auth.login_page')})
    response.delete_cookie('auth_token')

    return response


@auth_bp.route('/api/logout-all', methods=['POST'])
@login_required
def api_logout_all():
    user_id = g.user['id']
    logout_all_sessions(user_id)

    response = jsonify({'success': True, 'redirect': url_for('auth.login_page')})
    response.delete_cookie('auth_token')

    return response


@auth_bp.route('/api/me', methods=['GET'])
def api_me():
    token = request.cookies.get('auth_token') or request.headers.get('X-Auth-Token')
    user = get_current_user(token)

    if not user:
        return jsonify({'success': False, 'error': '未登录'}), 401

    user_data = user_to_dict(user)
    return jsonify({'success': True, 'user': user_data})


@auth_bp.route('/github/login', methods=['GET'])
def github_login():
    github_oauth = GitHubOAuth()
    if not github_oauth.client_id:
        return render_template('login.html', error='GitHub 登录未配置，请联系管理员'), 500

    auth_url, state = github_oauth.get_authorization_url()
    response = make_response(redirect(auth_url))
    response.set_cookie('oauth_state', state, max_age=600, httponly=True, secure=request.is_secure, samesite='Lax')

    return response


@auth_bp.route('/github/callback', methods=['GET'])
def github_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    saved_state = request.cookies.get('oauth_state')

    if not code or not state or state != saved_state:
        return render_template('login.html', error='GitHub 认证失败，请重试'), 400

    github_oauth = GitHubOAuth()
    access_token = github_oauth.get_access_token(code)

    if not access_token:
        return render_template('login.html', error='GitHub 认证失败，请重试'), 400

    github_user = github_oauth.get_user_info(access_token)
    if github_user:
        github_user['access_token'] = access_token

    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    user, session, errors = github_login_or_register(github_user, ip_address, user_agent)

    if errors:
        return render_template('login.html', error=errors.get('oauth', 'GitHub 认证失败')), 400

    response = make_response(redirect(url_for('index')))
    response.delete_cookie('oauth_state')
    response.set_cookie(
        'auth_token',
        session['token'],
        max_age=24 * 60 * 60,
        httponly=True,
        secure=request.is_secure,
        samesite='Lax'
    )

    return response


@auth_bp.route('/api/validate/username', methods=['POST'])
def api_validate_username():
    data = request.get_json()
    username = data.get('username', '').strip()

    from blueprints.auth.services import validate_username
    is_valid, message = validate_username(username)

    return jsonify({'valid': is_valid, 'message': message})


@auth_bp.route('/api/validate/email', methods=['POST'])
def api_validate_email():
    data = request.get_json()
    email = data.get('email', '').strip()

    from blueprints.auth.services import validate_email
    is_valid, message = validate_email(email)

    return jsonify({'valid': is_valid, 'message': message})
