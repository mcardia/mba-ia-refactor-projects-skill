// Domain/HTTP error carrying the status code the error handler must answer with.
class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.name = 'HttpError';
        this.status = status;
    }
}

module.exports = HttpError;
