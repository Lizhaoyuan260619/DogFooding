let layerManager, commandHistory, canvasRenderer, socketClient;
let voiceClient;
let currentUserId, currentUserName, currentUserColor, currentRoomCode;
let users = [];
let remoteCursors = {};
let voicePeers = new Map();

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
    initUIEventBindings();
    loadInitialData();
}

function initCoreInstances() {
    const canvasWidth = 1920;
    const canvasHeight = 1080;
    
    layerManager = new LayerManager(5, canvasWidth, canvasHeight);
    commandHistory = new CommandHistory();
    
    const container = document.getElementById('canvasContainer');
    canvasRenderer = new CanvasRenderer(container, layerManager, commandHistory);
    canvasRenderer.setUser(currentUserId, currentUserName);
    
    socketClient = new SocketClient();
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

    initVoice();
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

    initVoiceEventBindings();
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
        if (voiceClient) {
            voiceClient.leave();
        }
        sessionStorage.clear();
        socketClient.disconnect();
        window.location.href = '/';
    }
}

function initVoice() {
    voiceClient = new VoiceClient(socketClient.socket);

    voiceClient.setOnStatusChangeCallback(handleVoiceStatusChange);
    voiceClient.setOnPeerJoinedCallback(handleVoicePeerJoined);
    voiceClient.setOnPeerLeftCallback(handleVoicePeerLeft);
    voiceClient.setOnPeerMuteStatusCallback(handleVoicePeerMuteStatus);
    voiceClient.setOnPeerSpeakingCallback(handleVoicePeerSpeaking);
    voiceClient.setOnAudioLevelCallback(handleVoiceAudioLevel);
}

function initVoiceEventBindings() {
    document.getElementById('voiceJoinBtn').addEventListener('click', handleVoiceJoin);
    document.getElementById('voiceMuteBtn').addEventListener('click', handleVoiceMuteToggle);

    const pttBtn = document.getElementById('voicePTTBtn');
    pttBtn.addEventListener('mousedown', handleVoicePTTStart);
    pttBtn.addEventListener('mouseup', handleVoicePTTStop);
    pttBtn.addEventListener('mouseleave', handleVoicePTTStop);
    pttBtn.addEventListener('touchstart', (e) => { e.preventDefault(); handleVoicePTTStart(); });
    pttBtn.addEventListener('touchend', (e) => { e.preventDefault(); handleVoicePTTStop(); });

    document.getElementById('voiceLeaveBtn').addEventListener('click', handleVoiceLeave);

    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && voiceClient && voiceClient.isJoined && !e.target.closest('input, textarea, [contenteditable]')) {
            e.preventDefault();
            voiceClient.startPTT();
            const pttBtn = document.getElementById('voicePTTBtn');
            if (pttBtn) pttBtn.classList.add('is-ptt-active');
        }
    });

    document.addEventListener('keyup', (e) => {
        if (e.code === 'Space' && voiceClient && voiceClient.isJoined) {
            voiceClient.stopPTT();
            const pttBtn = document.getElementById('voicePTTBtn');
            if (pttBtn) pttBtn.classList.remove('is-ptt-active');
        }
    });
}

async function handleVoiceJoin() {
    if (!voiceClient) return;
    const success = await voiceClient.join();
    if (success) {
        document.getElementById('voiceJoinBtn').style.display = 'none';
        document.getElementById('voiceMuteBtn').style.display = 'flex';
        document.getElementById('voicePTTBtn').style.display = 'flex';
        document.getElementById('voiceLeaveBtn').style.display = 'flex';
        document.getElementById('voiceAudioMeter').style.display = 'block';
        showToast('已加入语音频道', 'success');
    } else {
        showToast('无法访问麦克风，请检查权限设置', 'error');
    }
}

function handleVoiceMuteToggle() {
    if (!voiceClient) return;
    const isMuted = voiceClient.toggleMute();
    const btn = document.getElementById('voiceMuteBtn');
    const iconUnmuted = btn.querySelector('.icon-unmuted');
    const iconMuted = btn.querySelector('.icon-muted');
    const label = btn.querySelector('.mute-label');

    if (isMuted) {
        btn.classList.add('is-muted');
        iconUnmuted.style.display = 'none';
        iconMuted.style.display = 'block';
        label.textContent = '取消静音';
    } else {
        btn.classList.remove('is-muted');
        iconUnmuted.style.display = 'block';
        iconMuted.style.display = 'none';
        label.textContent = '静音';
    }
}

function handleVoicePTTStart() {
    if (!voiceClient) return;
    voiceClient.startPTT();
    document.getElementById('voicePTTBtn').classList.add('is-ptt-active');
}

function handleVoicePTTStop() {
    if (!voiceClient) return;
    voiceClient.stopPTT();
    document.getElementById('voicePTTBtn').classList.remove('is-ptt-active');
}

function handleVoiceLeave() {
    if (!voiceClient) return;
    voiceClient.leave();
    document.getElementById('voiceJoinBtn').style.display = 'flex';
    document.getElementById('voiceMuteBtn').style.display = 'none';
    document.getElementById('voicePTTBtn').style.display = 'none';
    document.getElementById('voiceLeaveBtn').style.display = 'none';
    document.getElementById('voiceAudioMeter').style.display = 'none';
    document.getElementById('voicePeerList').innerHTML = '';
    voicePeers.clear();

    const muteBtn = document.getElementById('voiceMuteBtn');
    muteBtn.classList.remove('is-muted');
    muteBtn.querySelector('.icon-unmuted').style.display = 'block';
    muteBtn.querySelector('.icon-muted').style.display = 'none';
    muteBtn.querySelector('.mute-label').textContent = '静音';

    showToast('已离开语音频道', 'warning');
}

function handleVoiceStatusChange(status) {
    const dot = document.querySelector('.voice-status-dot');
    const text = document.querySelector('.voice-status-text');
    dot.className = 'voice-status-dot';

    switch (status) {
        case 'connected':
            dot.classList.add(voiceClient.isMuted ? 'voice-status-muted' : 'voice-status-connected');
            text.textContent = voiceClient.isMuted ? '静音中' : '已连接';
            break;
        case 'connecting':
            dot.classList.add('voice-status-connecting');
            text.textContent = '连接中';
            break;
        case 'disconnected':
            dot.classList.add('voice-status-disconnected');
            text.textContent = '未连接';
            break;
    }

    if (voiceClient && voiceClient.isSpeaking && !voiceClient.isMuted) {
        dot.className = 'voice-status-dot voice-status-speaking';
        text.textContent = '正在讲话';
    }
}

function handleVoicePeerJoined(data) {
    voicePeers.set(data.socketId, {
        userId: data.userId,
        userName: data.userName,
        color: data.color,
        isMuted: false,
        isSpeaking: false
    });
    renderVoicePeerList();
    showToast(`${data.userName} 加入了语音`, 'info');
}

function handleVoicePeerLeft(data) {
    const peer = voicePeers.get(data.socketId);
    voicePeers.delete(data.socketId);
    renderVoicePeerList();
    if (peer) {
        showToast(`${peer.userName} 离开了语音`, 'warning');
    }
}

function handleVoicePeerMuteStatus(data) {
    const peer = voicePeers.get(data.socketId);
    if (peer) {
        peer.isMuted = data.isMuted;
        renderVoicePeerList();
    }
}

function handleVoicePeerSpeaking(data) {
    const peer = voicePeers.get(data.socketId);
    if (peer) {
        peer.isSpeaking = data.isSpeaking;
        renderVoicePeerList();
    }
}

function handleVoiceAudioLevel(level) {
    const fill = document.getElementById('voiceMeterFill');
    if (!fill) return;
    const percent = Math.min(level * 400, 100);
    fill.style.width = percent + '%';
    if (percent > 5) {
        fill.classList.add('is-active');
    } else {
        fill.classList.remove('is-active');
    }

    if (voiceClient && voiceClient.isJoined) {
        const dot = document.querySelector('.voice-status-dot');
        const text = document.querySelector('.voice-status-text');
        if (voiceClient.isSpeaking && !voiceClient.isMuted) {
            dot.className = 'voice-status-dot voice-status-speaking';
            text.textContent = '正在讲话';
        } else if (voiceClient.isMuted) {
            dot.className = 'voice-status-dot voice-status-muted';
            text.textContent = '静音中';
        } else {
            dot.className = 'voice-status-dot voice-status-connected';
            text.textContent = '已连接';
        }
    }
}

function renderVoicePeerList() {
    const container = document.getElementById('voicePeerList');
    container.innerHTML = '';

    voicePeers.forEach((peer) => {
        const item = document.createElement('div');
        item.className = 'voice-peer-item';

        let stateClass = 'is-idle';
        let stateText = '空闲';
        if (peer.isMuted) {
            stateClass = 'is-muted';
            stateText = '静音';
        } else if (peer.isSpeaking) {
            stateClass = 'is-speaking';
            stateText = '讲话中';
        }

        item.innerHTML = `
            <div class="voice-peer-avatar" style="background: ${peer.color}">${peer.userName.charAt(0).toUpperCase()}</div>
            <div class="voice-peer-name">${peer.userName}</div>
            <div class="voice-peer-state">
                <span class="voice-peer-state-dot ${stateClass}"></span>
                <span>${stateText}</span>
            </div>
        `;
        container.appendChild(item);
    });
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
