const { parseUserId } = require('./validators');
const { MESSAGES } = require('../config/constants');

function createUserController({ userService }) {
    return {
        async remove(req, res) {
            const userId = parseUserId(req.params.id);
            await userService.deleteUser(userId);
            res.send(MESSAGES.USER_DELETED);
        },
    };
}

module.exports = { createUserController };
