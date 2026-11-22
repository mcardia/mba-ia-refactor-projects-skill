const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

// Simulated payment gateway. The API key is held here and never logged.
function createPaymentGateway({ apiKey, logger }) {
    return {
        async charge({ cardNumber, amount }) {
            logger.info(`Processando pagamento de ${amount} no cartão final ${cardNumber.slice(-4)}`);
            if (!apiKey) logger.debug('PAYMENT_GATEWAY_KEY não configurada (gateway simulado)');
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentGateway };
