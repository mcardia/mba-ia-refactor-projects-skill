// Simulated payment gateway. The key comes from configuration and is never logged.
const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

module.exports = function createPaymentGateway({ apiKey, logger }) {
    return {
        charge(cardNumber, amount) {
            logger.info('Processando pagamento', {
                cardLast4: cardNumber.slice(-4),
                amount,
                gatewayConfigured: Boolean(apiKey),
            });
            return cardNumber.startsWith(APPROVED_CARD_PREFIX)
                ? PAYMENT_STATUS.PAID
                : PAYMENT_STATUS.DENIED;
        },
    };
};
