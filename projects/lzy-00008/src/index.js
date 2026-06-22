#!/usr/bin/env node

const { createServer } = require('./server');

const port = parseInt(process.env.PORT, 10) || 3000;
createServer(port);
