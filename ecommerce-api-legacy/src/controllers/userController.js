// DELETE /api/users/:id
const HttpError = require('../utils/httpError');

// Success text kept verbatim from the original API for client compatibility.
const DELETE_SUCCESS_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

module.exports = function createUserController({ userService }) {
    return {
        async remove(req, res) {
            const userId = Number(req.params.id);
            if (!Number.isInteger(userId) || userId <= 0) throw new HttpError(400, 'Bad Request');
            await userService.deleteUser(userId);
            res.send(DELETE_SUCCESS_MESSAGE);
        },
    };
};
