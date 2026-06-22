const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const { initDb, getDb } = require('./db');
const keyManager = require('./keys');
const contactManager = require('./contacts');
const { encryptMessage } = require('./encrypt');
const { decryptMessage } = require('./decrypt');
const signatureModule = require('./sign');
const { shredFile } = require('./shred');

const PUBLIC_DIR = path.join(__dirname, 'public');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml',
};

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}

function sendError(res, statusCode, message) {
  sendJson(res, statusCode, { error: message });
}

function serveStatic(req, res) {
  let filePath = path.join(PUBLIC_DIR, req.pathname === '/' ? 'index.html' : req.pathname);
  const ext = path.extname(filePath);
  if (!MIME_TYPES[ext]) {
    sendError(res, 403, 'Forbidden file type');
    return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      sendError(res, 404, 'Not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] });
    res.end(data);
  });
}

const API_ROUTES = {
  'POST /api/init': async (req, res) => {
    const dbPath = initDb();
    sendJson(res, 200, { message: 'Database initialized', path: dbPath });
  },

  'GET /api/keys': async (req, res) => {
    const keys = keyManager.listKeyPairs();
    sendJson(res, 200, keys);
  },

  'POST /api/keys/generate': async (req, res) => {
    const { name, password, confirmPassword } = await parseBody(req);
    if (!name) return sendError(res, 400, 'Key pair name is required');
    if (!password) return sendError(res, 400, 'Password is required');
    if (password !== confirmPassword) return sendError(res, 400, 'Passwords do not match');
    try {
      const result = keyManager.generateKeyPair(name, password);
      sendJson(res, 201, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/keys/export-pub': async (req, res) => {
    const { name, outputPath } = await parseBody(req);
    if (!name) return sendError(res, 400, 'Key pair name is required');
    if (!outputPath) return sendError(res, 400, 'Output path is required');
    try {
      const result = keyManager.exportPublicKey(name, outputPath);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/keys/export-priv': async (req, res) => {
    const { name, outputPath, password } = await parseBody(req);
    if (!name) return sendError(res, 400, 'Key pair name is required');
    if (!outputPath) return sendError(res, 400, 'Output path is required');
    if (!password) return sendError(res, 400, 'Password is required');
    try {
      const result = keyManager.exportPrivateKey(name, outputPath, password);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/keys/import': async (req, res) => {
    const { name, publicKeyPath, privateKeyPath, password } = await parseBody(req);
    if (!name) return sendError(res, 400, 'Key pair name is required');
    if (!publicKeyPath) return sendError(res, 400, 'Public key path is required');
    if (!privateKeyPath) return sendError(res, 400, 'Private key path is required');
    if (!password) return sendError(res, 400, 'Password is required');
    try {
      const result = keyManager.importKeyPair(name, publicKeyPath, privateKeyPath, password);
      sendJson(res, 201, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'DELETE /api/keys/:name': async (req, res) => {
    const name = decodeURIComponent(req.params.name);
    if (!name) return sendError(res, 400, 'Key pair name is required');
    try {
      keyManager.deleteKeyPair(name);
      sendJson(res, 200, { message: `Key pair "${name}" deleted` });
    } catch (err) {
      sendError(res, 404, err.message);
    }
  },

  'GET /api/contacts': async (req, res) => {
    const contacts = contactManager.listContacts();
    sendJson(res, 200, contacts);
  },

  'POST /api/contacts': async (req, res) => {
    const { nickname, publicKeyPath } = await parseBody(req);
    if (!nickname) return sendError(res, 400, 'Nickname is required');
    if (!publicKeyPath) return sendError(res, 400, 'Public key path is required');
    try {
      const result = contactManager.addContact(nickname, publicKeyPath);
      sendJson(res, 201, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'PUT /api/contacts/:nickname': async (req, res) => {
    const nickname = decodeURIComponent(req.params.nickname);
    const { newNickname, newPublicKeyPath } = await parseBody(req);
    if (!nickname) return sendError(res, 400, 'Nickname is required');
    try {
      const result = contactManager.updateContact(nickname, newNickname, newPublicKeyPath);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'DELETE /api/contacts/:nickname': async (req, res) => {
    const nickname = decodeURIComponent(req.params.nickname);
    if (!nickname) return sendError(res, 400, 'Nickname is required');
    try {
      contactManager.deleteContact(nickname);
      sendJson(res, 200, { message: `Contact "${nickname}" deleted` });
    } catch (err) {
      sendError(res, 404, err.message);
    }
  },

  'POST /api/encrypt': async (req, res) => {
    const { message, recipient, senderKeyName, senderPassword, outputPath } = await parseBody(req);
    if (!message) return sendError(res, 400, 'Message is required');
    if (!recipient) return sendError(res, 400, 'Recipient is required');
    try {
      const result = encryptMessage(message, recipient, senderKeyName || null, senderPassword || null, outputPath || null);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/decrypt': async (req, res) => {
    const { inputPath, keyName, password, senderKeyName } = await parseBody(req);
    if (!inputPath) return sendError(res, 400, 'Encrypted file path is required');
    if (!keyName) return sendError(res, 400, 'Key pair name is required');
    if (!password) return sendError(res, 400, 'Password is required');
    try {
      const result = decryptMessage(inputPath, keyName, password, senderKeyName || null);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/sign': async (req, res) => {
    const { message, keyName, password, outputPath } = await parseBody(req);
    if (!message) return sendError(res, 400, 'Message is required');
    if (!keyName) return sendError(res, 400, 'Key pair name is required');
    if (!password) return sendError(res, 400, 'Password is required');
    try {
      const result = signatureModule.signMessage(message, keyName, password, outputPath || undefined);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/verify': async (req, res) => {
    const { message, signature, publicKeyPath, signedFilePath } = await parseBody(req);
    try {
      if (signedFilePath && publicKeyPath) {
        const result = signatureModule.verifySignatureFromFile(signedFilePath, publicKeyPath);
        sendJson(res, 200, result);
      } else if (message && signature && publicKeyPath) {
        const isValid = signatureModule.verifySignature(message, signature, publicKeyPath);
        sendJson(res, 200, { valid: isValid });
      } else {
        sendError(res, 400, 'Provide either signedFilePath + publicKeyPath, or message + signature + publicKeyPath');
      }
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'POST /api/shred': async (req, res) => {
    const { filePath } = await parseBody(req);
    if (!filePath) return sendError(res, 400, 'File path is required');
    try {
      const result = shredFile(filePath);
      sendJson(res, 200, result);
    } catch (err) {
      sendError(res, 400, err.message);
    }
  },

  'GET /api/status': async (req, res) => {
    let dbReady = false;
    try {
      const db = getDb();
      db.prepare('SELECT 1').get();
      db.close();
      dbReady = true;
    } catch {}
    const keys = dbReady ? keyManager.listKeyPairs() : [];
    const contacts = dbReady ? contactManager.listContacts() : [];
    sendJson(res, 200, { dbReady, keyCount: keys.length, contactCount: contacts.length });
  },
};

function matchRoute(method, pathname) {
  const exactKey = `${method} ${pathname}`;
  if (API_ROUTES[exactKey]) {
    return { handler: API_ROUTES[exactKey], params: {} };
  }

  for (const routePattern of Object.keys(API_ROUTES)) {
    const [routeMethod, routePath] = routePattern.split(' ');
    if (routeMethod !== method) continue;

    const routeParts = routePath.split('/');
    const pathParts = pathname.split('/');
    if (routeParts.length !== pathParts.length) continue;

    const params = {};
    let match = true;
    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i].startsWith(':')) {
        params[routeParts[i].slice(1)] = pathParts[i];
      } else if (routeParts[i] !== pathParts[i]) {
        match = false;
        break;
      }
    }
    if (match) {
      return { handler: API_ROUTES[routePattern], params };
    }
  }
  return null;
}

function createServer(port = 3000) {
  initDb();

  const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    req.pathname = parsedUrl.pathname;
    req.query = parsedUrl.query;
    req.params = {};

    if (req.pathname.startsWith('/api/')) {
      const matched = matchRoute(req.method, req.pathname);
      if (matched) {
        req.params = matched.params;
        try {
          await matched.handler(req, res);
        } catch (err) {
          sendError(res, 500, err.message);
        }
      } else {
        sendError(res, 404, 'API endpoint not found');
      }
    } else {
      serveStatic(req, res);
    }
  });

  server.listen(port, () => {
    console.log(`\n  🔐 CryptoVault running at http://localhost:${port}\n`);
  });

  return server;
}

module.exports = { createServer };
