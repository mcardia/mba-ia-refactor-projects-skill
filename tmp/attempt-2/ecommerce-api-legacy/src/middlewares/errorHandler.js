const http = require('http');
const HttpError = require('../utils/httpError');
const { MESSAGES } = require('../config/constants');

// Single place that turns errors into the JSON envelope { error: <message> }.
function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (res.headersSent) return next(err);

        if (err instanceof HttpError) {
            return res.status(err.status).json({ error: err.message });
        }

        // Errors raised by express.json() (malformed JSON, payload too large) carry a 4xx status.
        const status = err.status || err.statusCode;
        if (status >= 400 && status < 500) {
            const message = status === 400 ? MESSAGES.BAD_REQUEST : http.STATUS_CODES[status];
            return res.status(status).json({ error: message });
        }

        logger.error(`Erro não tratado em ${req.method} ${req.path}`, err);
        return res.status(500).json({ error: MESSAGES.INTERNAL_ERROR });
    };
}

module.exports = { createErrorHandler };
