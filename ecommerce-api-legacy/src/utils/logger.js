// Minimal leveled logger. Never pass secrets, passwords or full card numbers to it.
const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const threshold = LEVELS[config.logLevel] ?? LEVELS.info;

function write(level, message, meta) {
    if (LEVELS[level] > threshold) return;
    const line = `${new Date().toISOString()} [${level.toUpperCase()}] ${message}`;
    const output = level === 'error' || level === 'warn' ? console.error : console.log;
    if (meta === undefined) output(line);
    else output(line, meta);
}

module.exports = {
    error: (message, meta) => write('error', message, meta),
    warn: (message, meta) => write('warn', message, meta),
    info: (message, meta) => write('info', message, meta),
    debug: (message, meta) => write('debug', message, meta),
};
