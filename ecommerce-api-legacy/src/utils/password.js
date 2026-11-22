// Salted scrypt password hashing (Node standard library).
const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const hash = crypto.scryptSync(password, salt, KEY_LENGTH);
    return `${salt.toString('hex')}:${hash.toString('hex')}`;
}

module.exports = { hashPassword };
