// Guard for privileged routes: requires the X-Admin-Token header to match ADMIN_TOKEN.
const crypto = require('crypto');
const HttpError = require('../utils/httpError');

module.exports = function createRequireAdmin({ adminToken }) {
    return (req, res, next) => {
        if (!adminToken) return next(new HttpError(403, 'Endpoint desabilitado'));
        const supplied = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(adminToken);
        if (supplied.length !== expected.length || !crypto.timingSafeEqual(supplied, expected)) {
            return next(new HttpError(401, 'Token de administrador obrigatório'));
        }
        return next();
    };
};
