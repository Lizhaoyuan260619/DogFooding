const { saveCommand, getNextSequence, deleteCommandsAfterSequence } = require('../db');

const validCommandTypes = ['path', 'line', 'rect', 'circle', 'text', 'erase'];

function validateCommand(command) {
    if (!command || typeof command !== 'object') return false;
    if (!validCommandTypes.includes(command.type)) return false;
    if (!command.layerId || typeof command.layerId !== 'string') return false;
    if (!command.userId || typeof command.userId !== 'string') return false;
    if (!command.userName || typeof command.userName !== 'string') return false;
    return true;
}

module.exports = function(io, socket, roomState, roomSequence) {
    socket.on('draw:command', async ({ command }) => {
        const state = roomState.get(socket.id);
        if (!state) return;

        if (!validateCommand(command)) {
            console.warn('Invalid command received:', command);
            return;
        }

        try {
            const sequence = await getNextSequence(state.roomCode);
            roomSequence.set(state.roomCode, sequence);

            await deleteCommandsAfterSequence(state.roomCode, sequence - 1);

            const commandId = await saveCommand(
                state.roomCode,
                command.userId,
                command.userName,
                command.type,
                command.layerId,
                command,
                sequence
            );

            socket.to(state.roomCode).emit('draw:command', {
                command: { ...command, id: commandId, sequence },
                fromUserId: state.userId
            });
        } catch (err) {
            console.error('Draw command error:', err);
        }
    });
};
