import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert';
import sqlite3 from 'sqlite3';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test database class
class TestDatabase {
  constructor(dbPath) {
    this.db = null;
    this.dbPath = dbPath;
  }

  init() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) {
          reject(err);
        } else {
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
          model TEXT,
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
          if (err) reject(err);
        });

        this.db.run(jobsTable, (err) => {
          if (err) reject(err);
        });

        this.db.run(issuesTable, (err) => {
          if (err) {
            reject(err);
          } else {
            resolve();
          }
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
            // Ignore 'Database is closed' errors
            if (err.code === 'SQLITE_MISUSE' && err.message.includes('closed')) {
              this.db = null;
              resolve();
            } else {
              reject(err);
            }
          } else {
            this.db = null;
            resolve();
          }
        });
      } else {
        resolve();
      }
    });
  }
}

describe('Database', () => {
  let db;
  const testDbPath = path.join(__dirname, 'test.db');

  before(async () => {
    // Clean up any existing test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  beforeEach(async () => {
    // Close any existing database connection
    if (db) {
      await db.close();
    }

    // Wait a bit for file handles to be released
    await new Promise(resolve => setTimeout(resolve, 50));

    // Create fresh database for each test
    if (fs.existsSync(testDbPath)) {
      try {
        fs.unlinkSync(testDbPath);
      } catch (err) {
        // If file is still locked, wait and try again
        await new Promise(resolve => setTimeout(resolve, 100));
        fs.unlinkSync(testDbPath);
      }
    }
    db = new TestDatabase(testDbPath);
    await db.init();
  });

  after(async () => {
    // Clean up test database
    if (db) {
      await db.close();
    }
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('Initialization', () => {
    it('should initialize database successfully', async () => {
      assert.ok(db.db, 'Database should be initialized');
    });

    it('should create fabricators table', async () => {
      const result = await db.get(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='fabricators'"
      );
      assert.ok(result, 'Fabricators table should exist');
      assert.strictEqual(result.name, 'fabricators');
    });

    it('should create jobs table', async () => {
      const result = await db.get(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
      );
      assert.ok(result, 'Jobs table should exist');
      assert.strictEqual(result.name, 'jobs');
    });

    it('should create issues table', async () => {
      const result = await db.get(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='issues'"
      );
      assert.ok(result, 'Issues table should exist');
      assert.strictEqual(result.name, 'issues');
    });
  });

  describe('CRUD Operations - Fabricators', () => {
    it('should insert a fabricator', async () => {
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1, 'ready']
      );

      assert.ok(result.id, 'Should return inserted ID');
      assert.strictEqual(result.id, 1);
    });

    it('should retrieve a fabricator by id', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [1]);
      assert.ok(fabricator, 'Should retrieve fabricator');
      assert.strictEqual(fabricator.name, 'Test Printer');
      assert.strictEqual(fabricator.devicePort, '/dev/ttyUSB0');
      assert.strictEqual(fabricator.status, 'offline');
    });

    it('should retrieve all fabricators', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1]
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 2', '/dev/ttyUSB1', 2]
      );

      const fabricators = await db.all('SELECT * FROM fabricators ORDER BY position ASC');
      assert.strictEqual(fabricators.length, 2);
      assert.strictEqual(fabricators[0].name, 'Printer 1');
      assert.strictEqual(fabricators[1].name, 'Printer 2');
    });

    it('should update a fabricator', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['printing', 1]);

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [1]);
      assert.strictEqual(fabricator.status, 'printing');
    });

    it('should delete a fabricator', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      await db.run('DELETE FROM fabricators WHERE id = ?', [1]);

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [1]);
      assert.strictEqual(fabricator, undefined);
    });

    it('should enforce unique devicePort constraint', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1]
      );

      await assert.rejects(
        async () => {
          await db.run(
            'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
            ['Printer 2', '/dev/ttyUSB0', 2]
          );
        },
        { message: /UNIQUE constraint failed/ }
      );
    });
  });

  describe('CRUD Operations - Jobs', () => {
    let fabricatorId;

    beforeEach(async () => {
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );
      fabricatorId = result.id;
    });

    it('should insert a job', async () => {
      const result = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      assert.ok(result.id, 'Should return inserted ID');
      assert.strictEqual(result.id, 1);
    });

    it('should retrieve a job by id', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.ok(job, 'Should retrieve job');
      assert.strictEqual(job.name, 'Test Job');
      assert.strictEqual(job.status, 'inqueue');
      assert.strictEqual(job.favorite, 0);
    });

    it('should retrieve jobs by fabricator_id', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Job 1', fabricatorId, 'inqueue', 'test1.gcode']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Job 2', fabricatorId, 'printing', 'test2.gcode']
      );

      const jobs = await db.all(
        'SELECT * FROM jobs WHERE fabricator_id = ? ORDER BY id ASC',
        [fabricatorId]
      );
      assert.strictEqual(jobs.length, 2);
      assert.strictEqual(jobs[0].name, 'Job 1');
      assert.strictEqual(jobs[1].name, 'Job 2');
    });

    it('should update job status', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['printing', 1]);

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.status, 'printing');
    });

    it('should delete a job', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      await db.run('DELETE FROM jobs WHERE id = ?', [1]);

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job, undefined);
    });

    it('should store and retrieve blob data', async () => {
      const testData = Buffer.from('Test GCode Data');
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob) VALUES (?, ?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode', testData]
      );

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.ok(Buffer.isBuffer(job.file_blob), 'file_blob should be a Buffer');
      assert.strictEqual(job.file_blob.toString(), 'Test GCode Data');
    });

    it('should filter jobs by favorite status', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, favorite) VALUES (?, ?, ?, ?)',
        ['Favorite Job', fabricatorId, 'complete', 1]
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, favorite) VALUES (?, ?, ?, ?)',
        ['Regular Job', fabricatorId, 'complete', 0]
      );

      const favorites = await db.all('SELECT * FROM jobs WHERE favorite = 1');
      assert.strictEqual(favorites.length, 1);
      assert.strictEqual(favorites[0].name, 'Favorite Job');
    });
  });

  describe('Database Connections', () => {
    it('should close database connection', async () => {
      await db.close();
      // If close doesn't throw, it succeeded
      assert.ok(true, 'Database closed successfully');
    });

    it('should handle closing when already closed', async () => {
      const freshDb = new TestDatabase(path.join(__dirname, 'test-close.db'));
      await freshDb.init();
      await freshDb.close();
      await freshDb.close(); // Second close should not throw
      assert.ok(true, 'Closing closed database succeeded');

      // Clean up
      const testPath = path.join(__dirname, 'test-close.db');
      if (fs.existsSync(testPath)) {
        await new Promise(resolve => setTimeout(resolve, 50));
        fs.unlinkSync(testPath);
      }
    });
  });

  describe('Foreign Key Relationships', () => {
    it('should allow null fabricator_id for jobs', async () => {
      const result = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Unassigned Job', null, 'inqueue']
      );

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [result.id]);
      assert.strictEqual(job.fabricator_id, null);
    });

    it('should retrieve jobs with fabricator information', async () => {
      const fabricatorResult = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorResult.id, 'inqueue']
      );

      const result = await db.get(
        `SELECT jobs.*, fabricators.name as fabricator_name
         FROM jobs
         JOIN fabricators ON jobs.fabricator_id = fabricators.id
         WHERE jobs.id = ?`,
        [1]
      );

      assert.strictEqual(result.name, 'Test Job');
      assert.strictEqual(result.fabricator_name, 'Test Printer');
    });
  });
});
