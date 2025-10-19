import sqlite3 from 'sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DB_PATH = path.join(__dirname, '..', 'data', 'qview.db');

class Database {
  constructor() {
    this.db = null;
  }

  init() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
          console.error('Error opening database:', err);
          reject(err);
        } else {
          console.log('Connected to SQLite database');
          this.createTables().then(resolve).catch(reject);
        }
      });
    });
  }

  createTables() {
    return new Promise((resolve, reject) => {
      const fabricatorsTable = `
        CREATE TABLE IF NOT EXISTS fabricators (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          devicePort TEXT UNIQUE,
          hwid TEXT,
          status TEXT DEFAULT 'offline',
          position INTEGER,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `;

      const jobsTable = `
        CREATE TABLE IF NOT EXISTS jobs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          fabricator_id INTEGER,
          status TEXT DEFAULT 'inqueue',
          file_name_original TEXT,
          file_name TEXT,
          file_blob BLOB,
          favorite INTEGER DEFAULT 0,
          td_id INTEGER,
          filament TEXT,
          issue_id INTEGER,
          comments TEXT,
          time_start DATETIME,
          time_end DATETIME,
          time_elapsed INTEGER,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (fabricator_id) REFERENCES fabricators (id)
        )
      `;

      const issuesTable = `
        CREATE TABLE IF NOT EXISTS issues (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          description TEXT,
          category TEXT DEFAULT 'printer',
          severity TEXT,
          fabricator_id INTEGER,
          job_id INTEGER,
          status TEXT DEFAULT 'open',
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          resolved_at DATETIME,
          FOREIGN KEY (fabricator_id) REFERENCES fabricators (id),
          FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
      `;

      this.db.serialize(() => {
        this.db.run(fabricatorsTable, (err) => {
          if (err) {
            console.error('Error creating fabricators table:', err);
            reject(err);
            return;
          }
        });

        this.db.run(jobsTable, (err) => {
          if (err) {
            console.error('Error creating jobs table:', err);
            reject(err);
            return;
          }
        });

        this.db.run(issuesTable, (err) => {
          if (err) {
            console.error('Error creating issues table:', err);
            reject(err);
            return;
          }
          resolve();
        });
      });
    });
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function (err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id: this.lastID, changes: this.changes });
        }
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) {
          reject(err);
        } else {
          resolve(row);
        }
      });
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }

  close() {
    return new Promise((resolve, reject) => {
      if (this.db) {
        this.db.close((err) => {
          if (err) {
            reject(err);
          } else {
            console.log('Database connection closed');
            resolve();
          }
        });
      } else {
        resolve();
      }
    });
  }
}

// Export a singleton instance
const database = new Database();
export default database;
