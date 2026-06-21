const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, '..', 'whiteboard.db');
const db = new sqlite3.Database(dbPath);

function initDB() {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run(`CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )`);

            db.run(`CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                socket_id TEXT UNIQUE NOT NULL,
                room_code TEXT NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_code) REFERENCES rooms(code)
            )`);

            db.run(`CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                command_type TEXT NOT NULL,
                layer_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_code) REFERENCES rooms(code),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )`, (err) => {
                if (err) reject(err);
                else resolve();
            });
        });
    });
}

function createRoom(code) {
    return new Promise((resolve, reject) => {
        const stmt = db.prepare('INSERT INTO rooms (code) VALUES (?)');
        stmt.run(code, function(err) {
            if (err) reject(err);
            else resolve(this.lastID);
        });
        stmt.finalize();
    });
}

function getRoom(code) {
    return new Promise((resolve, reject) => {
        db.get('SELECT * FROM rooms WHERE code = ?', [code], (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
}

function addUser(userId, socketId, roomCode, name, color) {
    return new Promise((resolve, reject) => {
        const stmt = db.prepare('INSERT INTO users (id, socket_id, room_code, name, color) VALUES (?, ?, ?, ?, ?)');
        stmt.run(userId, socketId, roomCode, name, color, function(err) {
            if (err) reject(err);
            else resolve();
        });
        stmt.finalize();
    });
}

function removeUser(socketId) {
    return new Promise((resolve, reject) => {
        db.get('SELECT room_code FROM users WHERE socket_id = ?', [socketId], (err, user) => {
            if (err) return reject(err);
            const roomCode = user ? user.room_code : null;
            db.run('DELETE FROM users WHERE socket_id = ?', [socketId], (err) => {
                if (err) reject(err);
                else resolve(roomCode);
            });
        });
    });
}

function getUsersByRoom(roomCode) {
    return new Promise((resolve, reject) => {
        db.all('SELECT id, name, color FROM users WHERE room_code = ?', [roomCode], (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
}

function saveCommand(roomCode, userId, userName, commandType, layerId, payload, sequence) {
    return new Promise((resolve, reject) => {
        const stmt = db.prepare(
            'INSERT INTO commands (room_code, user_id, user_name, command_type, layer_id, payload, sequence) VALUES (?, ?, ?, ?, ?, ?, ?)'
        );
        stmt.run(roomCode, userId, userName, commandType, layerId, JSON.stringify(payload), sequence, function(err) {
            if (err) reject(err);
            else resolve(this.lastID);
        });
        stmt.finalize();
    });
}

function getCommandsByRoom(roomCode) {
    return new Promise((resolve, reject) => {
        db.all(
            'SELECT id, command_type, layer_id, payload, user_id, user_name, sequence FROM commands WHERE room_code = ? ORDER BY sequence ASC',
            [roomCode],
            (err, rows) => {
                if (err) reject(err);
                else resolve(rows.map(row => ({
                    ...row,
                    payload: JSON.parse(row.payload)
                })));
            }
        );
    });
}

function getNextSequence(roomCode) {
    return new Promise((resolve, reject) => {
        db.get('SELECT COALESCE(MAX(sequence), 0) + 1 as next_seq FROM commands WHERE room_code = ?', [roomCode], (err, row) => {
            if (err) reject(err);
            else resolve(row ? row.next_seq : 1);
        });
    });
}

function deleteCommandsAfterSequence(roomCode, sequence) {
    return new Promise((resolve, reject) => {
        db.run('DELETE FROM commands WHERE room_code = ? AND sequence > ?', [roomCode, sequence], (err) => {
            if (err) reject(err);
            else resolve();
        });
    });
}

module.exports = {
    db,
    initDB,
    createRoom,
    getRoom,
    addUser,
    removeUser,
    getUsersByRoom,
    saveCommand,
    getCommandsByRoom,
    getNextSequence,
    deleteCommandsAfterSequence
};
