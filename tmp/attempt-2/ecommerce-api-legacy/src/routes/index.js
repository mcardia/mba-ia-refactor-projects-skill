const express = require('express');
const { createCheckoutRoutes } = require('./checkoutRoutes');
const { createAdminRoutes } = require('./adminRoutes');
const { createUserRoutes } = require('./userRoutes');

function createRoutes({ controllers, requireAdmin }) {
    const router = express.Router();
    router.use(createCheckoutRoutes({ checkoutController: controllers.checkout }));
    router.use(createAdminRoutes({ adminController: controllers.admin, requireAdmin }));
    router.use(createUserRoutes({ userController: controllers.user, requireAdmin }));
    return router;
}

module.exports = { createRoutes };
