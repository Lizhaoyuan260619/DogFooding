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
