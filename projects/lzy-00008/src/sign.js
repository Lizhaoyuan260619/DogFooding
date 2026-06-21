const crypto = require('crypto');
const fs = require('fs');
const { decryptStoredPrivateKey, getPublicKeyPem } = require('./keys');

function signMessage(message, keyName, password, outputPath) {
  if (!message) throw new Error('Message content is required');
  if (!keyName) throw new Error('Key pair name is required');
  if (!password) throw new Error('Password is required');

  const privateKeyPem = decryptStoredPrivateKey(keyName, password);
  const privateKey = crypto.createPrivateKey(privateKeyPem);

  const sign = crypto.createSign('sha256');
  sign.update(message);
  sign.end();
  const signature = sign.sign(privateKey).toString('base64');

  const publicKeyPem = getPublicKeyPem(keyName);
  const fingerprint = crypto.createHash('sha256').update(publicKeyPem).digest('hex');

  const result = {
    message,
    signature,
    signer_fingerprint: fingerprint,
    algorithm: 'RSA-SHA256',
    timestamp: new Date().toISOString()
  };

  if (outputPath) {
    fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf8');
  }

  return result;
}

function verifySignature(message, signature, publicKeyPath) {
  if (!message) throw new Error('Message content is required');
  if (!signature) throw new Error('Signature is required');
  if (!publicKeyPath) throw new Error('Signer public key file path is required');

  let publicKeyPem;
  try {
    publicKeyPem = fs.readFileSync(publicKeyPath, 'utf8');
  } catch {
    throw new Error(`Cannot read public key file: ${publicKeyPath}`);
  }

  let publicKey;
  try {
    publicKey = crypto.createPublicKey(publicKeyPem);
  } catch {
    throw new Error('Invalid public key file');
  }

  const verifier = crypto.createVerify('sha256');
  verifier.update(message);
  verifier.end();

  let signatureBuffer;
  try {
    signatureBuffer = Buffer.from(signature, 'base64');
  } catch {
    throw new Error('Invalid signature format');
  }

  const isValid = verifier.verify(publicKey, signatureBuffer);
  return isValid;
}

function verifySignatureFromFile(signedFilePath, publicKeyPath) {
  if (!signedFilePath) throw new Error('Signed file path is required');
  if (!publicKeyPath) throw new Error('Signer public key file path is required');

  let content;
  try {
    content = fs.readFileSync(signedFilePath, 'utf8');
  } catch {
    throw new Error(`Cannot read signed file: ${signedFilePath}`);
  }

  let signedData;
  try {
    signedData = JSON.parse(content);
  } catch {
    throw new Error('Invalid signed file format');
  }

  if (!signedData.message || !signedData.signature) {
    throw new Error('Signed file is missing required fields (message, signature)');
  }

  const isValid = verifySignature(signedData.message, signedData.signature, publicKeyPath);
  return {
    valid: isValid,
    message: signedData.message,
    signerFingerprint: signedData.signer_fingerprint || null,
    algorithm: signedData.algorithm || null,
    timestamp: signedData.timestamp || null
  };
}

module.exports = { signMessage, verifySignature, verifySignatureFromFile };
