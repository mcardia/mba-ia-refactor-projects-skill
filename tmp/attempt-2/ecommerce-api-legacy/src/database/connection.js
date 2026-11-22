const sqlite3 = require('sqlite3');
const { PAYMENT_STATUS } = require('../config/constants');
const { hashPassword } = require('../utils/password');

const SCHEMA = [
    'PRAGMA foreign_keys = ON',
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)',
    'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    'CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), course_id INTEGER REFERENCES courses(id))',
    'CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER REFERENCES enrollments(id), amount REAL, status TEXT)',
    'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
];

function openDatabase(filename) {
    return new Promise((resolve, reject) => {
        const handle = new sqlite3.Database(filename, (err) => (err ? reject(err) : resolve(handle)));
    });
}

// Promise-based wrapper around one sqlite3 connection, plus serialized transactions.
function createClient(handle) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        handle.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        handle.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        handle.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    // A single connection can hold one transaction at a time, so transactions are queued.
    let queue = Promise.resolve();
    const transaction = (work) => {
        const result = queue.then(async () => {
            await run('BEGIN');
            try {
                const output = await work();
                await run('COMMIT');
                return output;
            } catch (err) {
                await run('ROLLBACK');
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };

    const close = () => new Promise((resolve, reject) => {
        handle.close((err) => (err ? reject(err) : resolve()));
    });

    return { run, get, all, transaction, close };
}

async function initializeSchema(db) {
    for (const statement of SCHEMA) {
        await db.run(statement);
    }
}

async function seedDatabase(db) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return;

    const seedPasswordHash = await hashPassword('123');
    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', seedPasswordHash]);
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)', ['Clean Architecture', 997.0, 'Docker', 497.0]);
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [1, 997.0, PAYMENT_STATUS.PAID]);
    });
}

async function createDatabase(filename) {
    const db = createClient(await openDatabase(filename));
    await initializeSchema(db);
    await seedDatabase(db);
    return db;
}

module.exports = { createDatabase };
