document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    const userNameInput = document.getElementById('userName');
    const roomCodeInput = document.getElementById('roomCode');
    const createRoomBtn = document.getElementById('createRoomBtn');
    const joinRoomBtn = document.getElementById('joinRoomBtn');
    const errorMessage = document.getElementById('errorMessage');
    
    const savedName = localStorage.getItem('whiteboard_userName');
    if (savedName) {
        userNameInput.value = savedName;
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.add('show');
        setTimeout(() => {
            errorMessage.classList.remove('show');
        }, 3000);
    }
    
    function validateUserName(name) {
        const cleanName = name.trim();
        if (!cleanName) {
            showError('请输入昵称');
            return null;
        }
        if (cleanName.length > 20) {
            showError('昵称不能超过20个字符');
            return null;
        }
        return cleanName;
    }
    
    function validateRoomCode(code) {
        const cleanCode = code.trim().toUpperCase();
        if (!cleanCode) {
            showError('请输入邀请码');
            return null;
        }
        if (cleanCode.length !== 6) {
            showError('邀请码必须是6位字符');
            return null;
        }
        return cleanCode;
    }
    
    createRoomBtn.addEventListener('click', async function() {
        const userName = validateUserName(userNameInput.value);
        if (!userName) return;
        
        try {
            localStorage.setItem('whiteboard_userName', userName);
            
            socket.emit('room:create', { userName }, function(response) {
                if (response.success) {
                    sessionStorage.setItem('whiteboard_roomCode', response.roomCode);
                    sessionStorage.setItem('whiteboard_userId', response.userId);
                    sessionStorage.setItem('whiteboard_userName', response.userName);
                    sessionStorage.setItem('whiteboard_userColor', response.color);
                    sessionStorage.setItem('whiteboard_users', JSON.stringify(response.users));
                    sessionStorage.setItem('whiteboard_commands', JSON.stringify(response.commands || []));
                    window.location.href = '/board';
                } else {
                    showError(response.error || '创建房间失败');
                }
            });
        } catch (err) {
            showError('创建房间失败，请稍后重试');
        }
    });
    
    joinRoomBtn.addEventListener('click', async function() {
        const userName = validateUserName(userNameInput.value);
        if (!userName) return;
        
        const roomCode = validateRoomCode(roomCodeInput.value);
        if (!roomCode) return;
        
        try {
            localStorage.setItem('whiteboard_userName', userName);
            
            socket.emit('room:join', { roomCode, userName }, function(response) {
                if (response.success) {
                    sessionStorage.setItem('whiteboard_roomCode', response.roomCode);
                    sessionStorage.setItem('whiteboard_userId', response.userId);
                    sessionStorage.setItem('whiteboard_userName', response.userName);
                    sessionStorage.setItem('whiteboard_userColor', response.color);
                    sessionStorage.setItem('whiteboard_users', JSON.stringify(response.users));
                    sessionStorage.setItem('whiteboard_commands', JSON.stringify(response.commands || []));
                    window.location.href = '/board';
                } else {
                    showError(response.error || '加入房间失败');
                }
            });
        } catch (err) {
            showError('加入房间失败，请稍后重试');
        }
    });
    
    roomCodeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            joinRoomBtn.click();
        }
    });
    
    userNameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            if (roomCodeInput.value.trim()) {
                joinRoomBtn.click();
            } else {
                createRoomBtn.click();
            }
        }
    });
});
