function createAdminController({ reportService }) {
    return {
        async financialReport(req, res) {
            res.json(await reportService.financialReport());
        },
    };
}

module.exports = { createAdminController };
