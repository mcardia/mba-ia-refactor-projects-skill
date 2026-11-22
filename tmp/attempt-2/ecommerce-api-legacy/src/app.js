// Composition root: load config, open the database, wire layers, start the HTTP server.
const express = require('express');
const config = require('./config');
const { createLogger } = require('./utils/logger');
const { createDatabase } = require('./database/connection');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createAdminController } = require('./controllers/adminController');
const { createUserController } = require('./controllers/userController');
const { createRequireAdmin } = require('./middlewares/requireAdmin');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { createRoutes } = require('./routes');

function createApp({ db, logger }) {
    const models = {
        userModel: createUserModel(db),
        courseModel: createCourseModel(db),
        enrollmentModel: createEnrollmentModel(db),
        paymentModel: createPaymentModel(db),
        auditLogModel: createAuditLogModel(db),
    };
    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    const services = {
        checkout: createCheckoutService({ db, ...models, paymentGateway }),
        report: createReportService(models),
        user: createUserService({ db, ...models }),
    };
    const controllers = {
        checkout: createCheckoutController({ checkoutService: services.checkout }),
        admin: createAdminController({ reportService: services.report }),
        user: createUserController({ userService: services.user }),
    };

    const app = express();
    app.use(express.json());
    app.use(createRoutes({ controllers, requireAdmin: createRequireAdmin(config) }));
    app.use(createErrorHandler({ logger }));
    return app;
}

const logger = createLogger(config.logLevel);

async function main() {
    const db = await createDatabase(config.databasePath);
    const app = createApp({ db, logger });

    const listenArgs = config.host ? [config.port, config.host] : [config.port];
    app.listen(...listenArgs, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', err);
    process.exit(1);
});
