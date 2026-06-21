const fs = require('fs');
const crypto = require('crypto');

function shredFile(filePath) {
  if (!filePath) throw new Error('File path is required');

  const resolvedPath = require('path').resolve(filePath);
  if (!fs.existsSync(resolvedPath)) throw new Error(`File not found: ${resolvedPath}`);

  const stat = fs.statSync(resolvedPath);
  if (stat.isDirectory()) throw new Error('Cannot shred a directory');

  const fileSize = stat.size;
  const passes = 3;

  for (let pass = 0; pass < passes; pass++) {
    const randomData = crypto.randomBytes(fileSize);
    const fd = fs.openSync(resolvedPath, 'r+');
    try {
      fs.writeSync(fd, randomData, 0, fileSize, 0);
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
  }

  fs.unlinkSync(resolvedPath);

  return { filePath: resolvedPath, passes, size: fileSize };
}

module.exports = { shredFile };
