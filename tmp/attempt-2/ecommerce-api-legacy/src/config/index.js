// Every runtime setting comes from the environment. Defaults are development-safe and never secrets.
const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    host: process.env.HOST || undefined, // undefined => all interfaces (original behavior)
    databasePath: process.env.DATABASE_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    adminToken: process.env.ADMIN_TOKEN || '', // empty => admin endpoints disabled (403)
    logLevel: process.env.LOG_LEVEL || 'info',
});

module.exports = config;
