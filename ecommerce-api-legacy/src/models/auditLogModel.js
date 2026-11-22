const { run } = require('../database/connection');

module.exports = function createAuditLogModel(db) {
    return {
        record(action) {
            return run(db,
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
        },
    };
};
