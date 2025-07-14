import dotenv from 'dotenv';

dotenv.config();

import {Pool} from 'pg';

const pool = new Pool(process.env.DATABASE_URL ? {connectionString: process.env.DATABASE_URL} : {
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT || '5432', 10),
});


/**
 * Generic query function for PostgreSQL database.
 * @param {string} text
 * @param {any[]} [params]
 * @return {Promise<any[]>}
 */
async function query(text, params= []) {
    const start = Date.now();
    const res = await pool.query(text, params).then(qr => qr);
    const duration = Date.now() - start;
    if (params) for (let i = 0; i < params.length; i++) text = text.replace("$".concat(String(i + 1)), params[i]);
    console.log('executed query', {text, duration, rows: res.rowCount});
    return res.rows;
}
export default {
    pool,
    query
};