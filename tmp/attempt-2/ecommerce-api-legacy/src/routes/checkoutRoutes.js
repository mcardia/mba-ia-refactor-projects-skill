const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function createCheckoutRoutes({ checkoutController }) {
    const router = express.Router();
    router.post('/api/checkout', asyncHandler(checkoutController.create));
    return router;
}

module.exports = { createCheckoutRoutes };
