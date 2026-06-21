const roomHandler = require('./room');
const drawingHandler = require('./drawing');
const historyHandler = require('./history');
const voiceHandler = require('./voice');

const roomState = new Map();
const roomSequence = new Map();

module.exports = function(io) {
    io.on('connection', (socket) => {
        socket.on('error', (err) => {
        });

        socket.on('disconnect', (reason) => {
        });

        roomHandler(io, socket, roomState);
        drawingHandler(io, socket, roomState, roomSequence);
        historyHandler(io, socket, roomState, roomSequence);
        voiceHandler(io, socket, roomState);
    });
};
