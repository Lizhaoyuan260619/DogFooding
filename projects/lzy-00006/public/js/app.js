let layerManager, commandHistory, canvasRenderer, socketClient, voiceChatManager;
let currentUserId, currentUserName, currentUserColor, currentRoomCode;
let users = [];
let remoteCursors = {};
let voiceEnabled = false;
let voiceParticipants = [];

const toolNames = {
    'pen': '画笔',
    'erase': '橡皮擦',
    'line': '直线',
    'rect': '矩形',
    'circle': '圆形',
    'text': '文字'
};

document.addEventListener('DOMContentLoaded', initApp);

function initApp() {
    try {
        const roomCode = sessionStorage.getItem('whiteboard_roomCode');
        const userId = sessionStorage.getItem('whiteboard_userId');
        const userName = sessionStorage.getItem('whiteboard_userName');
        const userColor = sessionStorage.getItem('whiteboard_userColor');
        
        if (!roomCode || !userId || !userName) {
            window.location.href = '/';
            return;
        }
        
        currentUserId = userId;
        currentUserName = userName;
        currentUserColor = userColor;
        currentRoomCode = roomCode;
        
        initCoreInstances();
        initUI();
        initSocket();
        initVoiceManagerSocket();
        initUIEventBindings();
        loadInitialData();
    } catch (err) {
        console.error('initApp error:', err);
    }
}

function initCoreInstances() {
    try {
        const canvasWidth = 1920;
        const canvasHeight = 1080;
        
        layerManager = new LayerManager(5, canvasWidth, canvasHeight);
        
        commandHistory = new CommandHistory();
        
        const container = document.getElementById('canvasContainer');
        
        canvasRenderer = new CanvasRenderer(container, layerManager, commandHistory);
        canvasRenderer.setUser(currentUserId, currentUserName);
        
        socketClient = new SocketClient();

        if (VoiceChatManager.isSupported()) {
            voiceChatManager = new VoiceChatManager(socketClient, {
                userId: currentUserId,
                userName: currentUserName,
                userColor: currentUserColor,
                roomCode: currentRoomCode
            });
        }
    } catch (err) {
        console.error('initCoreInstances error:', err);
        throw err;
    }
}

function initUI() {
    document.getElementById('roomCode').textContent = currentRoomCode;
    document.getElementById('userInfo').innerHTML = `
        <span class="user-avatar" style="background: ${currentUserColor}">${currentUserName.charAt(0).toUpperCase()}</span>
        ${currentUserName}
    `;
    
    updateLineWidthPreview(3);
    updateHistoryButtons();
    renderLayerList();
}

function initSocket() {
    socketClient.connect();
    
    socketClient.setOnUserJoinedCallback(handleUserJoined);
    socketClient.setOnUserLeftCallback(handleUserLeft);
    socketClient.setOnUsersUpdateCallback(handleUsersUpdate);
    socketClient.setOnCommandReceivedCallback(handleRemoteCommand);
    socketClient.setOnCursorUpdateCallback(handleRemoteCursor);
    socketClient.setOnUndoCallback(handleRemoteUndo);
    socketClient.setOnRedoCallback(handleRemoteRedo);
}

function initVoiceManagerSocket() {
    if (voiceChatManager && socketClient.socket) {
        voiceChatManager.initSocket(socketClient.socket);
    }
}

function initUIEventBindings() {
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            canvasRenderer.setTool(btn.dataset.tool);
        });
    });
    
    document.getElementById('colorPicker').addEventListener('input', (e) => {
        canvasRenderer.setColor(e.target.value);
    });
    
    document.querySelectorAll('.color-preset').forEach(preset => {
        preset.addEventListener('click', () => {
            const color = preset.dataset.color;
            document.getElementById('colorPicker').value = color;
            canvasRenderer.setColor(color);
        });
    });
    
    document.getElementById('lineWidthSlider').addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        canvasRenderer.setLineWidth(value);
        document.getElementById('lineWidthValue').textContent = value + 'px';
        updateLineWidthPreview(value);
    });
    
    document.getElementById('fontSizeSlider').addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        canvasRenderer.setFontSize(value);
        document.getElementById('fontSizeValue').textContent = value + 'px';
    });
    
    document.getElementById('fillCheckbox').addEventListener('change', (e) => {
        if (e.target.checked) {
            canvasRenderer.setFillColor(document.getElementById('fillColorPicker').value);
        } else {
            canvasRenderer.setFillColor(null);
        }
    });
    
    document.getElementById('fillColorPicker').addEventListener('input', (e) => {
        if (document.getElementById('fillCheckbox').checked) {
            canvasRenderer.setFillColor(e.target.value);
        }
    });
    
    document.getElementById('undoBtn').addEventListener('click', () => {
        const command = canvasRenderer.undo();
        if (command) {
            socketClient.sendUndo();
            addToHistory(command, 'undo');
        }
    });
    
    document.getElementById('redoBtn').addEventListener('click', () => {
        const command = canvasRenderer.redo();
        if (command) {
            socketClient.sendRedo();
            addToHistory(command, 'redo');
        }
    });
    
    document.getElementById('exportBtn').addEventListener('click', exportToPNG);
    
    document.getElementById('addLayerBtn').addEventListener('click', addLayer);
    
    document.getElementById('copyRoomCode').addEventListener('click', copyRoomCode);
    
    document.getElementById('leaveRoomBtn').addEventListener('click', leaveRoom);
    
    canvasRenderer.setOnCommandCallback(handleLocalCommand);
    canvasRenderer.setOnCursorMoveCallback(handleLocalCursorMove);
    
    commandHistory.setOnChangeCallback(updateHistoryButtons);

    if (voiceChatManager) {
        initVoiceEventBindings();
    }
}

function initVoiceEventBindings() {
    document.getElementById('voiceJoinBtn').addEventListener('click', toggleVoiceChat);
    document.getElementById('voiceMuteBtn').addEventListener('click', toggleVoiceMute);
    document.getElementById('voiceLeaveBtn').addEventListener('click', leaveVoiceChat);
    document.getElementById('voiceMuteAllBtn').addEventListener('click', toggleMuteAll);

    const pttBtn = document.getElementById('voicePTTBtn');
    pttBtn.addEventListener('mousedown', () => {
        voiceChatManager.setPTTActive(true);
        pttBtn.classList.add('is-ptt-active');
    });
    pttBtn.addEventListener('mouseup', () => {
        voiceChatManager.setPTTActive(false);
        pttBtn.classList.remove('is-ptt-active');
    });
    pttBtn.addEventListener('mouseleave', () => {
        voiceChatManager.setPTTActive(false);
        pttBtn.classList.remove('is-ptt-active');
    });
    pttBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        voiceChatManager.setPTTActive(true);
        pttBtn.classList.add('is-ptt-active');
    });
    pttBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        voiceChatManager.setPTTActive(false);
        pttBtn.classList.remove('is-ptt-active');
    });

    voiceChatManager.setOnJoinedCallback(handleVoiceJoined);
    voiceChatManager.setOnLeftCallback(handleVoiceLeft);
    voiceChatManager.setOnParticipantJoinedCallback(handleVoiceParticipantJoined);
    voiceChatManager.setOnParticipantLeftCallback(handleVoiceParticipantLeft);
    voiceChatManager.setOnSpeakingChangeCallback(handleVoiceSpeakingChange);
    voiceChatManager.setOnMuteChangeCallback(handleVoiceMuteChange);
    voiceChatManager.setOnStateChangeCallback(updateVoicePeerList);
    voiceChatManager.setOnErrorCallback(handleVoiceError);
    voiceChatManager.setOnVolumeChangeCallback(handleVoiceVolumeChange);
    voiceChatManager.setOnConnectionStateChangeCallback(handleVoiceConnectionStateChange);
}

function loadInitialData() {
    try {
        const savedUsers = sessionStorage.getItem('whiteboard_users');
        const savedCommands = sessionStorage.getItem('whiteboard_commands');
        
        if (savedUsers) {
            users = JSON.parse(savedUsers);
            renderUserList();
        }
        
        if (savedCommands) {
            const commands = JSON.parse(savedCommands);
            if (commands.length > 0) {
                canvasRenderer.loadCommands(commands);
                commands.forEach(cmd => addToHistory(cmd, 'remote'));
            }
        }
    } catch (err) {
        console.error('Error loading initial data:', err);
    }
    
    sessionStorage.removeItem('whiteboard_users');
    sessionStorage.removeItem('whiteboard_commands');
}

function handleLocalCommand(command) {
    socketClient.sendCommand(command);
    addToHistory(command, 'local');
}

function handleRemoteCommand(commandData) {
    if (commandData.userId === currentUserId) return;
    
    canvasRenderer.executeRemoteCommand(commandData);
    addToHistory(commandData, 'remote');
    showToast(`${commandData.userName} 绘制了 ${toolNames[commandData.type] || commandData.type}`, 'info');
}

function handleRemoteUndo(data) {
    if (data.userId === currentUserId) return;
    
    canvasRenderer.undoToSequence(data.sequence);
    showToast(`${data.userName} 执行了撤销`, 'warning');
}

function handleRemoteRedo(data) {
    if (data.userId === currentUserId) return;
    
    canvasRenderer.redoRemote(data.command);
    addToHistory(data.command, 'remote');
    showToast(`${data.userName} 执行了重做`, 'info');
}

function handleUserJoined(user) {
    users.push(user);
    renderUserList();
    showToast(`${user.name} 加入了房间`, 'success');
}

function handleUserLeft(userId) {
    users = users.filter(u => u.id !== userId);
    renderUserList();
    removeRemoteCursor(userId);
    showToast('有用户离开了房间', 'warning');
}

function handleUsersUpdate(newUsers) {
    users = newUsers;
    renderUserList();
}

function handleLocalCursorMove(x, y) {
    socketClient.sendCursorMove(x, y);
}

function handleRemoteCursor(data) {
    if (data.userId === currentUserId) return;
    updateRemoteCursor(data);
}

function updateRemoteCursor(data) {
    let cursorEl = remoteCursors[data.userId];
    
    if (!cursorEl) {
        cursorEl = document.createElement('div');
        cursorEl.className = 'remote-cursor';
        cursorEl.innerHTML = `
            <div class="remote-cursor-dot" style="background: ${data.color}"></div>
            <div class="remote-cursor-label" style="background: ${data.color}">${data.name}</div>
        `;
        document.getElementById('cursorLayer').appendChild(cursorEl);
        remoteCursors[data.userId] = cursorEl;
    }
    
    const canvasRect = document.getElementById('canvasContainer').getBoundingClientRect();
    const canvas = canvasRenderer.displayCanvas;
    const displayRect = canvas.getBoundingClientRect();
    
    const scaleX = displayRect.width / canvas.width;
    const scaleY = displayRect.height / canvas.height;
    
    const offsetX = displayRect.left - canvasRect.left;
    const offsetY = displayRect.top - canvasRect.top;
    
    cursorEl.style.transform = `translate(${offsetX + data.x * scaleX}px, ${offsetY + data.y * scaleY}px)`;
}

function removeRemoteCursor(userId) {
    if (remoteCursors[userId]) {
        remoteCursors[userId].remove();
        delete remoteCursors[userId];
    }
}

function renderUserList() {
    const container = document.getElementById('userList');
    container.innerHTML = '';
    
    users.forEach(user => {
        const isCurrentUser = user.id === currentUserId;
        const userEl = document.createElement('div');
        userEl.className = 'user-item';
        userEl.innerHTML = `
            <div class="user-item-avatar" style="background: ${user.color}">
                ${user.name.charAt(0).toUpperCase()}
            </div>
            <div class="user-item-info">
                <div class="user-item-name">${user.name}${isCurrentUser ? ' (你)' : ''}</div>
                <div class="user-item-status">在线</div>
            </div>
        `;
        container.appendChild(userEl);
    });
}

function renderLayerList() {
    const container = document.getElementById('layerList');
    const layers = layerManager.getLayers();
    const currentLayerId = layerManager.currentLayerId;
    
    container.innerHTML = '';
    
    for (let i = layers.length - 1; i >= 0; i--) {
        const layer = layers[i];
        const layerEl = document.createElement('div');
        layerEl.className = `layer-item ${layer.id === currentLayerId ? 'active' : ''} ${!layer.visible ? 'hidden' : ''}`;
        layerEl.dataset.layerId = layer.id;
        
        layerEl.innerHTML = `
            <div class="layer-thumbnail">
                <canvas width="32" height="24"></canvas>
            </div>
            <span class="layer-name">${layer.name}</span>
            <div class="layer-actions">
                <button class="layer-visibility-btn" title="${layer.visible ? '隐藏' : '显示'}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${layer.visible 
                            ? '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'
                            : '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>'
                        }
                    </svg>
                </button>
                <button class="layer-delete-btn" title="删除图层" ${layers.length <= 1 ? 'disabled style="opacity:0.3;cursor:not-allowed"' : ''}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3,6 5,6 21,6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        `;
        
        const thumbCanvas = layerEl.querySelector('canvas');
        const thumbCtx = thumbCanvas.getContext('2d');
        thumbCtx.fillStyle = '#ffffff';
        thumbCtx.fillRect(0, 0, 32, 24);
        thumbCtx.drawImage(layer.canvas, 0, 0, layer.canvas.width, layer.canvas.height, 0, 0, 32, 24);
        
        layerEl.addEventListener('click', (e) => {
            if (!e.target.closest('.layer-visibility-btn') && !e.target.closest('.layer-delete-btn')) {
                layerManager.setCurrentLayer(layer.id);
                renderLayerList();
            }
        });
        
        layerEl.querySelector('.layer-visibility-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            layerManager.setLayerVisibility(layer.id, !layer.visible);
            renderLayerList();
        });
        
        layerEl.querySelector('.layer-delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            if (layers.length > 1) {
                try {
                    layerManager.removeLayer(layer.id);
                    renderLayerList();
                    showToast('图层已删除', 'success');
                } catch (err) {
                    showToast(err.message, 'error');
                }
            }
        });
        
        container.appendChild(layerEl);
    }
    
    layerManager.setOnChangeCallback(() => {
        renderLayerList();
        canvasRenderer.render();
    });
}

function addLayer() {
    try {
        layerManager.addLayer();
        renderLayerList();
        showToast('新图层已添加', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function addToHistory(command, source) {
    const container = document.getElementById('historyList');
    const emptyEl = container.querySelector('.empty-history');
    if (emptyEl) emptyEl.remove();
    
    const item = document.createElement('div');
    item.className = 'history-item';
    
    const icon = getCommandIcon(command.type);
    const typeName = toolNames[command.type] || command.type;
    const userName = source === 'local' ? '你' : (command.userName || '未知用户');
    
    item.innerHTML = `
        <div class="history-item-icon">${icon}</div>
        <div class="history-item-content">
            <div class="history-item-type">${typeName}</div>
            <div class="history-item-user">${userName} · ${new Date().toLocaleTimeString()}</div>
        </div>
    `;
    
    container.insertBefore(item, container.firstChild);
    
    while (container.children.length > 50) {
        container.removeChild(container.lastChild);
    }
}

function getCommandIcon(type) {
    const icons = {
        'pen': '✏️',
        'erase': '🧹',
        'line': '📏',
        'rect': '⬜',
        'circle': '⭕',
        'text': '🔤'
    };
    return icons[type] || '🎨';
}

function updateHistoryButtons() {
    const undoBtn = document.getElementById('undoBtn');
    const redoBtn = document.getElementById('redoBtn');
    
    undoBtn.disabled = !commandHistory.canUndo();
    redoBtn.disabled = !commandHistory.canRedo();
}

function updateLineWidthPreview(width) {
    document.getElementById('linePreview').style.height = width + 'px';
}

function exportToPNG() {
    try {
        const dataUrl = canvasRenderer.exportToPNG();
        const link = document.createElement('a');
        link.download = `whiteboard-${currentRoomCode}-${Date.now()}.png`;
        link.href = dataUrl;
        link.click();
        showToast('已导出为 PNG 图片', 'success');
    } catch (err) {
        showToast('导出失败', 'error');
        console.error('Export error:', err);
    }
}

function copyRoomCode() {
    navigator.clipboard.writeText(currentRoomCode).then(() => {
        showToast('邀请码已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败，请手动复制', 'error');
    });
}

function leaveRoom() {
    if (confirm('确定要离开房间吗？')) {
        if (voiceChatManager && voiceEnabled) {
            voiceChatManager.leave();
        }
        sessionStorage.clear();
        socketClient.disconnect();
        window.location.href = '/';
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function toggleVoiceChat() {
    if (!voiceChatManager) {
        showToast('您的浏览器不支持语音对讲功能', 'error');
        return;
    }

    if (!voiceEnabled) {
        const result = await voiceChatManager.join();
        if (!result.success) {
            showToast(result.error, 'error');
        }
    } else {
        await leaveVoiceChat();
    }
}

async function leaveVoiceChat() {
    if (voiceChatManager) {
        await voiceChatManager.leave();
    }
}

function toggleVoiceMute() {
    if (voiceChatManager) {
        voiceChatManager.toggleMute();
    }
}

async function toggleMuteAll() {
    if (!voiceChatManager || !voiceChatManager.isAdmin) return;

    const allMuted = voiceParticipants
        .filter(p => p.userId !== currentUserId)
        .every(p => p.isMuted);

    const result = await voiceChatManager.muteAll(!allMuted);
    if (result.success) {
        showToast(allMuted ? '已解除全体静音' : '已全体静音', 'success');
    } else {
        showToast(result.error, 'error');
    }
}

function handleVoiceJoined(participants) {
    voiceEnabled = true;
    voiceParticipants = participants;

    document.getElementById('voiceJoinBtn').style.display = 'none';
    document.getElementById('voicePTTBtn').style.display = 'flex';
    document.getElementById('voiceMuteBtn').style.display = 'flex';
    document.getElementById('voiceLeaveBtn').style.display = 'flex';
    document.getElementById('voiceAudioMeter').style.display = 'block';
    document.getElementById('voicePeerList').style.display = 'flex';

    if (voiceChatManager.isAdmin) {
        document.getElementById('voiceAdminControls').style.display = 'flex';
    }

    updateVoiceStatus('connected');
    updateVoicePeerList();
    showToast('已加入语音对讲', 'success');
}

function handleVoiceLeft() {
    voiceEnabled = false;
    voiceParticipants = [];

    document.getElementById('voiceJoinBtn').style.display = 'flex';
    document.getElementById('voicePTTBtn').style.display = 'none';
    document.getElementById('voiceMuteBtn').style.display = 'none';
    document.getElementById('voiceLeaveBtn').style.display = 'none';
    document.getElementById('voiceAudioMeter').style.display = 'none';
    document.getElementById('voiceAdminControls').style.display = 'none';
    document.getElementById('voicePeerList').style.display = 'none';

    document.getElementById('voiceMuteBtn').classList.remove('is-muted');
    document.getElementById('voiceMuteBtn').innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
        </svg>
        静音
    `;

    updateVoiceStatus('disconnected');
    updateVoicePeerList();
    showToast('已离开语音对讲', 'info');
}

function handleVoiceParticipantJoined(user) {
    const existing = voiceParticipants.find(p => p.userId === user.userId);
    if (!existing) {
        voiceParticipants.push(user);
    }
    updateVoicePeerList();
    showToast(`${user.userName} 加入了语音`, 'success');
}

function handleVoiceParticipantLeft(userId, newAdminId) {
    voiceParticipants = voiceParticipants.filter(p => p.userId !== userId);

    if (newAdminId === currentUserId && !voiceChatManager.isAdmin) {
        voiceChatManager.isAdmin = true;
        document.getElementById('voiceAdminControls').style.display = 'flex';
        showToast('你已成为语音管理员', 'info');
    }

    updateVoicePeerList();
    showToast('有用户离开了语音', 'warning');
}

function handleVoiceSpeakingChange(userId, isSpeaking) {
    const participant = voiceParticipants.find(p => p.userId === userId);
    if (participant) {
        participant.isSpeaking = isSpeaking;
    }
    updateVoicePeerList();
}

function handleVoiceMuteChange(userId, isMuted, isForced) {
    if (userId === currentUserId) {
        const muteBtn = document.getElementById('voiceMuteBtn');
        if (isMuted) {
            muteBtn.classList.add('is-muted');
            muteBtn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <line x1="23" y1="9" x2="17" y2="15"/>
                    <line x1="17" y1="9" x2="23" y2="15"/>
                </svg>
                解除静音
            `;
            updateVoiceStatus('muted');
        } else {
            muteBtn.classList.remove('is-muted');
            muteBtn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
                静音
            `;
            updateVoiceStatus('connected');
        }

        if (isForced) {
            showToast(isMuted ? '管理员已将你静音' : '管理员已解除你的静音', 'warning');
        }
    }

    const participant = voiceParticipants.find(p => p.userId === userId);
    if (participant) {
        participant.isMuted = isMuted;
    }

    updateVoicePeerList();
}

function handleVoiceError(errorMessage) {
    showToast(errorMessage, 'error');
}

function handleVoiceVolumeChange(userId, volume) {
    if (userId === currentUserId) {
        const meterFill = document.getElementById('voiceMeterFill');
        meterFill.style.width = (volume * 100) + '%';

        if (volume > 0.5) {
            meterFill.classList.add('is-active');
        } else {
            meterFill.classList.remove('is-active');
        }
    }
}

function handleVoiceConnectionStateChange(state) {
    updateVoiceStatus(state);
}

function updateVoiceStatus(state) {
    const statusDot = document.getElementById('voiceStatusDot');
    const statusText = document.getElementById('voiceStatusText');

    statusDot.className = 'voice-status-dot';

    switch (state) {
        case 'connected':
            statusDot.classList.add('voice-status-connected');
            statusText.textContent = '已连接';
            break;
        case 'connecting':
            statusDot.classList.add('voice-status-connecting');
            statusText.textContent = '连接中...';
            break;
        case 'reconnecting':
            statusDot.classList.add('voice-status-connecting');
            statusText.textContent = '重连中...';
            break;
        case 'muted':
            statusDot.classList.add('voice-status-muted');
            statusText.textContent = '已静音';
            break;
        case 'speaking':
            statusDot.classList.add('voice-status-speaking');
            statusText.textContent = '讲话中';
            break;
        case 'disconnected':
        default:
            statusDot.classList.add('voice-status-disconnected');
            statusText.textContent = '未连接';
            break;
    }
}

function updateVoicePeerList() {
    const container = document.getElementById('voicePeerList');

    if (!voiceEnabled || voiceParticipants.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 11px; text-align: center; padding: 8px;">暂无参与者</div>';
        return;
    }

    container.innerHTML = '';

    voiceParticipants.forEach(participant => {
        const isCurrentUser = participant.userId === currentUserId;
        const peerEl = document.createElement('div');
        peerEl.className = 'voice-peer-item';

        let stateClass = 'is-idle';
        let stateText = '空闲';

        if (participant.isSpeaking && !participant.isMuted) {
            stateClass = 'is-speaking';
            stateText = '讲话中';
        } else if (participant.isMuted) {
            stateClass = 'is-muted';
            stateText = '静音';
        }

        peerEl.innerHTML = `
            <div class="voice-peer-avatar" style="background: ${participant.userColor}">
                ${participant.userName.charAt(0).toUpperCase()}
            </div>
            <div class="voice-peer-name">
                ${participant.userName}${isCurrentUser ? ' (你)' : ''}
                ${participant.isAdmin ? '<span style="color: var(--warning-color); font-size: 9px;"> 管理员</span>' : ''}
            </div>
            <div class="voice-peer-state">
                <span class="voice-peer-state-dot ${stateClass}"></span>
                ${stateText}
            </div>
        `;

        if (voiceChatManager.isAdmin && !isCurrentUser) {
            peerEl.style.cursor = 'pointer';
            peerEl.addEventListener('click', async () => {
                const newMuteState = !participant.isMuted;
                const result = await voiceChatManager.muteUser(participant.userId, newMuteState);
                if (result.success) {
                    showToast(newMuteState ? `已静音 ${participant.userName}` : `已解除 ${participant.userName} 的静音`, 'success');
                } else {
                    showToast(result.error, 'error');
                }
            });
        }

        container.appendChild(peerEl);
    });
}
