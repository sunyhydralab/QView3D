import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert';
import zlib from 'zlib';
import sqlite3 from 'sqlite3';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Mock database for testing
class MockDatabase {
  constructor(dbPath) {
    this.db = null;
    this.dbPath = dbPath;
  }

  async init() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) reject(err);
        else this.createTables().then(resolve).catch(reject);
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
          status TEXT DEFAULT 'offline',
          position INTEGER
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
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (fabricator_id) REFERENCES fabricators (id)
        )
      `;

      this.db.serialize(() => {
        this.db.run(fabricatorsTable, (err) => {
          if (err) reject(err);
        });
        this.db.run(jobsTable, (err) => {
          if (err) reject(err);
          else resolve();
        });
      });
    });
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function (err) {
        if (err) reject(err);
        else resolve({ id: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
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

describe('Job Operations', () => {
  let db;
  const testDbPath = path.join(__dirname, 'jobs-test.db');
  let fabricatorId;

  before(async () => {
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

    if (fs.existsSync(testDbPath)) {
      try {
        fs.unlinkSync(testDbPath);
      } catch (err) {
        // If file is still locked, wait and try again
        await new Promise(resolve => setTimeout(resolve, 100));
        fs.unlinkSync(testDbPath);
      }
    }
    db = new MockDatabase(testDbPath);
    await db.init();

    // Create a test fabricator
    const result = await db.run(
      'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
      ['Test Printer', '/dev/ttyUSB0', 1, 'ready']
    );
    fabricatorId = result.id;
  });

  after(async () => {
    if (db) {
      await db.close();
    }
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('Job CRUD Operations', () => {
    it('should create a new job', async () => {
      const result = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      assert.ok(result.id);
      assert.strictEqual(result.id, 1);
    });

    it('should retrieve a job by id', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.name, 'Test Job');
      assert.strictEqual(job.fabricator_id, fabricatorId);
      assert.strictEqual(job.status, 'inqueue');
    });

    it('should update job status', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue']
      );

      await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['printing', 1]);

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.status, 'printing');
    });

    it('should delete a job', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue']
      );

      const result = await db.run('DELETE FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(result.changes, 1);

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job, undefined);
    });

    it('should cancel a job', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue']
      );

      await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['cancelled', 1]);

      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.status, 'cancelled');
    });
  });

  describe('Job Queue Operations', () => {
    it('should retrieve jobs for a specific fabricator', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 1', fabricatorId, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 2', fabricatorId, 'inqueue']
      );

      const jobs = await db.all(
        'SELECT * FROM jobs WHERE fabricator_id = ? AND status = ? ORDER BY id ASC',
        [fabricatorId, 'inqueue']
      );

      assert.strictEqual(jobs.length, 2);
      assert.strictEqual(jobs[0].name, 'Job 1');
      assert.strictEqual(jobs[1].name, 'Job 2');
    });

    it('should count jobs in queue', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 1', fabricatorId, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 2', fabricatorId, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 3', fabricatorId, 'complete']
      );

      const result = await db.get(
        'SELECT COUNT(*) as count FROM jobs WHERE fabricator_id = ? AND status = ?',
        [fabricatorId, 'inqueue']
      );

      assert.strictEqual(result.count, 2);
    });

    it('should find fabricator with smallest queue', async () => {
      // Create second fabricator
      const result2 = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 2', '/dev/ttyUSB1', 2]
      );

      // Add jobs to first fabricator
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 1', fabricatorId, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 2', fabricatorId, 'inqueue']
      );

      // Add one job to second fabricator
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 3', result2.id, 'inqueue']
      );

      // Find fabricator with smallest queue
      const fabricators = await db.all(`
        SELECT f.id, COUNT(j.id) as job_count
        FROM fabricators f
        LEFT JOIN jobs j ON f.id = j.fabricator_id AND j.status = 'inqueue'
        GROUP BY f.id
        ORDER BY job_count ASC
        LIMIT 1
      `);

      assert.strictEqual(fabricators[0].id, result2.id);
      assert.strictEqual(fabricators[0].job_count, 1);
    });

    it('should cancel multiple jobs from queue', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 1', fabricatorId, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 2', fabricatorId, 'inqueue']
      );

      const jobIds = [1, 2];
      for (const jobId of jobIds) {
        await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['cancelled', jobId]);
      }

      const jobs = await db.all(
        'SELECT * FROM jobs WHERE fabricator_id = ? AND status = ?',
        [fabricatorId, 'cancelled']
      );

      assert.strictEqual(jobs.length, 2);
    });
  });

  describe('File Compression and Decompression', () => {
    it('should compress file data with gzip', () => {
      const originalData = 'G28\nG1 X10 Y10\nG1 Z5\nM104 S200';
      const compressed = zlib.gzipSync(Buffer.from(originalData));

      assert.ok(Buffer.isBuffer(compressed));
      assert.ok(compressed.length > 0);
      // Compressed data should typically be smaller for repetitive text
      assert.ok(compressed.length < originalData.length * 2);
    });

    it('should decompress gzipped file data', () => {
      const originalData = 'G28\nG1 X10 Y10\nG1 Z5\nM104 S200';
      const compressed = zlib.gzipSync(Buffer.from(originalData));
      const decompressed = zlib.gunzipSync(compressed).toString('utf-8');

      assert.strictEqual(decompressed, originalData);
    });

    it('should store and retrieve compressed file data', async () => {
      const gcodeData = 'G28\nG1 X10 Y10\nG1 Z5\nM104 S200';
      const compressed = zlib.gzipSync(Buffer.from(gcodeData));

      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob) VALUES (?, ?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode', compressed]
      );

      const job = await db.get('SELECT file_blob FROM jobs WHERE id = ?', [1]);
      const decompressed = zlib.gunzipSync(job.file_blob).toString('utf-8');

      assert.strictEqual(decompressed, gcodeData);
    });

    it('should handle large file compression', () => {
      // Create a large gcode file (10000 lines)
      const lines = [];
      for (let i = 0; i < 10000; i++) {
        lines.push(`G1 X${i} Y${i} Z${i % 100}`);
      }
      const largeData = lines.join('\n');

      const compressed = zlib.gzipSync(Buffer.from(largeData));
      const decompressed = zlib.gunzipSync(compressed).toString('utf-8');

      assert.strictEqual(decompressed, largeData);
      // Compression should be effective on repetitive data
      assert.ok(compressed.length < largeData.length / 2);
    });
  });

  describe('Job Search and Filtering', () => {
    beforeEach(async () => {
      // Create multiple test jobs
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, favorite, created_at) VALUES (?, ?, ?, ?, ?)',
        ['Calibration Cube', fabricatorId, 'complete', 1, '2024-01-01 10:00:00']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, favorite, created_at) VALUES (?, ?, ?, ?, ?)',
        ['Benchy', fabricatorId, 'complete', 0, '2024-01-02 11:00:00']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, favorite, created_at) VALUES (?, ?, ?, ?, ?)',
        ['Test Print', fabricatorId, 'inqueue', 1, '2024-01-03 12:00:00']
      );
    });

    it('should search jobs by name', async () => {
      const jobs = await db.all(
        'SELECT * FROM jobs WHERE name LIKE ?',
        ['%Cube%']
      );

      assert.strictEqual(jobs.length, 1);
      assert.strictEqual(jobs[0].name, 'Calibration Cube');
    });

    it('should filter jobs by favorite status', async () => {
      const jobs = await db.all('SELECT * FROM jobs WHERE favorite = 1');

      assert.strictEqual(jobs.length, 2);
      assert.ok(jobs.every(job => job.favorite === 1));
    });

    it('should filter jobs by date range', async () => {
      const jobs = await db.all(
        'SELECT * FROM jobs WHERE created_at >= ? AND created_at <= ?',
        ['2024-01-01 00:00:00', '2024-01-02 23:59:59']
      );

      assert.strictEqual(jobs.length, 2);
    });

    it('should sort jobs by date ascending', async () => {
      const jobs = await db.all(
        'SELECT * FROM jobs ORDER BY created_at ASC'
      );

      assert.strictEqual(jobs[0].name, 'Calibration Cube');
      assert.strictEqual(jobs[2].name, 'Test Print');
    });

    it('should sort jobs by date descending', async () => {
      const jobs = await db.all(
        'SELECT * FROM jobs ORDER BY created_at DESC'
      );

      assert.strictEqual(jobs[0].name, 'Test Print');
      assert.strictEqual(jobs[2].name, 'Calibration Cube');
    });

    it('should paginate job results', async () => {
      const pageSize = 2;
      const page = 1;
      const offset = (page - 1) * pageSize;

      const jobs = await db.all(
        'SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?',
        [pageSize, offset]
      );

      assert.strictEqual(jobs.length, 2);
    });
  });

  describe('Job Metadata', () => {
    it('should store and retrieve job comments', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, comments) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'complete', 'Print was successful']
      );

      const job = await db.get('SELECT comments FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.comments, 'Print was successful');
    });

    it('should update job comments', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'complete']
      );

      await db.run(
        'UPDATE jobs SET comments = ? WHERE id = ?',
        ['Updated comment', 1]
      );

      const job = await db.get('SELECT comments FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.comments, 'Updated comment');
    });

    it('should store filament information', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, filament) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'PLA - Red']
      );

      const job = await db.get('SELECT filament FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.filament, 'PLA - Red');
    });

    it('should toggle favorite status', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, favorite) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'complete', 0]
      );

      await db.run('UPDATE jobs SET favorite = ? WHERE id = ?', [1, 1]);
      let job = await db.get('SELECT favorite FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.favorite, 1);

      await db.run('UPDATE jobs SET favorite = ? WHERE id = ?', [0, 1]);
      job = await db.get('SELECT favorite FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.favorite, 0);
    });

    it('should assign issue to job', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'error']
      );

      await db.run('UPDATE jobs SET issue_id = ? WHERE id = ?', [42, 1]);

      const job = await db.get('SELECT issue_id FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.issue_id, 42);
    });
  });

  describe('Job File Naming', () => {
    it('should generate file name with job ID', async () => {
      const result = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', 'test.gcode']
      );

      const jobId = result.id;
      const fileName = `test_${jobId}.gcode`;

      await db.run('UPDATE jobs SET file_name = ? WHERE id = ?', [fileName, jobId]);

      const job = await db.get('SELECT file_name FROM jobs WHERE id = ?', [jobId]);
      assert.strictEqual(job.file_name, fileName);
    });

    it('should handle file names with multiple dots', async () => {
      const originalName = 'my.test.file.gcode';
      const result = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original) VALUES (?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue', originalName]
      );

      const baseName = originalName.split('.').slice(0, -1).join('.');
      const extension = originalName.split('.').pop();
      const fileName = `${baseName}_${result.id}.${extension}`;

      assert.strictEqual(fileName, `my.test.file_${result.id}.gcode`);
    });
  });

  describe('Job Status Transitions', () => {
    it('should transition from inqueue to printing', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'inqueue']
      );

      await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['printing', 1]);

      const job = await db.get('SELECT status FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.status, 'printing');
    });

    it('should transition from printing to complete', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'printing']
      );

      await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['complete', 1]);

      const job = await db.get('SELECT status FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.status, 'complete');
    });

    it('should transition from printing to error', async () => {
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorId, 'printing']
      );

      await db.run('UPDATE jobs SET status = ? WHERE id = ?', ['error', 1]);

      const job = await db.get('SELECT status FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.status, 'error');
    });

    it('should allow job rerun by creating duplicate', async () => {
      // Original job
      const gcodeData = 'G28\nG1 X10 Y10';
      const compressed = zlib.gzipSync(Buffer.from(gcodeData));

      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob, favorite, filament) VALUES (?, ?, ?, ?, ?, ?, ?)',
        ['Test Job', fabricatorId, 'complete', 'test.gcode', compressed, 1, 'PLA']
      );

      const originalJob = await db.get('SELECT * FROM jobs WHERE id = ?', [1]);

      // Create rerun job
      const result = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob, favorite, filament) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [originalJob.name, fabricatorId, 'inqueue', originalJob.file_name_original, originalJob.file_blob, originalJob.favorite, originalJob.filament]
      );

      const rerunJob = await db.get('SELECT * FROM jobs WHERE id = ?', [result.id]);

      assert.strictEqual(rerunJob.name, originalJob.name);
      assert.strictEqual(rerunJob.status, 'inqueue');
      assert.notStrictEqual(rerunJob.id, originalJob.id);
    });
  });
});
