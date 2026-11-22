// User removal with its dependent rows, atomically.
const HttpError = require('../utils/httpError');

module.exports = function createUserService({ userModel, enrollmentModel, paymentModel, inTransaction }) {
    return {
        async deleteUser(userId) {
            await inTransaction(async () => {
                const user = await userModel.findById(userId);
                if (!user) throw new HttpError(404, 'Usuário não encontrado');
                await paymentModel.deleteByUserId(userId);
                await enrollmentModel.deleteByUserId(userId);
                await userModel.deleteById(userId);
            });
        },
    };
};
