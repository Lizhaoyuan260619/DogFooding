const { getCommandsByRoom, getNextSequence, saveCommand, deleteCommandsAfterSequence } = require('../db');

module.exports = function(io, socket, roomState, roomSequence) {
    socket.on('history:undo', async () => {
        const state = roomState.get(socket.id);
        if (!state) return;

        try {
            const currentSeq = roomSequence.get(state.roomCode) || 0;
            if (currentSeq <= 0) return;

            const newSeq = currentSeq - 1;
            roomSequence.set(state.roomCode, newSeq);

            io.to(state.roomCode).emit('history:undo', {
                userId: state.userId,
                userName: state.userName,
                sequence: newSeq
            });
        } catch (err) {
            console.error('Undo error:', err);
        }
    });

    socket.on('history:redo', async () => {
        const state = roomState.get(socket.id);
        if (!state) return;

        try {
            const commands = await getCommandsByRoom(state.roomCode);
            const currentSeq = roomSequence.get(state.roomCode) || 0;

            if (currentSeq >= commands.length) return;

            const commandToRedo = commands[currentSeq];
            if (!commandToRedo) return;

            const newSeq = currentSeq + 1;
            roomSequence.set(state.roomCode, newSeq);

            io.to(state.roomCode).emit('history:redo', {
                command: {
                    ...commandToRedo.payload,
                    id: commandToRedo.id,
                    sequence: commandToRedo.sequence
                },
                userId: state.userId,
                userName: state.userName
            });
        } catch (err) {
            console.error('Redo error:', err);
        }
    });

    socket.on('history:sync', async ({ roomCode }, callback) => {
        try {
            const commands = await getCommandsByRoom(roomCode);
            callback({ success: true, commands });
        } catch (err) {
            console.error('History sync error:', err);
            callback({ success: false, error: '同步历史记录失败' });
        }
    });
};
