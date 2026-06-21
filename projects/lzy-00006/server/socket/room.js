const { getRoom, createRoom, addUser, removeUser, getUsersByRoom, getCommandsByRoom } = require('../db');

const userColors = [
    '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6',
    '#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#06b6d4'
];

function generateRoomCode() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

function generateUserId() {
    return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function getRandomColor() {
    return userColors[Math.floor(Math.random() * userColors.length)];
}

function sanitizeName(name) {
    return String(name).trim().substring(0, 20).replace(/[<>]/g, '');
}

module.exports = function(io, socket, roomState) {
    socket.on('room:create', async ({ userName }, callback) => {
        try {
            const cleanName = sanitizeName(userName);
            if (!cleanName) {
                return callback({ success: false, error: '请输入有效的昵称' });
            }

            let code;
            let existing;
            do {
                code = generateRoomCode();
                existing = await getRoom(code);
            } while (existing);

            await createRoom(code);

            const userId = generateUserId();
            const color = getRandomColor();
            await addUser(userId, socket.id, code, cleanName, color);

            socket.join(code);
            roomState.set(socket.id, { roomCode: code, userId, userName: cleanName, color });

            const users = await getUsersByRoom(code);
            const commands = await getCommandsByRoom(code);

            callback({
                success: true,
                roomCode: code,
                userId,
                userName: cleanName,
                color,
                users,
                commands
            });
        } catch (err) {
            console.error('Create room error:', err);
            callback({ success: false, error: '创建房间失败' });
        }
    });

    socket.on('room:join', async ({ roomCode, userName }, callback) => {
        try {
            const cleanCode = String(roomCode).trim().toUpperCase();
            const cleanName = sanitizeName(userName);

            if (!cleanName) {
                return callback({ success: false, error: '请输入有效的昵称' });
            }

            if (!cleanCode || cleanCode.length !== 6) {
                return callback({ success: false, error: '请输入有效的邀请码' });
            }

            const room = await getRoom(cleanCode);
            if (!room) {
                return callback({ success: false, error: '房间不存在' });
            }

            const userId = generateUserId();
            const color = getRandomColor();
            await addUser(userId, socket.id, cleanCode, cleanName, color);

            socket.join(cleanCode);
            roomState.set(socket.id, { roomCode: cleanCode, userId, userName: cleanName, color });

            const users = await getUsersByRoom(cleanCode);
            const commands = await getCommandsByRoom(cleanCode);

            io.to(cleanCode).emit('room:user-joined', {
                user: { id: userId, name: cleanName, color }
            });

            callback({
                success: true,
                roomCode: cleanCode,
                userId,
                userName: cleanName,
                color,
                users,
                commands
            });
        } catch (err) {
            console.error('Join room error:', err);
            callback({ success: false, error: '加入房间失败' });
        }
    });

    socket.on('cursor:move', async ({ x, y }) => {
        const state = roomState.get(socket.id);
        if (!state) return;

        socket.to(state.roomCode).emit('cursor:update', {
            userId: state.userId,
            x,
            y,
            name: state.userName,
            color: state.color
        });
    });

    socket.on('disconnect', async () => {
        const state = roomState.get(socket.id);
        if (!state) return;

        try {
            const roomCode = await removeUser(socket.id);
            if (roomCode) {
                roomState.delete(socket.id);
                const users = await getUsersByRoom(roomCode);
                io.to(roomCode).emit('room:user-left', { userId: state.userId });
                io.to(roomCode).emit('room:users', { users });
            }
        } catch (err) {
            console.error('Disconnect error:', err);
        }
    });
};
