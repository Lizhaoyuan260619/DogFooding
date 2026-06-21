class SocketClient {
    constructor() {
        this.socket = null;
        this.roomCode = null;
        this.userId = null;
        this.userName = null;
        this.userColor = null;
        
        this.onUserJoinedCallback = null;
        this.onUserLeftCallback = null;
        this.onUsersUpdateCallback = null;
        this.onCommandReceivedCallback = null;
        this.onCursorUpdateCallback = null;
        this.onUndoCallback = null;
        this.onRedoCallback = null;

        this.onVoiceUserJoinedCallback = null;
        this.onVoiceUserLeftCallback = null;
        this.onVoiceStateCallback = null;
        this.onVoiceSignalCallback = null;
        this.onVoiceMuteForcedCallback = null;
        this.onVoiceSpeakingChangeCallback = null;
        this.onVoiceNetworkUpdateCallback = null;
    }
    
    connect() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
        
        this.socket.on('room:user-joined', (data) => {
            if (this.onUserJoinedCallback) {
                this.onUserJoinedCallback(data.user);
            }
        });
        
        this.socket.on('room:user-left', (data) => {
            if (this.onUserLeftCallback) {
                this.onUserLeftCallback(data.userId);
            }
        });
        
        this.socket.on('room:users', (data) => {
            if (this.onUsersUpdateCallback) {
                this.onUsersUpdateCallback(data.users);
            }
        });
        
        this.socket.on('cursor:update', (data) => {
            if (this.onCursorUpdateCallback) {
                this.onCursorUpdateCallback(data);
            }
        });
        
        this.socket.on('draw:command', (data) => {
            if (this.onCommandReceivedCallback) {
                this.onCommandReceivedCallback(data.command);
            }
        });
        
        this.socket.on('history:undo', (data) => {
            if (this.onUndoCallback) {
                this.onUndoCallback(data);
            }
        });
        
        this.socket.on('history:redo', (data) => {
            if (this.onRedoCallback) {
                this.onRedoCallback(data);
            }
        });

        this.socket.on('voice:user-joined', (data) => {
            if (this.onVoiceUserJoinedCallback) {
                this.onVoiceUserJoinedCallback(data);
            }
        });

        this.socket.on('voice:user-left', (data) => {
            if (this.onVoiceUserLeftCallback) {
                this.onVoiceUserLeftCallback(data);
            }
        });

        this.socket.on('voice:state', (data) => {
            if (this.onVoiceStateCallback) {
                this.onVoiceStateCallback(data);
            }
        });

        this.socket.on('voice:signal', (data) => {
            if (this.onVoiceSignalCallback) {
                this.onVoiceSignalCallback(data);
            }
        });

        this.socket.on('voice:mute-forced', (data) => {
            if (this.onVoiceMuteForcedCallback) {
                this.onVoiceMuteForcedCallback(data);
            }
        });

        this.socket.on('voice:speaking-change', (data) => {
            if (this.onVoiceSpeakingChangeCallback) {
                this.onVoiceSpeakingChangeCallback(data);
            }
        });

        this.socket.on('voice:network-update', (data) => {
            if (this.onVoiceNetworkUpdateCallback) {
                this.onVoiceNetworkUpdateCallback(data);
            }
        });
    }
    
    createRoom(userName) {
        return new Promise((resolve, reject) => {
            this.socket.emit('room:create', { userName }, (response) => {
                if (response.success) {
                    this.roomCode = response.roomCode;
                    this.userId = response.userId;
                    this.userName = response.userName;
                    this.userColor = response.color;
                    resolve(response);
                } else {
                    reject(new Error(response.error || '创建房间失败'));
                }
            });
        });
    }
    
    joinRoom(roomCode, userName) {
        return new Promise((resolve, reject) => {
            this.socket.emit('room:join', { roomCode, userName }, (response) => {
                if (response.success) {
                    this.roomCode = response.roomCode;
                    this.userId = response.userId;
                    this.userName = response.userName;
                    this.userColor = response.color;
                    resolve(response);
                } else {
                    reject(new Error(response.error || '加入房间失败'));
                }
            });
        });
    }
    
    sendCommand(command) {
        if (!this.socket || !this.roomCode) return;
        this.socket.emit('draw:command', { command: command.serialize() });
    }
    
    sendCursorMove(x, y) {
        if (!this.socket || !this.roomCode) return;
        this.socket.emit('cursor:move', { x, y });
    }
    
    sendUndo() {
        if (!this.socket || !this.roomCode) return;
        this.socket.emit('history:undo');
    }
    
    sendRedo() {
        if (!this.socket || !this.roomCode) return;
        this.socket.emit('history:redo');
    }
    
    syncHistory() {
        return new Promise((resolve, reject) => {
            this.socket.emit('history:sync', { roomCode: this.roomCode }, (response) => {
                if (response.success) {
                    resolve(response.commands);
                } else {
                    reject(new Error(response.error || '同步历史失败'));
                }
            });
        });
    }
    
    setOnUserJoinedCallback(callback) {
        this.onUserJoinedCallback = callback;
    }
    
    setOnUserLeftCallback(callback) {
        this.onUserLeftCallback = callback;
    }
    
    setOnUsersUpdateCallback(callback) {
        this.onUsersUpdateCallback = callback;
    }
    
    setOnCommandReceivedCallback(callback) {
        this.onCommandReceivedCallback = callback;
    }
    
    setOnCursorUpdateCallback(callback) {
        this.onCursorUpdateCallback = callback;
    }
    
    setOnUndoCallback(callback) {
        this.onUndoCallback = callback;
    }
    
    setOnRedoCallback(callback) {
        this.onRedoCallback = callback;
    }

    setOnVoiceUserJoinedCallback(callback) {
        this.onVoiceUserJoinedCallback = callback;
    }

    setOnVoiceUserLeftCallback(callback) {
        this.onVoiceUserLeftCallback = callback;
    }

    setOnVoiceStateCallback(callback) {
        this.onVoiceStateCallback = callback;
    }

    setOnVoiceSignalCallback(callback) {
        this.onVoiceSignalCallback = callback;
    }

    setOnVoiceMuteForcedCallback(callback) {
        this.onVoiceMuteForcedCallback = callback;
    }

    setOnVoiceSpeakingChangeCallback(callback) {
        this.onVoiceSpeakingChangeCallback = callback;
    }

    setOnVoiceNetworkUpdateCallback(callback) {
        this.onVoiceNetworkUpdateCallback = callback;
    }

    sendVoiceJoin(roomCode) {
        return new Promise((resolve, reject) => {
            this.socket.emit('voice:join', { roomCode }, (response) => {
                if (response.success) {
                    resolve(response);
                } else {
                    reject(new Error(response.error || '加入语音失败'));
                }
            });
        });
    }

    sendVoiceLeave(roomCode) {
        return new Promise((resolve, reject) => {
            this.socket.emit('voice:leave', { roomCode }, (response) => {
                if (response.success) {
                    resolve(response);
                } else {
                    reject(new Error(response.error || '离开语音失败'));
                }
            });
        });
    }

    sendVoiceMute(roomCode, isMuted, targetUserId = null) {
        return new Promise((resolve, reject) => {
            const data = { roomCode, isMuted };
            if (targetUserId) {
                data.targetUserId = targetUserId;
            }
            this.socket.emit('voice:mute', data, (response) => {
                if (response.success) {
                    resolve(response);
                } else {
                    reject(new Error(response.error || '操作失败'));
                }
            });
        });
    }

    sendVoiceMuteAll(roomCode, isMuted) {
        return new Promise((resolve, reject) => {
            this.socket.emit('voice:mute-all', { roomCode, isMuted }, (response) => {
                if (response.success) {
                    resolve(response);
                } else {
                    reject(new Error(response.error || '操作失败'));
                }
            });
        });
    }

    sendVoiceSpeaking(roomCode, isSpeaking) {
        if (!this.socket || !roomCode) return;
        this.socket.emit('voice:speaking', { roomCode, isSpeaking });
    }

    sendVoiceSignal(targetUserId, data) {
        if (!this.socket) return;
        this.socket.emit('voice:signal', { targetUserId, data });
    }

    sendVoiceNetworkStats(roomCode, stats) {
        if (!this.socket || !roomCode) return;
        this.socket.emit('voice:network-stats', { roomCode, stats });
    }
    
    getUserInfo() {
        return {
            userId: this.userId,
            userName: this.userName,
            userColor: this.userColor,
            roomCode: this.roomCode
        };
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }
}

window.SocketClient = SocketClient;
