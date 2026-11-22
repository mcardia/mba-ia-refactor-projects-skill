// Business constants shared by every layer.
const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Simulated gateway rule: cards whose number starts with this prefix are approved.
const APPROVED_CARD_PREFIX = '4';

const MAX_CARD_DIGITS = 19;
const MAX_TEXT_LENGTH = 255;

// Label used in the financial report when an enrollment has no matching user.
const UNKNOWN_STUDENT = 'Unknown';

module.exports = {
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIX,
    MAX_CARD_DIGITS,
    MAX_TEXT_LENGTH,
    UNKNOWN_STUDENT,
};
