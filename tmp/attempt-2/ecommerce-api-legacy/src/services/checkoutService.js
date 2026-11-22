const HttpError = require('../utils/httpError');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS, MESSAGES } = require('../config/constants');

function createCheckoutService({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway }) {
    return {
        // Finds or creates the student, charges the card and records enrollment + payment + audit atomically.
        async checkout({ name, email, password, courseId, cardNumber }) {
            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new HttpError(404, MESSAGES.COURSE_NOT_FOUND);

            const existingUser = await userModel.findByEmail(email);
            if (!existingUser && !password) throw new HttpError(400, MESSAGES.BAD_REQUEST);
            const passwordHash = existingUser ? null : await hashPassword(password);

            const status = await paymentGateway.charge({ cardNumber, amount: course.price });
            if (status !== PAYMENT_STATUS.PAID) throw new HttpError(400, MESSAGES.PAYMENT_DENIED);

            return db.transaction(async () => {
                // Re-read inside the transaction so concurrent checkouts cannot duplicate the user.
                const user = await userModel.findByEmail(email);
                let userId = user && user.id;
                if (!userId) {
                    if (!passwordHash) throw new HttpError(400, MESSAGES.BAD_REQUEST);
                    userId = await userModel.create({ name, email, passwordHash });
                }

                const enrollmentId = await enrollmentModel.create(userId, course.id);
                await paymentModel.create(enrollmentId, course.price, status);
                await auditLogModel.record(`Checkout curso ${course.id} por ${userId}`);
                return { enrollmentId };
            });
        },
    };
}

module.exports = { createCheckoutService };
