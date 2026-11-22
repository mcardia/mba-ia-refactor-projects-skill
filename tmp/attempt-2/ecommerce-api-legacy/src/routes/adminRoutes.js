const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function createAdminRoutes({ adminController, requireAdmin }) {
    const router = express.Router();
    router.get('/api/admin/financial-report', requireAdmin, asyncHandler(adminController.financialReport));
    return router;
}

module.exports = { createAdminRoutes };
