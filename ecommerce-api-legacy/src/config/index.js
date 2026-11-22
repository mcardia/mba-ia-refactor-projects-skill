// Application settings, read from the environment. No secret has a real default value.
module.exports = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    databasePath: process.env.DATABASE_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    // Empty => admin endpoints are disabled (403).
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});
