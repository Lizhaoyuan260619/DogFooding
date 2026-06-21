const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const { initDB } = require('./db');
const socketHandler = require('./socket');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, '..', 'public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

app.get('/board', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'board.html'));
});

process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection:', reason);
});

initDB()
    .then(() => {
        socketHandler(io);

        server.listen(PORT, () => {
            console.log(`Server running on http://localhost:${PORT}`);
        });

        server.on('error', (err) => {
            console.error('Server error:', err);
        });
    })
    .catch((err) => {
        console.error('Failed to initialize database:', err);
        process.exit(1);
    });
