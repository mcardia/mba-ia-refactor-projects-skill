const { run, get } = require('../database/connection');
const { hashPassword } = require('../utils/password');

module.exports = function createUserModel(db) {
    return {
        findById(id) {
            return get(db, 'SELECT id, name, email FROM users WHERE id = ?', [id]);
        },

        findByEmail(email) {
            return get(db, 'SELECT id, name, email FROM users WHERE email = ?', [email]);
        },

        async create({ name, email, password }) {
            const { lastID } = await run(db,
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, hashPassword(password)]);
            return { id: lastID, name, email };
        },

        async deleteById(id) {
            const { changes } = await run(db, 'DELETE FROM users WHERE id = ?', [id]);
            return changes;
        },
    };
};
