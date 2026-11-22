// Checkout use case: find course, charge card, create user if needed, enroll, record payment.
const HttpError = require('../utils/httpError');
const { PAYMENT_STATUS } = require('../config/constants');

module.exports = function createCheckoutService({
    userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
    paymentGateway, inTransaction, logger,
}) {
    return {
        async checkout({ name, email, password, courseId, cardNumber }) {
            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new HttpError(404, 'Curso não encontrado');

            const existingUser = await userModel.findByEmail(email);
            if (!existingUser && !password) throw new HttpError(400, 'Bad Request');

            const status = paymentGateway.charge(cardNumber, course.price);
            if (status === PAYMENT_STATUS.DENIED) throw new HttpError(400, 'Pagamento recusado');

            const enrollmentId = await inTransaction(async () => {
                const user = existingUser || await userModel.create({ name, email, password });
                const newEnrollmentId = await enrollmentModel.create(user.id, course.id);
                await paymentModel.create(newEnrollmentId, course.price, status);
                await auditLogModel.record(`Checkout curso ${course.id} por ${user.id}`);
                return newEnrollmentId;
            });

            logger.info('Checkout concluído', { courseId: course.id, enrollmentId });
            return { enrollmentId };
        },
    };
};
