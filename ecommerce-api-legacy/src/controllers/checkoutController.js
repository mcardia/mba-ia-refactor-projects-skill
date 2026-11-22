// POST /api/checkout: maps the public request fields, validates them, delegates to the service.
const HttpError = require('../utils/httpError');
const { MAX_CARD_DIGITS, MAX_TEXT_LENGTH } = require('../config/constants');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const BAD_REQUEST = 'Bad Request';

function isNonEmptyText(value) {
    return typeof value === 'string' && value.trim() !== '' && value.length <= MAX_TEXT_LENGTH;
}

function parseCheckoutPayload(body) {
    const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card: cardNumber } = body || {};

    if (!name || !email || !rawCourseId || !cardNumber) throw new HttpError(400, BAD_REQUEST);
    if (!isNonEmptyText(name) || !isNonEmptyText(email) || !EMAIL_PATTERN.test(email)) {
        throw new HttpError(400, BAD_REQUEST);
    }
    if (password !== undefined && password !== null && !isNonEmptyText(password)) {
        throw new HttpError(400, BAD_REQUEST);
    }

    const courseId = Number(rawCourseId);
    if (!Number.isInteger(courseId) || courseId <= 0) throw new HttpError(400, BAD_REQUEST);

    const cardPattern = new RegExp(`^\\d{1,${MAX_CARD_DIGITS}}$`);
    if (typeof cardNumber !== 'string' || !cardPattern.test(cardNumber)) {
        throw new HttpError(400, BAD_REQUEST);
    }

    return { name, email, password: password || null, courseId, cardNumber };
}

module.exports = function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const input = parseCheckoutPayload(req.body);
            const { enrollmentId } = await checkoutService.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
};
