const { run } = require('../database/connection');

module.exports = function createPaymentModel(db) {
    return {
        async create(enrollmentId, amount, status) {
            const { lastID } = await run(db,
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status]);
            return lastID;
        },

        deleteByUserId(userId) {
            return run(db,
                'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                [userId]);
        },
    };
};
