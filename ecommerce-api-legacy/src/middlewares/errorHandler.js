// Centralized error handler: one JSON envelope, no internal details leaked to clients.
module.exports = function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        // Malformed JSON bodies from express.json() arrive as 400 errors with type 'entity.parse.failed'.
        const status = err.status || err.statusCode || 500;
        if (status >= 500) {
            logger.error('Erro não tratado', { message: err.message, stack: err.stack });
            return res.status(500).json({ error: 'Erro interno' });
        }
        const message = err.type === 'entity.parse.failed' ? 'Bad Request' : err.message;
        return res.status(status).json({ error: message });
    };
};
