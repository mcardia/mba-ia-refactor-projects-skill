// Minimal leveled logger. Never pass secrets, passwords or full card numbers to it.
const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const write = (name, stream) => (message, ...details) => {
        if (LEVELS[name] < threshold) return;
        stream(`${new Date().toISOString()} [${name.toUpperCase()}] ${message}`, ...details);
    };

    return {
        debug: write('debug', console.log),
        info: write('info', console.log),
        warn: write('warn', console.error),
        error: write('error', console.error),
    };
}

module.exports = { createLogger };
