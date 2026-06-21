const fs = require('fs');
const { getDb } = require('./db');

function addContact(nickname, publicKeyPath) {
  if (!nickname) throw new Error('Nickname is required');
  if (!publicKeyPath) throw new Error('Public key file path is required');

  const resolvedPath = require('path').resolve(publicKeyPath);
  if (!fs.existsSync(resolvedPath)) throw new Error(`Public key file not found: ${resolvedPath}`);

  const pemContent = fs.readFileSync(resolvedPath, 'utf8');
  try {
    require('crypto').createPublicKey(pemContent);
  } catch {
    throw new Error('Invalid public key file');
  }

  const db = getDb();
  try {
    db.prepare('INSERT INTO contacts (nickname, public_key_path) VALUES (?, ?)').run(nickname, resolvedPath);
  } catch (err) {
    if (err.message.includes('UNIQUE constraint')) {
      throw new Error(`Contact "${nickname}" already exists`);
    }
    throw err;
  } finally {
    db.close();
  }

  return { nickname, publicKeyPath: resolvedPath };
}

function listContacts() {
  const db = getDb();
  try {
    return db.prepare('SELECT id, nickname, public_key_path, created_at FROM contacts ORDER BY created_at DESC').all();
  } finally {
    db.close();
  }
}

function getContact(nickname) {
  const db = getDb();
  try {
    const row = db.prepare('SELECT * FROM contacts WHERE nickname = ?').get(nickname);
    if (!row) throw new Error(`Contact "${nickname}" not found`);
    return row;
  } finally {
    db.close();
  }
}

function updateContact(nickname, newNickname, newPublicKeyPath) {
  const db = getDb();
  try {
    const contact = db.prepare('SELECT * FROM contacts WHERE nickname = ?').get(nickname);
    if (!contact) throw new Error(`Contact "${nickname}" not found`);

    const updates = [];
    const values = [];

    if (newNickname) {
      updates.push('nickname = ?');
      values.push(newNickname);
    }
    if (newPublicKeyPath) {
      const resolvedPath = require('path').resolve(newPublicKeyPath);
      if (!fs.existsSync(resolvedPath)) throw new Error(`Public key file not found: ${resolvedPath}`);
      updates.push('public_key_path = ?');
      values.push(resolvedPath);
    }

    if (updates.length === 0) throw new Error('No updates specified');

    values.push(nickname);
    db.prepare(`UPDATE contacts SET ${updates.join(', ')} WHERE nickname = ?`).run(...values);
  } finally {
    db.close();
  }

  return getContact(newNickname || nickname);
}

function deleteContact(nickname) {
  const db = getDb();
  try {
    const result = db.prepare('DELETE FROM contacts WHERE nickname = ?').run(nickname);
    if (result.changes === 0) throw new Error(`Contact "${nickname}" not found`);
  } finally {
    db.close();
  }
}

module.exports = { addContact, listContacts, getContact, updateContact, deleteContact };
