import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert';
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

// Mock serial port listing
class MockSerialPort {
  static async list() {
    return [
      {
        path: '/dev/ttyUSB0',
        manufacturer: 'FTDI',
        serialNumber: 'A12345',
        hwid: 'USB\\VID_0403&PID_6001'
      },
      {
        path: '/dev/ttyUSB1',
        manufacturer: 'CH340',
        serialNumber: 'B67890',
        hwid: 'USB\\VID_1A86&PID_7523'
      }
    ];
  }
}

describe('Fabricator Operations', () => {
  let db;
  const testDbPath = path.join(__dirname, 'fabricators-test.db');

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
  });

  after(async () => {
    if (db) {
      await db.close();
    }
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('Fabricator Registration', () => {
    it('should register a new fabricator', async () => {
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1, 'ready']
      );

      assert.ok(result.id);
      assert.strictEqual(result.id, 1);
    });

    it('should retrieve registered fabricator', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1, 'ready']
      );

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [1]);
      assert.strictEqual(fabricator.name, 'Test Printer');
      assert.strictEqual(fabricator.devicePort, '/dev/ttyUSB0');
      assert.strictEqual(fabricator.status, 'ready');
    });

    it('should prevent duplicate device ports', async () => {
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

    it('should set default status to offline', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      const fabricator = await db.get('SELECT status FROM fabricators WHERE id = ?', [1]);
      assert.strictEqual(fabricator.status, 'offline');
    });

    it('should calculate next position automatically', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1]
      );

      const maxPos = await db.get('SELECT MAX(position) as max_pos FROM fabricators');
      const nextPosition = (maxPos?.max_pos || 0) + 1;

      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 2', '/dev/ttyUSB1', nextPosition]
      );

      const fabricator = await db.get('SELECT position FROM fabricators WHERE id = ?', [2]);
      assert.strictEqual(fabricator.position, 2);
    });

    it('should store printer model information', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, model) VALUES (?, ?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1, 'Prusa MK3']
      );

      const fabricator = await db.get('SELECT model FROM fabricators WHERE id = ?', [1]);
      assert.strictEqual(fabricator.model, 'Prusa MK3');
    });
  });

  describe('Port Listing', () => {
    it('should list available serial ports', async () => {
      const ports = await MockSerialPort.list();

      assert.ok(Array.isArray(ports));
      assert.ok(ports.length > 0);
      assert.ok(ports[0].path);
    });

    it('should return port metadata', async () => {
      const ports = await MockSerialPort.list();

      assert.ok(ports[0].manufacturer);
      assert.ok(ports[0].serialNumber);
      assert.ok(ports[0].hwid);
    });

    it('should filter available ports', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1]
      );

      const allPorts = await MockSerialPort.list();
      const usedPorts = await db.all('SELECT devicePort FROM fabricators');
      const usedPortPaths = usedPorts.map(p => p.devicePort);

      const availablePorts = allPorts.filter(port => !usedPortPaths.includes(port.path));

      assert.strictEqual(availablePorts.length, allPorts.length - 1);
      assert.ok(!availablePorts.some(p => p.path === '/dev/ttyUSB0'));
    });
  });

  describe('Fabricator Deletion', () => {
    it('should delete a fabricator', async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      await db.run('DELETE FROM fabricators WHERE id = ?', [1]);

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [1]);
      assert.strictEqual(fabricator, undefined);
    });

    it('should nullify jobs when fabricator is deleted', async () => {
      const fabricatorResult = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', fabricatorResult.id, 'inqueue']
      );

      // Nullify jobs before deleting fabricator
      await db.run('UPDATE jobs SET fabricator_id = NULL WHERE fabricator_id = ?', [fabricatorResult.id]);
      await db.run('DELETE FROM fabricators WHERE id = ?', [fabricatorResult.id]);

      const job = await db.get('SELECT fabricator_id FROM jobs WHERE id = ?', [1]);
      assert.strictEqual(job.fabricator_id, null);
    });

    it('should handle deleting non-existent fabricator', async () => {
      const result = await db.run('DELETE FROM fabricators WHERE id = ?', [999]);
      assert.strictEqual(result.changes, 0);
    });
  });

  describe('Fabricator Queries', () => {
    beforeEach(async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1, 'ready']
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Printer 2', '/dev/ttyUSB1', 2, 'printing']
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Printer 3', '/dev/ttyUSB2', 3, 'offline']
      );
    });

    it('should get all fabricators', async () => {
      const fabricators = await db.all('SELECT * FROM fabricators ORDER BY position ASC');

      assert.strictEqual(fabricators.length, 3);
      assert.strictEqual(fabricators[0].name, 'Printer 1');
      assert.strictEqual(fabricators[2].name, 'Printer 3');
    });

    it('should get fabricator by id', async () => {
      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [2]);

      assert.strictEqual(fabricator.name, 'Printer 2');
      assert.strictEqual(fabricator.status, 'printing');
    });

    it('should filter fabricators by status', async () => {
      const readyFabricators = await db.all(
        'SELECT * FROM fabricators WHERE status = ?',
        ['ready']
      );

      assert.strictEqual(readyFabricators.length, 1);
      assert.strictEqual(readyFabricators[0].name, 'Printer 1');
    });

    it('should get distinct printer models', async () => {
      await db.run('UPDATE fabricators SET model = ? WHERE id = ?', ['Prusa MK3', 1]);
      await db.run('UPDATE fabricators SET model = ? WHERE id = ?', ['Ender 3', 2]);
      await db.run('UPDATE fabricators SET model = ? WHERE id = ?', ['Prusa MK3', 3]);

      const models = await db.all(
        'SELECT DISTINCT model FROM fabricators WHERE model IS NOT NULL ORDER BY model ASC'
      );

      assert.strictEqual(models.length, 2);
      assert.strictEqual(models[0].model, 'Ender 3');
      assert.strictEqual(models[1].model, 'Prusa MK3');
    });
  });

  describe('Fabricator Updates', () => {
    let fabricatorId;

    beforeEach(async () => {
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1, 'ready']
      );
      fabricatorId = result.id;
    });

    it('should update fabricator name', async () => {
      await db.run('UPDATE fabricators SET name = ? WHERE id = ?', ['Updated Printer', fabricatorId]);

      const fabricator = await db.get('SELECT name FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.name, 'Updated Printer');
    });

    it('should update fabricator status', async () => {
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['printing', fabricatorId]);

      const fabricator = await db.get('SELECT status FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.status, 'printing');
    });

    it('should update fabricator model', async () => {
      await db.run('UPDATE fabricators SET model = ? WHERE id = ?', ['Prusa MK4', fabricatorId]);

      const fabricator = await db.get('SELECT model FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.model, 'Prusa MK4');
    });

    it('should handle status transitions', async () => {
      // offline -> ready
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['offline', fabricatorId]);
      let fabricator = await db.get('SELECT status FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.status, 'offline');

      // ready -> printing
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', fabricatorId]);
      fabricator = await db.get('SELECT status FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.status, 'ready');

      // printing -> ready
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['printing', fabricatorId]);
      fabricator = await db.get('SELECT status FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.status, 'printing');

      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', fabricatorId]);
      fabricator = await db.get('SELECT status FROM fabricators WHERE id = ?', [fabricatorId]);
      assert.strictEqual(fabricator.status, 'ready');
    });
  });

  describe('Fabricator Ordering', () => {
    beforeEach(async () => {
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1]
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 2', '/dev/ttyUSB1', 2]
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 3', '/dev/ttyUSB2', 3]
      );
    });

    it('should retrieve fabricators in position order', async () => {
      const fabricators = await db.all('SELECT * FROM fabricators ORDER BY position ASC');

      assert.strictEqual(fabricators[0].position, 1);
      assert.strictEqual(fabricators[1].position, 2);
      assert.strictEqual(fabricators[2].position, 3);
    });

    it('should reorder fabricators', async () => {
      // Reorder: [3, 1, 2]
      const fabricatorIds = [3, 1, 2];

      for (let i = 0; i < fabricatorIds.length; i++) {
        await db.run('UPDATE fabricators SET position = ? WHERE id = ?', [i + 1, fabricatorIds[i]]);
      }

      const fabricators = await db.all('SELECT * FROM fabricators ORDER BY position ASC');

      assert.strictEqual(fabricators[0].id, 3);
      assert.strictEqual(fabricators[1].id, 1);
      assert.strictEqual(fabricators[2].id, 2);
    });

    it('should handle empty position list', async () => {
      const fabricators = await db.all('SELECT * FROM fabricators WHERE position IS NULL');
      assert.strictEqual(fabricators.length, 0);
    });
  });

  describe('Fabricator Statistics', () => {
    beforeEach(async () => {
      const result1 = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 1', '/dev/ttyUSB0', 1]
      );
      const result2 = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Printer 2', '/dev/ttyUSB1', 2]
      );

      // Add jobs to fabricators
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 1', result1.id, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 2', result1.id, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 3', result2.id, 'inqueue']
      );
    });

    it('should count jobs per fabricator', async () => {
      const stats = await db.all(`
        SELECT f.id, f.name, COUNT(j.id) as job_count
        FROM fabricators f
        LEFT JOIN jobs j ON f.id = j.fabricator_id AND j.status = 'inqueue'
        GROUP BY f.id
        ORDER BY f.position ASC
      `);

      assert.strictEqual(stats.length, 2);
      assert.strictEqual(stats[0].job_count, 2);
      assert.strictEqual(stats[1].job_count, 1);
    });

    it('should find fabricator with most jobs', async () => {
      const result = await db.get(`
        SELECT f.id, f.name, COUNT(j.id) as job_count
        FROM fabricators f
        LEFT JOIN jobs j ON f.id = j.fabricator_id AND j.status = 'inqueue'
        GROUP BY f.id
        ORDER BY job_count DESC
        LIMIT 1
      `);

      assert.strictEqual(result.job_count, 2);
      assert.strictEqual(result.name, 'Printer 1');
    });

    it('should find fabricator with fewest jobs', async () => {
      const result = await db.get(`
        SELECT f.id, f.name, COUNT(j.id) as job_count
        FROM fabricators f
        LEFT JOIN jobs j ON f.id = j.fabricator_id AND j.status = 'inqueue'
        GROUP BY f.id
        ORDER BY job_count ASC
        LIMIT 1
      `);

      assert.strictEqual(result.job_count, 1);
      assert.strictEqual(result.name, 'Printer 2');
    });
  });

  describe('Fabricator Validation', () => {
    it('should require name field', async () => {
      await assert.rejects(
        async () => {
          await db.run(
            'INSERT INTO fabricators (devicePort, position) VALUES (?, ?)',
            ['/dev/ttyUSB0', 1]
          );
        },
        { message: /NOT NULL constraint failed/ }
      );
    });

    it('should allow null model field', async () => {
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        ['Test Printer', '/dev/ttyUSB0', 1]
      );

      const fabricator = await db.get('SELECT model FROM fabricators WHERE id = ?', [result.id]);
      assert.strictEqual(fabricator.model, null);
    });

    it('should handle long printer names', async () => {
      const longName = 'A'.repeat(255);
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position) VALUES (?, ?, ?)',
        [longName, '/dev/ttyUSB0', 1]
      );

      const fabricator = await db.get('SELECT name FROM fabricators WHERE id = ?', [result.id]);
      assert.strictEqual(fabricator.name, longName);
    });
  });
});
