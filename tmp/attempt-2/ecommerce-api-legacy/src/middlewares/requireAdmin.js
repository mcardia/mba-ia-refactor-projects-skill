const crypto = require('crypto');
const HttpError = require('../utils/httpError');
const { MESSAGES } = require('../config/constants');

// Guards admin/destructive routes with the X-Admin-Token header. No token configured => disabled.
function createRequireAdmin({ adminToken }) {
    return (req, res, next) => {
        if (!adminToken) return next(new HttpError(403, MESSAGES.ADMIN_DISABLED));
        const supplied = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(adminToken);
        if (supplied.length !== expected.length || !crypto.timingSafeEqual(supplied, expected)) {
            return next(new HttpError(401, MESSAGES.ADMIN_TOKEN_REQUIRED));
        }
        next();
    };
}

module.exports = { createRequireAdmin };
