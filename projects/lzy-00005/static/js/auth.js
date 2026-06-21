const Auth = {
    validationStates: {},
    debounceTimers: {},

    initRegister() {
        this.setupRegisterValidation();
        this.setupRegisterSubmit();
    },

    initLogin() {
        this.setupLoginValidation();
        this.setupLoginSubmit();
    },

    setupRegisterValidation() {
        const username = document.getElementById('username');
        const email = document.getElementById('email');
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm_password');
        const agree = document.getElementById('agree');

        username.addEventListener('input', (e) => this.debounce('username', () => this.validateUsername(e.target.value), 300));
        username.addEventListener('blur', (e) => this.validateUsername(e.target.value));

        email.addEventListener('input', (e) => this.debounce('email', () => this.validateEmail(e.target.value), 300));
        email.addEventListener('blur', (e) => this.validateEmail(e.target.value));

        password.addEventListener('input', (e) => {
            this.validatePassword(e.target.value);
            this.updatePasswordStrength(e.target.value);
            if (confirmPassword.value) {
                this.validateConfirmPassword(confirmPassword.value, e.target.value);
            }
        });

        confirmPassword.addEventListener('input', (e) => {
            this.validateConfirmPassword(e.target.value, password.value);
        });
        confirmPassword.addEventListener('blur', (e) => {
            this.validateConfirmPassword(e.target.value, password.value);
        });

        agree.addEventListener('change', (e) => {
            this.validateAgree(e.target.checked);
        });
    },

    setupLoginValidation() {
        const identifier = document.getElementById('identifier');
        const password = document.getElementById('password');

        identifier.addEventListener('input', () => this.clearError('identifier'));
        password.addEventListener('input', () => this.clearError('password'));
    },

    setupRegisterSubmit() {
        const form = document.getElementById('registerForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            const agree = document.getElementById('agree').checked;

            const isUsernameValid = await this.validateUsername(username);
            const isEmailValid = await this.validateEmail(email);
            const isPasswordValid = this.validatePassword(password);
            const isConfirmValid = this.validateConfirmPassword(confirmPassword, password);
            const isAgreeValid = this.validateAgree(agree);

            if (!isUsernameValid || !isEmailValid || !isPasswordValid || !isConfirmValid || !isAgreeValid) {
                this.showToast('请检查表单中的错误', 'error');
                return;
            }

            this.setLoading(true);

            try {
                const response = await fetch('/auth/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password, confirm_password: confirmPassword })
                });

                const data = await response.json();

                if (data.success) {
                    this.showToast('注册成功！正在跳转到登录页面...', 'success');
                    setTimeout(() => {
                        window.location.href = data.redirect || '/auth/login';
                    }, 1500);
                } else {
                    this.handleErrors(data.errors);
                    this.showToast('注册失败，请检查表单', 'error');
                }
            } catch (error) {
                this.showToast('网络错误，请稍后重试', 'error');
            } finally {
                this.setLoading(false);
            }
        });
    },

    setupLoginSubmit() {
        const form = document.getElementById('loginForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const identifier = document.getElementById('identifier').value;
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('remember_me').checked;

            if (!identifier || !password) {
                if (!identifier) this.showError('identifier', '请输入用户名或邮箱');
                if (!password) this.showError('password', '请输入密码');
                return;
            }

            this.setLoading(true);

            try {
                const response = await fetch('/auth/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ identifier, password, remember_me: rememberMe })
                });

                const data = await response.json();

                if (data.success) {
                    this.showToast('登录成功！正在跳转...', 'success');
                    setTimeout(() => {
                        window.location.href = data.redirect || '/';
                    }, 1000);
                } else {
                    this.handleErrors(data.errors);
                    this.showToast('登录失败，请检查账号或密码', 'error');
                }
            } catch (error) {
                this.showToast('网络错误，请稍后重试', 'error');
            } finally {
                this.setLoading(false);
            }
        });
    },

    async validateUsername(username) {
        if (!username) {
            this.showError('username', '请输入用户名');
            return false;
        }

        if (username.length < 3) {
            this.showError('username', '用户名至少需要3个字符');
            return false;
        }

        if (username.length > 20) {
            this.showError('username', '用户名不能超过20个字符');
            return false;
        }

        if (!/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(username)) {
            this.showError('username', '用户名只能包含字母、数字、下划线和中文字符');
            return false;
        }

        try {
            const response = await fetch('/auth/api/validate/username', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });
            const data = await response.json();

            if (data.valid) {
                this.showSuccess('username', '用户名可用');
                return true;
            } else {
                this.showError('username', data.message);
                return false;
            }
        } catch {
            this.showSuccess('username', '');
            return true;
        }
    },

    async validateEmail(email) {
        if (!email) {
            this.showError('email', '请输入电子邮箱');
            return false;
        }

        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            this.showError('email', '请输入有效的电子邮箱地址');
            return false;
        }

        try {
            const response = await fetch('/auth/api/validate/email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await response.json();

            if (data.valid) {
                this.showSuccess('email', '邮箱可用');
                return true;
            } else {
                this.showError('email', data.message);
                return false;
            }
        } catch {
            this.showSuccess('email', '');
            return true;
        }
    },

    validatePassword(password) {
        if (!password) {
            this.showError('password', '请输入密码');
            return false;
        }

        if (password.length < 8) {
            this.showError('password', '密码至少需要8个字符');
            return false;
        }

        if (password.length > 128) {
            this.showError('password', '密码不能超过128个字符');
            return false;
        }

        if (!/[A-Za-z]/.test(password)) {
            this.showError('password', '密码必须包含至少一个字母');
            return false;
        }

        if (!/[0-9]/.test(password)) {
            this.showError('password', '密码必须包含至少一个数字');
            return false;
        }

        this.clearError('password');
        return true;
    },

    validateConfirmPassword(confirmPassword, password) {
        if (!confirmPassword) {
            this.showError('confirm_password', '请确认密码');
            return false;
        }

        if (confirmPassword !== password) {
            this.showError('confirm_password', '两次输入的密码不一致');
            return false;
        }

        this.showSuccess('confirm_password', '密码一致');
        return true;
    },

    validateAgree(checked) {
        if (!checked) {
            this.showError('agree', '请阅读并同意服务条款和隐私政策');
            return false;
        }
        this.clearError('agree');
        return true;
    },

    updatePasswordStrength(password) {
        const strengthBar = document.getElementById('strengthBar');
        const strengthText = document.getElementById('strengthText');

        if (!password) {
            strengthBar.style.width = '0%';
            strengthBar.className = 'strength-bar';
            strengthText.textContent = '密码强度';
            return;
        }

        let strength = 0;

        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[A-Za-z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;

        const percentage = (strength / 5) * 100;
        strengthBar.style.width = percentage + '%';

        if (strength <= 2) {
            strengthBar.className = 'strength-bar weak';
            strengthText.textContent = '密码强度：弱';
        } else if (strength <= 3) {
            strengthBar.className = 'strength-bar medium';
            strengthText.textContent = '密码强度：中等';
        } else {
            strengthBar.className = 'strength-bar strong';
            strengthText.textContent = '密码强度：强';
        }
    },

    showError(field, message) {
        const errorEl = document.getElementById(field + 'Error');
        const inputEl = document.getElementById(field);
        const successEl = document.getElementById(field + 'Success');

        if (errorEl) errorEl.textContent = message;
        if (inputEl) {
            inputEl.classList.add('invalid');
            inputEl.classList.remove('valid');
        }
        if (successEl) successEl.textContent = '';
    },

    showSuccess(field, message) {
        const errorEl = document.getElementById(field + 'Error');
        const inputEl = document.getElementById(field);
        const successEl = document.getElementById(field + 'Success');

        if (errorEl) errorEl.textContent = '';
        if (inputEl) {
            inputEl.classList.remove('invalid');
            inputEl.classList.add('valid');
        }
        if (successEl) successEl.textContent = message;
    },

    clearError(field) {
        const errorEl = document.getElementById(field + 'Error');
        const inputEl = document.getElementById(field);
        const successEl = document.getElementById(field + 'Success');

        if (errorEl) errorEl.textContent = '';
        if (inputEl) {
            inputEl.classList.remove('invalid', 'valid');
        }
        if (successEl) successEl.textContent = '';
    },

    handleErrors(errors) {
        for (const field in errors) {
            this.showError(field, errors[field]);
        }
    },

    setLoading(loading) {
        const submitBtn = document.getElementById('submitBtn');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoading = submitBtn.querySelector('.btn-loading');

        submitBtn.disabled = loading;
        btnText.style.display = loading ? 'none' : 'inline';
        btnLoading.style.display = loading ? 'inline' : 'none';
    },

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';

        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    },

    debounce(key, func, wait) {
        clearTimeout(this.debounceTimers[key]);
        this.debounceTimers[key] = setTimeout(func, wait);
    },

    async logout() {
        try {
            await fetch('/auth/api/logout', { method: 'POST' });
            window.location.href = '/auth/login';
        } catch (error) {
            window.location.href = '/auth/login';
        }
    },

    async getCurrentUser() {
        try {
            const response = await fetch('/auth/api/me');
            const data = await response.json();
            return data.success ? data.user : null;
        } catch {
            return null;
        }
    }
};

window.Auth = Auth;
