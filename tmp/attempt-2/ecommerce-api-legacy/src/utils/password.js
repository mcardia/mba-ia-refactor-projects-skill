const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;

// Salted scrypt hash stored as "<salt hex>:<hash hex>".
async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const derived = await scrypt(password, salt, KEY_LENGTH);
    return `${salt.toString('hex')}:${derived.toString('hex')}`;
}

module.exports = { hashPassword };
