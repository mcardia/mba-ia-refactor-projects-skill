// Composition root: load config, open the database, wire layers, start the server.
const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { createDatabase, createTransactionRunner } = require('./database/connection');

const createUserModel = require('./models/userModel');
const createCourseModel = require('./models/courseModel');
const createEnrollmentModel = require('./models/enrollmentModel');
const createPaymentModel = require('./models/paymentModel');
const createAuditLogModel = require('./models/auditLogModel');

const createPaymentGateway = require('./services/paymentGateway');
const createCheckoutService = require('./services/checkoutService');
const createFinancialReportService = require('./services/financialReportService');
const createUserService = require('./services/userService');

const createCheckoutController = require('./controllers/checkoutController');
const createAdminController = require('./controllers/adminController');
const createUserController = require('./controllers/userController');

const createCheckoutRoutes = require('./routes/checkoutRoutes');
const createAdminRoutes = require('./routes/adminRoutes');
const createUserRoutes = require('./routes/userRoutes');

const createRequireAdmin = require('./middlewares/requireAdmin');
const createErrorHandler = require('./middlewares/errorHandler');

async function main() {
    const db = await createDatabase(config);
    const inTransaction = createTransactionRunner(db);

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);

    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });
    const checkoutService = createCheckoutService({
        userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
        paymentGateway, inTransaction, logger,
    });
    const financialReportService = createFinancialReportService({ courseModel });
    const userService = createUserService({ userModel, enrollmentModel, paymentModel, inTransaction });

    const requireAdmin = createRequireAdmin({ adminToken: config.adminToken });

    const app = express();
    app.use(express.json());
    app.use(createCheckoutRoutes({ checkoutController: createCheckoutController({ checkoutService }) }));
    app.use(createAdminRoutes({
        adminController: createAdminController({ financialReportService }), requireAdmin,
    }));
    app.use(createUserRoutes({ userController: createUserController({ userService }), requireAdmin }));
    app.use(createErrorHandler({ logger }));

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas desabilitadas');

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', { message: err.message });
    process.exit(1);
});
