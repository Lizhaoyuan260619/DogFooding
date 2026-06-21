const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { getDb } = require('./db');
const { getPublicKeyPem, decryptStoredPrivateKey } = require('./keys');
const { getContact } = require('./contacts');

function resolveRecipientPublicKey(recipient) {
  let recipientPem;
  if (fs.existsSync(path.resolve(recipient))) {
    recipientPem = fs.readFileSync(path.resolve(recipient), 'utf8');
  } else {
    const contact = getContact(recipient);
    recipientPem = fs.readFileSync(contact.public_key_path, 'utf8');
  }
  try {
    crypto.createPublicKey(recipientPem);
  } catch {
    throw new Error('Invalid recipient public key');
  }
  return recipientPem;
}

function encryptMessage(message, recipient, senderKeyName, senderPassword, outputPath) {
  if (!message && !readMessageFromStdin) throw new Error('Message content is required');
  if (!recipient) throw new Error('Recipient (nickname or public key file path) is required');

  const recipientPem = resolveRecipientPublicKey(recipient);
  const recipientPublicKey = crypto.createPublicKey(recipientPem);

  const aesKey = crypto.randomBytes(32);
  const iv = crypto.randomBytes(16);

  const cipher = crypto.createCipheriv('aes-256-cbc', aesKey, iv);
  const encryptedMessage = Buffer.concat([cipher.update(message, 'utf8'), cipher.final()]);

  const encryptedAesKey = crypto.publicEncrypt(
    { key: recipientPublicKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' },
    aesKey
  );

  let signature = null;
  let senderFingerprint = null;
  if (senderKeyName && senderPassword) {
    const senderPrivateKeyPem = decryptStoredPrivateKey(senderKeyName, senderPassword);
    const senderPrivateKey = crypto.createPrivateKey(senderPrivateKeyPem);
    const sign = crypto.createSign('sha256');
    sign.update(message);
    sign.end();
    signature = sign.sign(senderPrivateKey).toString('base64');
    const senderPublicKeyPem = getPublicKeyPem(senderKeyName);
    senderFingerprint = crypto.createHash('sha256').update(senderPublicKeyPem).digest('hex');
  }

  const payload = {
    encrypted_message: encryptedMessage.toString('base64'),
    encrypted_aes_key: encryptedAesKey.toString('base64'),
    iv: iv.toString('base64'),
    signature,
    sender_fingerprint: senderFingerprint,
    timestamp: new Date().toISOString()
  };

  const encoded = Buffer.from(JSON.stringify(payload)).toString('base64');

  const finalOutputPath = outputPath || `encrypted_${Date.now()}.enc`;
  fs.writeFileSync(finalOutputPath, encoded, 'utf8');

  const db = getDb();
  try {
    db.prepare(
      'INSERT INTO messages (sender_key_name, recipient_contact_nickname, encrypted_file_path) VALUES (?, ?, ?)'
    ).run(senderKeyName || null, recipient, path.resolve(finalOutputPath));
  } finally {
    db.close();
  }

  return { outputPath: finalOutputPath, senderFingerprint };
}

module.exports = { encryptMessage, resolveRecipientPublicKey };
