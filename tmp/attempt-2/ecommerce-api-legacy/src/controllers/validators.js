const HttpError = require('../utils/httpError');
const { CARD_NUMBER_PATTERN, EMAIL_PATTERN, MESSAGES } = require('../config/constants');

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function parsePositiveInteger(value) {
    if (typeof value === 'number' && Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) > 0) return Number(value);
    return null;
}

// Maps the public request fields (usr, eml, pwd, c_id, card) to descriptive names.
function parseCheckoutPayload(body) {
    const { usr, eml, pwd, c_id: rawCourseId, card } = body || {};
    const courseId = parsePositiveInteger(rawCourseId);

    const valid = isNonEmptyString(usr)
        && isNonEmptyString(eml) && EMAIL_PATTERN.test(eml)
        && courseId !== null
        && typeof card === 'string' && CARD_NUMBER_PATTERN.test(card)
        && (pwd === undefined || pwd === null || isNonEmptyString(pwd));
    if (!valid) throw new HttpError(400, MESSAGES.BAD_REQUEST);

    return { name: usr.trim(), email: eml.trim(), password: pwd || null, courseId, cardNumber: card };
}

function parseUserId(rawId) {
    const userId = parsePositiveInteger(rawId);
    if (userId === null) throw new HttpError(400, MESSAGES.BAD_REQUEST);
    return userId;
}

module.exports = { parseCheckoutPayload, parseUserId };
