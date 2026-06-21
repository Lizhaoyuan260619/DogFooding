const MAX_PARTICIPANTS = 10;

const voiceSessions = new Map();

module.exports = function(io, socket, roomState) {
    function getRoomState(roomCode) {
        if (!voiceSessions.has(roomCode)) {
            voiceSessions.set(roomCode, {
                participants: new Map(),
                adminId: null,
                createdAt: Date.now()
            });
        }
        return voiceSessions.get(roomCode);
    }

    function broadcastVoiceState(roomCode) {
        const session = voiceSessions.get(roomCode);
        if (!session) return;

        const participants = Array.from(session.participants.values()).map(p => ({
            userId: p.userId,
            userName: p.userName,
            userColor: p.userColor,
            isMuted: p.isMuted,
            isSpeaking: p.isSpeaking,
            isAdmin: p.userId === session.adminId
        }));

        io.to(roomCode).emit('voice:state', {
            participants,
            adminId: session.adminId
        });
    }

    socket.on('voice:join', async ({ roomCode }, callback) => {
        try {
            const state = roomState.get(socket.id);
            if (!state || state.roomCode !== roomCode) {
                return callback({ success: false, error: '未加入房间' });
            }

            const session = getRoomState(roomCode);

            if (session.participants.size >= MAX_PARTICIPANTS) {
                return callback({ success: false, error: `语音会话最多支持 ${MAX_PARTICIPANTS} 人` });
            }

            if (!session.adminId) {
                session.adminId = state.userId;
            }

            session.participants.set(state.userId, {
                userId: state.userId,
                userName: state.userName,
                userColor: state.color,
                socketId: socket.id,
                isMuted: false,
                isSpeaking: false,
                joinedAt: Date.now()
            });

            callback({
                success: true,
                isAdmin: state.userId === session.adminId,
                participants: Array.from(session.participants.values()).map(p => ({
                    userId: p.userId,
                    userName: p.userName,
                    userColor: p.userColor,
                    isMuted: p.isMuted,
                    isSpeaking: p.isSpeaking,
                    isAdmin: p.userId === session.adminId
                }))
            });

            broadcastVoiceState(roomCode);

            socket.to(roomCode).emit('voice:user-joined', {
                user: {
                    userId: state.userId,
                    userName: state.userName,
                    userColor: state.color,
                    isMuted: false,
                    isSpeaking: false,
                    isAdmin: state.userId === session.adminId
                }
            });
        } catch (err) {
            console.error('voice:join error:', err);
            callback({ success: false, error: '加入语音失败' });
        }
    });

    socket.on('voice:leave', async ({ roomCode }, callback) => {
        try {
            const state = roomState.get(socket.id);
            if (!state) return callback({ success: true });

            const session = voiceSessions.get(roomCode);
            if (!session) return callback({ success: true });

            const wasAdmin = state.userId === session.adminId;
            session.participants.delete(state.userId);

            if (wasAdmin && session.participants.size > 0) {
                const firstParticipant = session.participants.values().next().value;
                session.adminId = firstParticipant.userId;
            }

            if (session.participants.size === 0) {
                voiceSessions.delete(roomCode);
            } else {
                broadcastVoiceState(roomCode);
            }

            callback({ success: true });

            socket.to(roomCode).emit('voice:user-left', {
                userId: state.userId,
                newAdminId: wasAdmin ? session.adminId : null
            });
        } catch (err) {
            console.error('voice:leave error:', err);
            callback({ success: false, error: '离开语音失败' });
        }
    });

    socket.on('voice:mute', async ({ roomCode, isMuted, targetUserId }, callback) => {
        try {
            const state = roomState.get(socket.id);
            if (!state) return callback({ success: false, error: '未加入房间' });

            const session = voiceSessions.get(roomCode);
            if (!session) return callback({ success: false, error: '语音会话不存在' });

            if (targetUserId && targetUserId !== state.userId) {
                if (state.userId !== session.adminId) {
                    return callback({ success: false, error: '仅管理员可静音他人' });
                }

                const targetParticipant = session.participants.get(targetUserId);
                if (!targetParticipant) {
                    return callback({ success: false, error: '目标用户不存在' });
                }

                targetParticipant.isMuted = isMuted;

                io.to(targetParticipant.socketId).emit('voice:mute-forced', { isMuted });
            } else {
                const participant = session.participants.get(state.userId);
                if (participant) {
                    participant.isMuted = isMuted;
                }
            }

            callback({ success: true });
            broadcastVoiceState(roomCode);
        } catch (err) {
            console.error('voice:mute error:', err);
            callback({ success: false, error: '操作失败' });
        }
    });

    socket.on('voice:mute-all', async ({ roomCode, isMuted }, callback) => {
        try {
            const state = roomState.get(socket.id);
            if (!state) return callback({ success: false, error: '未加入房间' });

            const session = voiceSessions.get(roomCode);
            if (!session) return callback({ success: false, error: '语音会话不存在' });

            if (state.userId !== session.adminId) {
                return callback({ success: false, error: '仅管理员可全体静音' });
            }

            for (const participant of session.participants.values()) {
                if (participant.userId !== session.adminId) {
                    participant.isMuted = isMuted;
                    io.to(participant.socketId).emit('voice:mute-forced', { isMuted });
                }
            }

            callback({ success: true });
            broadcastVoiceState(roomCode);
        } catch (err) {
            console.error('voice:mute-all error:', err);
            callback({ success: false, error: '操作失败' });
        }
    });

    socket.on('voice:speaking', async ({ roomCode, isSpeaking }) => {
        try {
            const state = roomState.get(socket.id);
            if (!state) return;

            const session = voiceSessions.get(roomCode);
            if (!session) return;

            const participant = session.participants.get(state.userId);
            if (participant && participant.isSpeaking !== isSpeaking) {
                participant.isSpeaking = isSpeaking;

                socket.to(roomCode).emit('voice:speaking-change', {
                    userId: state.userId,
                    isSpeaking
                });
            }
        } catch (err) {
            console.error('voice:speaking error:', err);
        }
    });

    socket.on('voice:signal', async ({ targetUserId, data }) => {
        try {
            const state = roomState.get(socket.id);
            if (!state) return;

            const session = voiceSessions.get(state.roomCode);
            if (!session) return;

            const targetParticipant = session.participants.get(targetUserId);
            if (!targetParticipant) return;

            io.to(targetParticipant.socketId).emit('voice:signal', {
                senderUserId: state.userId,
                senderUserName: state.userName,
                senderUserColor: state.color,
                data
            });
        } catch (err) {
            console.error('voice:signal error:', err);
        }
    });

    socket.on('voice:network-stats', async ({ roomCode, stats }) => {
        try {
            const state = roomState.get(socket.id);
            if (!state) return;

            socket.to(roomCode).emit('voice:network-update', {
                userId: state.userId,
                stats
            });
        } catch (err) {
            console.error('voice:network-stats error:', err);
        }
    });

    socket.on('disconnect', async () => {
        const state = roomState.get(socket.id);
        if (!state) return;

        const session = voiceSessions.get(state.roomCode);
        if (!session) return;

        const participant = session.participants.get(state.userId);
        if (!participant) return;

        const wasAdmin = state.userId === session.adminId;
        session.participants.delete(state.userId);

        if (wasAdmin && session.participants.size > 0) {
            const firstParticipant = session.participants.values().next().value;
            session.adminId = firstParticipant.userId;
        }

        if (session.participants.size === 0) {
            voiceSessions.delete(state.roomCode);
        } else {
            broadcastVoiceState(state.roomCode);
        }

        socket.to(state.roomCode).emit('voice:user-left', {
            userId: state.userId,
            newAdminId: wasAdmin ? session.adminId : null
        });
    });
};
