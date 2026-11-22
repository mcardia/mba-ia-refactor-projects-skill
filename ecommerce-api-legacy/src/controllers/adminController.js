// GET /api/admin/financial-report
module.exports = function createAdminController({ financialReportService }) {
    return {
        async financialReport(req, res) {
            res.json(await financialReportService.build());
        },
    };
};
