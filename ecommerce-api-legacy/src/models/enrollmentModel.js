const { run } = require('../database/connection');

module.exports = function createEnrollmentModel(db) {
    return {
        async create(userId, courseId) {
            const { lastID } = await run(db,
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
            return lastID;
        },

        deleteByUserId(userId) {
            return run(db, 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
        },
    };
};
