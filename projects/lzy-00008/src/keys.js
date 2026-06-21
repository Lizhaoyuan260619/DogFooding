const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { getDb, DB_DIR } = require('./db');

function generateKeyPair(name, password) {
  if (!name) throw new Error('Key pair name is required');
  if (!password) throw new Error('Password is required to encrypt the private key');

  const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding: { type: 'spki', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
  });

  const fingerprint = crypto.createHash('sha256').update(publicKey).digest('hex');

  const cipher = crypto.createCipheriv(
    'aes-256-cbc',
    crypto.scryptSync(password, 'salt', 32),
    Buffer.alloc(16, 0)
  );
  const encryptedPrivateKey = cipher.update(privateKey, 'utf8', 'base64') + cipher.final('base64');

  const db = getDb();
  try {
    db.prepare(
      'INSERT INTO keypairs (name, public_key_pem, encrypted_private_key_pem, fingerprint) VALUES (?, ?, ?, ?)'
    ).run(name, publicKey, encryptedPrivateKey, fingerprint);
  } finally {
    db.close();
  }

  return { name, fingerprint };
}

function listKeyPairs() {
  const db = getDb();
  try {
    return db.prepare('SELECT id, name, fingerprint, created_at FROM keypairs ORDER BY created_at DESC').all();
  } finally {
    db.close();
  }
}

function exportPublicKey(name, outputPath) {
  const db = getDb();
  try {
    const row = db.prepare('SELECT public_key_pem, fingerprint FROM keypairs WHERE name = ?').get(name);
    if (!row) throw new Error(`Key pair "${name}" not found`);
    fs.writeFileSync(outputPath, row.public_key_pem, 'utf8');
    return { outputPath, fingerprint: row.fingerprint };
  } finally {
    db.close();
  }
}

function exportPrivateKey(name, outputPath, password) {
  const db = getDb();
  try {
    const row = db.prepare('SELECT encrypted_private_key_pem, fingerprint FROM keypairs WHERE name = ?').get(name);
    if (!row) throw new Error(`Key pair "${name}" not found`);

    const decipher = crypto.createDecipheriv(
      'aes-256-cbc',
      crypto.scryptSync(password, 'salt', 32),
      Buffer.alloc(16, 0)
    );
    const privateKey = decipher.update(row.encrypted_private_key_pem, 'base64', 'utf8') + decipher.final('utf8');
    fs.writeFileSync(outputPath, privateKey, 'utf8');
    return { outputPath, fingerprint: row.fingerprint };
  } finally {
    db.close();
  }
}

function importKeyPair(name, publicKeyPath, privateKeyPath, password) {
  if (!name) throw new Error('Key pair name is required');

  const publicKeyPem = fs.readFileSync(publicKeyPath, 'utf8');
  const privateKeyPem = fs.readFileSync(privateKeyPath, 'utf8');

  try {
    crypto.createPublicKey(publicKeyPem);
  } catch {
    throw new Error('Invalid public key file');
  }
  try {
    crypto.createPrivateKey(privateKeyPem);
  } catch {
    throw new Error('Invalid private key file');
  }

  const fingerprint = crypto.createHash('sha256').update(publicKeyPem).digest('hex');

  const cipher = crypto.createCipheriv(
    'aes-256-cbc',
    crypto.scryptSync(password, 'salt', 32),
    Buffer.alloc(16, 0)
  );
  const encryptedPrivateKey = cipher.update(privateKeyPem, 'utf8', 'base64') + cipher.final('base64');

  const db = getDb();
  try {
    const existing = db.prepare('SELECT id FROM keypairs WHERE fingerprint = ?').get(fingerprint);
    if (existing) throw new Error('A key pair with the same fingerprint already exists');
    db.prepare(
      'INSERT INTO keypairs (name, public_key_pem, encrypted_private_key_pem, fingerprint) VALUES (?, ?, ?, ?)'
    ).run(name, publicKeyPem, encryptedPrivateKey, fingerprint);
  } finally {
    db.close();
  }

  return { name, fingerprint };
}

function getPublicKeyPem(name) {
  const db = getDb();
  try {
    const row = db.prepare('SELECT public_key_pem FROM keypairs WHERE name = ?').get(name);
    if (!row) throw new Error(`Key pair "${name}" not found`);
    return row.public_key_pem;
  } finally {
    db.close();
  }
}

function decryptStoredPrivateKey(name, password) {
  const db = getDb();
  try {
    const row = db.prepare('SELECT encrypted_private_key_pem FROM keypairs WHERE name = ?').get(name);
    if (!row) throw new Error(`Key pair "${name}" not found`);
    const decipher = crypto.createDecipheriv(
      'aes-256-cbc',
      crypto.scryptSync(password, 'salt', 32),
      Buffer.alloc(16, 0)
    );
    return decipher.update(row.encrypted_private_key_pem, 'base64', 'utf8') + decipher.final('utf8');
  } finally {
    db.close();
  }
}

function deleteKeyPair(name) {
  const db = getDb();
  try {
    const result = db.prepare('DELETE FROM keypairs WHERE name = ?').run(name);
    if (result.changes === 0) throw new Error(`Key pair "${name}" not found`);
  } finally {
    db.close();
  }
}

module.exports = {
  generateKeyPair,
  listKeyPairs,
  exportPublicKey,
  exportPrivateKey,
  importKeyPair,
  getPublicKeyPem,
  decryptStoredPrivateKey,
  deleteKeyPair
};
