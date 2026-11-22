// Database connection, schema, seed data and promise-based query helpers.
const sqlite3 = require('sqlite3');
const { PAYMENT_STATUS } = require('../config/constants');
const { hashPassword } = require('../utils/password');

const SCHEMA = [
    'PRAGMA foreign_keys = ON',
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)',
    'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id)
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT
    )`,
    'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
];

function open(path) {
    return new Promise((resolve, reject) => {
        const db = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(db)));
    });
}

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onDone(err) {
            if (err) reject(err);
            else resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

// A single connection is shared, so transactions are serialized through a queue.
function createTransactionRunner(db) {
    let queue = Promise.resolve();
    return function inTransaction(work) {
        const result = queue.then(async () => {
            await run(db, 'BEGIN');
            try {
                const value = await work();
                await run(db, 'COMMIT');
                return value;
            } catch (err) {
                await run(db, 'ROLLBACK');
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };
}

async function seed(db) {
    const existing = await get(db, 'SELECT COUNT(*) AS total FROM users');
    if (existing.total > 0) return;

    await run(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]);
    await run(db, 'INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
        ['Clean Architecture', 997.0, 'Docker', 497.0]);
    await run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await run(db, 'INSERT INTO payments (enrollment_id, amount, status) VALUES (1, ?, ?)',
        [997.0, PAYMENT_STATUS.PAID]);
}

async function createDatabase(config) {
    const db = await open(config.databasePath);
    for (const statement of SCHEMA) {
        await run(db, statement);
    }
    await seed(db);
    return db;
}

module.exports = { createDatabase, createTransactionRunner, run, get, all };
