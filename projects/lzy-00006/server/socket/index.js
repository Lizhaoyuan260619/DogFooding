const roomHandler = require('./room');
const drawingHandler = require('./drawing');
const historyHandler = require('./history');

const roomState = new Map();
const roomSequence = new Map();

module.exports = function(io) {
    io.on('connection', (socket) => {
        roomHandler(io, socket, roomState);
        drawingHandler(io, socket, roomState, roomSequence);
        historyHandler(io, socket, roomState, roomSequence);
    });
};
