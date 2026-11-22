function createCourseModel(db) {
    return {
        findActiveById(courseId) {
            return db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [courseId]);
        },

        // One row per (course, enrollment) with the student and the enrollment's first payment.
        // Courses without enrollments appear once with NULL enrollment columns.
        listWithEnrollmentsAndPayments() {
            return db.all(`
                SELECT c.id AS course_id,
                       c.title AS course_title,
                       e.id AS enrollment_id,
                       u.name AS student_name,
                       p.amount AS payment_amount,
                       p.status AS payment_status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.id = (
                    SELECT MIN(first_payment.id) FROM payments first_payment
                    WHERE first_payment.enrollment_id = e.id
                )
                ORDER BY c.id, e.id`);
        },
    };
}

module.exports = { createCourseModel };
