let layerManager, commandHistory, canvasRenderer, socketClient;
let currentUserId, currentUserName, currentUserColor, currentRoomCode;
let users = [];
let remoteCursors = {};

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
