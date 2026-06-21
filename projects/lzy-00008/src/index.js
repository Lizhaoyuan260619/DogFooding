#!/usr/bin/env node

const { Command } = require('commander');
const readline = require('readline');
const { initDb } = require('./db');
const keyManager = require('./keys');
const contactManager = require('./contacts');
const { encryptMessage } = require('./encrypt');
const { decryptMessage } = require('./decrypt');
const signatureModule = require('./sign');
const { shredFile } = require('./shred');

const program = new Command();

program
  .name('crypto-cli')
  .description('Lightweight CLI encrypted communication tool')
  .version('1.0.0');

function promptPassword(prompt) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(prompt, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

function promptPasswordHidden(prompt) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const stdin = process.openStdin();

    process.stdout.write(prompt);

    let password = '';
    const onData = (char) => {
      const c = char.toString();
      switch (c) {
        case '\n':
        case '\r':
        case '\u0004':
          stdin.removeListener('data', onData);
          rl.close();
          process.stdout.write('\n');
          resolve(password);
          break;
        case '\u0003':
          process.exit();
          break;
        case '\u007F':
          password = password.slice(0, -1);
          break;
        default:
          password += c;
          break;
      }
    };

    stdin.on('data', onData);
  });
}

program
  .command('init')
  .description('Initialize the database')
  .action(() => {
    try {
      const dbPath = initDb();
      console.log(`Database initialized at: ${dbPath}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

const keysCmd = program.command('keys').description('Key pair management');

keysCmd
  .command('generate')
  .description('Generate a new RSA-2048 key pair')
  .requiredOption('-n, --name <name>', 'Key pair name')
  .action(async (opts) => {
    try {
      const password = await promptPasswordHidden('Enter password to encrypt private key: ');
      if (!password) {
        console.error('Error: Password cannot be empty');
        return;
      }
      const confirm = await promptPasswordHidden('Confirm password: ');
      if (password !== confirm) {
        console.error('Error: Passwords do not match');
        return;
      }
      const result = keyManager.generateKeyPair(opts.name, password);
      console.log(`Key pair generated successfully.`);
      console.log(`  Name: ${result.name}`);
      console.log(`  Fingerprint: ${result.fingerprint}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

keysCmd
  .command('list')
  .description('List all key pairs')
  .action(() => {
    try {
      const keys = keyManager.listKeyPairs();
      if (keys.length === 0) {
        console.log('No key pairs found.');
        return;
      }
      console.log('Key Pairs:');
      console.log('-'.repeat(80));
      for (const key of keys) {
        console.log(`  ID:          ${key.id}`);
        console.log(`  Name:        ${key.name}`);
        console.log(`  Fingerprint: ${key.fingerprint}`);
        console.log(`  Created:     ${key.created_at}`);
        console.log('-'.repeat(80));
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

keysCmd
  .command('export-pub')
  .description('Export public key to a PEM file')
  .requiredOption('-n, --name <name>', 'Key pair name')
  .requiredOption('-o, --output <path>', 'Output file path')
  .action((opts) => {
    try {
      const result = keyManager.exportPublicKey(opts.name, opts.output);
      console.log(`Public key exported to: ${result.outputPath}`);
      console.log(`Fingerprint: ${result.fingerprint}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

keysCmd
  .command('export-priv')
  .description('Export private key to a PEM file (requires password)')
  .requiredOption('-n, --name <name>', 'Key pair name')
  .requiredOption('-o, --output <path>', 'Output file path')
  .action(async (opts) => {
    try {
      const password = await promptPasswordHidden('Enter password to decrypt private key: ');
      const result = keyManager.exportPrivateKey(opts.name, opts.output, password);
      console.log(`Private key exported to: ${result.outputPath}`);
      console.log(`Fingerprint: ${result.fingerprint}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

keysCmd
  .command('import')
  .description('Import a key pair from PEM files')
  .requiredOption('-n, --name <name>', 'Key pair name')
  .requiredOption('--pubkey <path>', 'Public key PEM file path')
  .requiredOption('--privkey <path>', 'Private key PEM file path')
  .action(async (opts) => {
    try {
      const password = await promptPasswordHidden('Enter password to encrypt the private key: ');
      if (!password) {
        console.error('Error: Password cannot be empty');
        return;
      }
      const result = keyManager.importKeyPair(opts.name, opts.pubkey, opts.privkey, password);
      console.log(`Key pair imported successfully.`);
      console.log(`  Name: ${result.name}`);
      console.log(`  Fingerprint: ${result.fingerprint}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

keysCmd
  .command('delete')
  .description('Delete a key pair')
  .requiredOption('-n, --name <name>', 'Key pair name')
  .action((opts) => {
    try {
      keyManager.deleteKeyPair(opts.name);
      console.log(`Key pair "${opts.name}" deleted successfully.`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

const contactsCmd = program.command('contacts').description('Contact management');

contactsCmd
  .command('add')
  .description('Add a new contact')
  .requiredOption('-n, --nickname <nickname>', 'Contact nickname')
  .requiredOption('-k, --pubkey <path>', 'Public key file path')
  .action((opts) => {
    try {
      const result = contactManager.addContact(opts.nickname, opts.pubkey);
      console.log(`Contact added successfully.`);
      console.log(`  Nickname: ${result.nickname}`);
      console.log(`  Public Key: ${result.publicKeyPath}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

contactsCmd
  .command('list')
  .description('List all contacts')
  .action(() => {
    try {
      const contacts = contactManager.listContacts();
      if (contacts.length === 0) {
        console.log('No contacts found.');
        return;
      }
      console.log('Contacts:');
      console.log('-'.repeat(80));
      for (const c of contacts) {
        console.log(`  ID:          ${c.id}`);
        console.log(`  Nickname:    ${c.nickname}`);
        console.log(`  Public Key:  ${c.public_key_path}`);
        console.log(`  Created:     ${c.created_at}`);
        console.log('-'.repeat(80));
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

contactsCmd
  .command('update')
  .description('Update a contact')
  .requiredOption('-n, --nickname <nickname>', 'Current contact nickname')
  .option('--new-nickname <name>', 'New nickname')
  .option('--new-pubkey <path>', 'New public key file path')
  .action((opts) => {
    try {
      if (!opts.newNickname && !opts.newPubkey) {
        console.error('Error: At least one of --new-nickname or --new-pubkey is required');
        return;
      }
      const result = contactManager.updateContact(opts.nickname, opts.newNickname, opts.newPubkey);
      console.log(`Contact updated successfully.`);
      console.log(`  Nickname: ${result.nickname}`);
      console.log(`  Public Key: ${result.public_key_path}`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

contactsCmd
  .command('delete')
  .description('Delete a contact')
  .requiredOption('-n, --nickname <nickname>', 'Contact nickname')
  .action((opts) => {
    try {
      contactManager.deleteContact(opts.nickname);
      console.log(`Contact "${opts.nickname}" deleted successfully.`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

program
  .command('encrypt')
  .description('Encrypt a message')
  .requiredOption('-m, --message <text>', 'Message to encrypt')
  .requiredOption('-r, --recipient <name_or_path>', 'Recipient nickname or public key file path')
  .option('-s, --sender <name>', 'Sender key pair name (for signing)')
  .option('-o, --output <path>', 'Output encrypted file path')
  .action(async (opts) => {
    try {
      let senderPassword = null;
      if (opts.sender) {
        senderPassword = await promptPasswordHidden('Enter sender private key password: ');
      }
      const result = encryptMessage(
        opts.message,
        opts.recipient,
        opts.sender || null,
        senderPassword,
        opts.output || null
      );
      console.log(`Message encrypted successfully.`);
      console.log(`  Output: ${result.outputPath}`);
      if (result.senderFingerprint) {
        console.log(`  Signed by fingerprint: ${result.senderFingerprint}`);
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

program
  .command('decrypt')
  .description('Decrypt a message')
  .requiredOption('-i, --input <path>', 'Encrypted file path')
  .requiredOption('-k, --key <name>', 'Decryption key pair name')
  .option('-s, --sender <name>', 'Sender key pair name (for signature verification)')
  .action(async (opts) => {
    try {
      const password = await promptPasswordHidden('Enter private key password: ');
      const result = decryptMessage(opts.input, opts.key, password, opts.sender || null);
      console.log('\n=== Decrypted Message ===');
      console.log(result.message);
      console.log('=========================\n');
      if (result.signatureStatus !== 'not provided') {
        console.log(`Signature Status: ${result.signatureStatus}`);
        if (result.senderFingerprint) {
          console.log(`Sender Fingerprint: ${result.senderFingerprint}`);
        }
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

program
  .command('sign')
  .description('Sign a message')
  .requiredOption('-m, --message <text>', 'Message to sign')
  .requiredOption('-k, --key <name>', 'Signer key pair name')
  .option('-o, --output <path>', 'Output signed file path')
  .action(async (opts) => {
    try {
      const password = await promptPasswordHidden('Enter private key password: ');
      const result = signatureModule.signMessage(opts.message, opts.key, password, opts.output);
      console.log(`Message signed successfully.`);
      console.log(`  Algorithm: ${result.algorithm}`);
      console.log(`  Signer Fingerprint: ${result.signer_fingerprint}`);
      console.log(`  Signature: ${result.signature}`);
      if (opts.output) {
        console.log(`  Output: ${opts.output}`);
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

program
  .command('verify')
  .description('Verify a message signature')
  .option('-m, --message <text>', 'Original message text')
  .option('-s, --signature <base64>', 'Base64-encoded signature')
  .option('-k, --pubkey <path>', "Signer's public key file path")
  .option('-f, --file <path>', 'Signed file path (alternative to -m and -s)')
  .action((opts) => {
    try {
      if (opts.file) {
        if (!opts.pubkey) {
          console.error('Error: --pubkey is required for file verification');
          return;
        }
        const result = signatureModule.verifySignatureFromFile(opts.file, opts.pubkey);
        console.log(`Signature Verification: ${result.valid ? 'VALID ✓' : 'INVALID ✗'}`);
        if (result.signerFingerprint) console.log(`Signer Fingerprint: ${result.signerFingerprint}`);
        if (result.timestamp) console.log(`Signed At: ${result.timestamp}`);
        console.log(`Message: ${result.message}`);
      } else if (opts.message && opts.signature && opts.pubkey) {
        const isValid = signatureModule.verifySignature(opts.message, opts.signature, opts.pubkey);
        console.log(`Signature Verification: ${isValid ? 'VALID ✓' : 'INVALID ✗'}`);
      } else {
        console.error('Error: Provide either --file and --pubkey, or --message, --signature, and --pubkey');
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

program
  .command('shred')
  .description('Securely delete a file (3-pass random overwrite)')
  .requiredOption('-f, --file <path>', 'File to shred')
  .action((opts) => {
    try {
      const result = shredFile(opts.file);
      console.log(`File securely deleted.`);
      console.log(`  Path: ${result.filePath}`);
      console.log(`  Passes: ${result.passes}`);
      console.log(`  Original Size: ${result.size} bytes`);
    } catch (err) {
      console.error(`Error: ${err.message}`);
    }
  });

program.parse();
