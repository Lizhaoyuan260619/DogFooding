const crypto = require('crypto');
const fs = require('fs');
const { decryptStoredPrivateKey, getPublicKeyPem } = require('./keys');
const { getContact } = require('./contacts');

function decryptMessage(inputPath, keyName, password, senderKeyName) {
  if (!inputPath) throw new Error('Encrypted file path is required');
  if (!keyName) throw new Error('Decryption key pair name is required');
  if (!password) throw new Error('Password is required to decrypt the private key');

  let encoded;
  try {
    encoded = fs.readFileSync(inputPath, 'utf8');
  } catch {
    throw new Error(`Cannot read encrypted file: ${inputPath}`);
  }

  let payload;
  try {
    payload = JSON.parse(Buffer.from(encoded, 'base64').toString('utf8'));
  } catch {
    throw new Error('Invalid encrypted file format: unable to parse Base64 JSON payload');
  }

  const { encrypted_message, encrypted_aes_key, iv, signature, sender_fingerprint } = payload;
  if (!encrypted_message || !encrypted_aes_key || !iv) {
    throw new Error('Encrypted file is missing required fields (encrypted_message, encrypted_aes_key, iv)');
  }

  let privateKeyPem;
  try {
    privateKeyPem = decryptStoredPrivateKey(keyName, password);
  } catch (err) {
    throw new Error(`Failed to decrypt private key: ${err.message}`);
  }

  let aesKey;
  try {
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    aesKey = crypto.privateDecrypt(
      { key: privateKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' },
      Buffer.from(encrypted_aes_key, 'base64')
    );
  } catch {
    throw new Error('Key mismatch: the provided private key cannot decrypt this message');
  }

  let decryptedMessage;
  try {
    const decipher = crypto.createDecipheriv('aes-256-cbc', aesKey, Buffer.from(iv, 'base64'));
    const decBuf1 = decipher.update(Buffer.from(encrypted_message, 'base64'));
    const decBuf2 = decipher.final();
    decryptedMessage = Buffer.concat([decBuf1, decBuf2]).toString('utf8');
  } catch {
    throw new Error('Decryption failed: corrupted data or key mismatch');
  }

  let signatureValid = null;
  let signatureStatus = 'not provided';
  if (signature && sender_fingerprint) {
    signatureStatus = 'provided';
    try {
      let senderPublicKeyPem;
      if (senderKeyName) {
        senderPublicKeyPem = getPublicKeyPem(senderKeyName);
      } else {
        const keypairs = require('./db').getDb();
        try {
          const row = keypairs.prepare('SELECT public_key_pem FROM keypairs WHERE fingerprint = ?').get(sender_fingerprint);
          if (row) {
            senderPublicKeyPem = row.public_key_pem;
          }
        } finally {
          keypairs.close();
        }
      }

      if (senderPublicKeyPem) {
        const senderPublicKey = crypto.createPublicKey(senderPublicKeyPem);
        const verifier = crypto.createVerify('sha256');
        verifier.update(decryptedMessage);
        verifier.end();
        signatureValid = verifier.verify(senderPublicKey, Buffer.from(signature, 'base64'));
        signatureStatus = signatureValid ? 'valid' : 'invalid';
      } else {
        signatureStatus = 'sender public key not found';
      }
    } catch (err) {
      signatureStatus = `verification failed: ${err.message}`;
    }
  }

  return { message: decryptedMessage, signatureValid, signatureStatus, senderFingerprint: sender_fingerprint || null };
}

module.exports = { decryptMessage };
