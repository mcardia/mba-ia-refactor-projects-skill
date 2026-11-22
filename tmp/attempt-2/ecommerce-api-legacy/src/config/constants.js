const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Simulated gateway rule: cards whose number starts with this prefix are approved.
const APPROVED_CARD_PREFIX = '4';

const CARD_NUMBER_PATTERN = /^\d{12,19}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const MESSAGES = Object.freeze({
    BAD_REQUEST: 'Bad Request',
    COURSE_NOT_FOUND: 'Curso não encontrado',
    PAYMENT_DENIED: 'Pagamento recusado',
    USER_DELETED: 'Usuário deletado.',
    INTERNAL_ERROR: 'Erro interno do servidor',
    ADMIN_DISABLED: 'Endpoint administrativo desabilitado',
    ADMIN_TOKEN_REQUIRED: 'Token de administrador obrigatório',
});

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, CARD_NUMBER_PATTERN, EMAIL_PATTERN, MESSAGES };
