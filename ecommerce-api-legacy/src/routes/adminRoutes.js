const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function createAdminRoutes({ adminController, requireAdmin }) {
    const router = express.Router();
    router.get('/api/admin/financial-report', requireAdmin, asyncHandler(adminController.financialReport));
    return router;
};
