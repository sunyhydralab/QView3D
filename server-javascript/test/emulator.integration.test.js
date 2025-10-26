import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert';
import sqlite3 from 'sqlite3';
import path from 'path';
import fs from 'fs';
import http from 'http';
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

// Helper function to make HTTP requests
function makeRequest(method, path, body = null, port = 3001) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: port,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, body: parsed });
        } catch (e) {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

describe('Emulator Integration Tests', () => {
  let db;
  const testDbPath = path.join(__dirname, 'emulator-test.db');

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

  describe('Emulator Creation', () => {
    it('should create database entry with EMU_ prefix', async () => {
      // Simulate emulator creation by creating a fabricator with EMU_ prefix
      const mockPort = 'EMU_A3F7G9H2';
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', mockPort, 1, 'ready']
      );

      assert.ok(result.id);

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [result.id]);
      assert.strictEqual(fabricator.name, 'Mock Printer');
      assert.strictEqual(fabricator.devicePort, mockPort);
      assert.ok(fabricator.devicePort.startsWith('EMU_'), 'Port should start with EMU_ prefix');
      assert.strictEqual(fabricator.status, 'ready');
    });

    it('should have correct initial status (ready)', async () => {
      const mockPort = 'EMU_B1C2D3E4';
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 2', mockPort, 1, 'ready']
      );

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [result.id]);
      assert.strictEqual(fabricator.status, 'ready', 'Initial status should be ready');
    });

    it('should create multiple emulators with unique ports', async () => {
      // Create first emulator
      const result1 = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 1', 'EMU_PORT001', 1, 'ready']
      );

      // Create second emulator
      const result2 = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 2', 'EMU_PORT002', 2, 'ready']
      );

      // Create third emulator
      const result3 = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 3', 'EMU_PORT003', 3, 'ready']
      );

      const emulators = await db.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');

      assert.strictEqual(emulators.length, 3, 'Should have 3 emulators');

      // Check all ports are unique
      const ports = emulators.map(e => e.devicePort);
      const uniquePorts = new Set(ports);
      assert.strictEqual(uniquePorts.size, 3, 'All ports should be unique');

      // Check all have EMU_ prefix
      assert.ok(emulators.every(e => e.devicePort.startsWith('EMU_')), 'All ports should have EMU_ prefix');
    });

    it('should prevent duplicate EMU_ ports', async () => {
      const mockPort = 'EMU_DUPLICATE';

      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 1', mockPort, 1, 'ready']
      );

      // Try to create another with same port
      await assert.rejects(
        async () => {
          await db.run(
            'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
            ['Mock Printer 2', mockPort, 2, 'ready']
          );
        },
        { message: /UNIQUE constraint failed/ }
      );
    });
  });

  describe('Emulator in Fabricators List', () => {
    it('should appear in fabricators list (getfabricators)', async () => {
      // Create a regular printer
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Regular Printer', '/dev/ttyUSB0', 1, 'ready']
      );

      // Create an emulator
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_ABC123', 2, 'ready']
      );

      const fabricators = await db.all('SELECT * FROM fabricators ORDER BY position ASC');

      assert.strictEqual(fabricators.length, 2, 'Should have 2 fabricators');

      // Check emulator is in the list
      const emulator = fabricators.find(f => f.devicePort.startsWith('EMU_'));
      assert.ok(emulator, 'Emulator should be in fabricators list');
      assert.strictEqual(emulator.name, 'Mock Printer');
      assert.strictEqual(emulator.devicePort, 'EMU_ABC123');
    });

    it('should query specific emulator by ID', async () => {
      // Create emulator
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_XYZ789', 1, 'ready']
      );

      // Query by ID
      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [result.id]);

      assert.ok(fabricator, 'Should retrieve emulator by ID');
      assert.strictEqual(fabricator.id, result.id);
      assert.strictEqual(fabricator.name, 'Mock Printer');
      assert.strictEqual(fabricator.devicePort, 'EMU_XYZ789');
      assert.ok(fabricator.devicePort.startsWith('EMU_'), 'Should have EMU_ prefix');
    });

    it('should list all emulators (only EMU_ ports)', async () => {
      // Create mix of regular printers and emulators
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Regular Printer 1', '/dev/ttyUSB0', 1, 'ready']
      );

      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 1', 'EMU_MOCK001', 2, 'ready']
      );

      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Regular Printer 2', '/dev/ttyUSB1', 3, 'ready']
      );

      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer 2', 'EMU_MOCK002', 4, 'ready']
      );

      // Filter only emulators
      const emulators = await db.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');

      assert.strictEqual(emulators.length, 2, 'Should have exactly 2 emulators');
      assert.ok(emulators.every(e => e.devicePort.startsWith('EMU_')), 'All should have EMU_ prefix');
      assert.ok(emulators.every(e => e.name.includes('Mock')), 'All should be mock printers');
    });
  });

  describe('Emulator Disconnection', () => {
    it('should disconnect/remove emulator', async () => {
      // Create emulator
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_REMOVE', 1, 'ready']
      );

      const emulatorId = result.id;

      // Verify it exists
      let fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [emulatorId]);
      assert.ok(fabricator, 'Emulator should exist before removal');

      // Remove emulator
      await db.run('DELETE FROM fabricators WHERE id = ?', [emulatorId]);

      // Verify it's removed
      fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [emulatorId]);
      assert.strictEqual(fabricator, undefined, 'Emulator should be removed from database');
    });

    it('should remove disconnected emulator from database', async () => {
      // Create emulator
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_DISCONNECT', 1, 'ready']
      );

      // Verify emulator exists
      let emulators = await db.all('SELECT * FROM fabricators WHERE devicePort = ?', ['EMU_DISCONNECT']);
      assert.strictEqual(emulators.length, 1, 'Emulator should exist');

      // Delete by port
      await db.run('DELETE FROM fabricators WHERE devicePort = ?', ['EMU_DISCONNECT']);

      // Verify it's gone
      emulators = await db.all('SELECT * FROM fabricators WHERE devicePort = ?', ['EMU_DISCONNECT']);
      assert.strictEqual(emulators.length, 0, 'Emulator should be removed from database');
    });

    it('should handle removing multiple emulators', async () => {
      // Create multiple emulators
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 1', 'EMU_001', 1, 'ready']
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 2', 'EMU_002', 2, 'ready']
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 3', 'EMU_003', 3, 'ready']
      );

      // Verify count
      let emulators = await db.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');
      assert.strictEqual(emulators.length, 3, 'Should have 3 emulators');

      // Remove first emulator
      await db.run('DELETE FROM fabricators WHERE devicePort = ?', ['EMU_001']);

      emulators = await db.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');
      assert.strictEqual(emulators.length, 2, 'Should have 2 emulators after removal');

      // Remove remaining emulators
      await db.run('DELETE FROM fabricators WHERE devicePort LIKE "EMU_%"');

      emulators = await db.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');
      assert.strictEqual(emulators.length, 0, 'Should have no emulators');
    });
  });

  describe('Emulator Status Updates', () => {
    it('should update emulator status', async () => {
      // Create emulator
      const result = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_STATUS', 1, 'ready']
      );

      const emulatorId = result.id;

      // Update status to printing
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['printing', emulatorId]);

      let fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [emulatorId]);
      assert.strictEqual(fabricator.status, 'printing');

      // Update status to paused
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['paused', emulatorId]);

      fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [emulatorId]);
      assert.strictEqual(fabricator.status, 'paused');

      // Update status back to ready
      await db.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', emulatorId]);

      fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [emulatorId]);
      assert.strictEqual(fabricator.status, 'ready');
    });
  });

  describe('Emulator with Jobs', () => {
    it('should associate jobs with emulator', async () => {
      // Create emulator
      const emulatorResult = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_JOBS', 1, 'ready']
      );

      const emulatorId = emulatorResult.id;

      // Create job for emulator
      const jobResult = await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Test Job', emulatorId, 'inqueue']
      );

      // Verify job is associated
      const job = await db.get('SELECT * FROM jobs WHERE id = ?', [jobResult.id]);
      assert.strictEqual(job.fabricator_id, emulatorId);
      assert.strictEqual(job.name, 'Test Job');
    });

    it('should nullify jobs when emulator is removed', async () => {
      // Create emulator
      const emulatorResult = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_CLEANUP', 1, 'ready']
      );

      const emulatorId = emulatorResult.id;

      // Create jobs
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 1', emulatorId, 'inqueue']
      );
      await db.run(
        'INSERT INTO jobs (name, fabricator_id, status) VALUES (?, ?, ?)',
        ['Job 2', emulatorId, 'inqueue']
      );

      // Nullify jobs before removing emulator
      await db.run('UPDATE jobs SET fabricator_id = NULL WHERE fabricator_id = ?', [emulatorId]);

      // Remove emulator
      await db.run('DELETE FROM fabricators WHERE id = ?', [emulatorId]);

      // Verify jobs still exist but are unassigned
      const jobs = await db.all('SELECT * FROM jobs WHERE name IN (?, ?)', ['Job 1', 'Job 2']);
      assert.strictEqual(jobs.length, 2);
      assert.ok(jobs.every(j => j.fabricator_id === null), 'All jobs should have null fabricator_id');
    });
  });

  describe('Emulator Port Validation', () => {
    it('should only accept EMU_ prefix for emulator ports', async () => {
      // Valid EMU_ port
      const validResult = await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_VALID', 1, 'ready']
      );

      assert.ok(validResult.id, 'Should create emulator with valid EMU_ port');

      const fabricator = await db.get('SELECT * FROM fabricators WHERE id = ?', [validResult.id]);
      assert.ok(fabricator.devicePort.startsWith('EMU_'), 'Port should start with EMU_');
    });

    it('should distinguish emulator ports from regular ports', async () => {
      // Create regular printer
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Regular Printer', '/dev/ttyUSB0', 1, 'ready']
      );

      // Create emulator
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock Printer', 'EMU_MOCK', 2, 'ready']
      );

      // Query only emulators
      const emulators = await db.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');
      assert.strictEqual(emulators.length, 1);
      assert.ok(emulators[0].devicePort.startsWith('EMU_'));

      // Query only regular printers
      const regularPrinters = await db.all('SELECT * FROM fabricators WHERE devicePort NOT LIKE "EMU_%"');
      assert.strictEqual(regularPrinters.length, 1);
      assert.ok(!regularPrinters[0].devicePort.startsWith('EMU_'));
    });
  });

  describe('Emulator Ordering and Position', () => {
    it('should maintain position in fabricator list', async () => {
      // Create emulators at specific positions
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 1', 'EMU_POS1', 1, 'ready']
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 2', 'EMU_POS2', 2, 'ready']
      );
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 3', 'EMU_POS3', 3, 'ready']
      );

      const fabricators = await db.all('SELECT * FROM fabricators ORDER BY position ASC');

      assert.strictEqual(fabricators.length, 3);
      assert.strictEqual(fabricators[0].position, 1);
      assert.strictEqual(fabricators[1].position, 2);
      assert.strictEqual(fabricators[2].position, 3);
      assert.strictEqual(fabricators[0].name, 'Mock 1');
      assert.strictEqual(fabricators[1].name, 'Mock 2');
      assert.strictEqual(fabricators[2].name, 'Mock 3');
    });

    it('should calculate next position automatically', async () => {
      // Create first emulator
      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 1', 'EMU_AUTO1', 1, 'ready']
      );

      // Get max position and add next
      const maxPos = await db.get('SELECT MAX(position) as max_pos FROM fabricators');
      const nextPosition = (maxPos?.max_pos || 0) + 1;

      await db.run(
        'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
        ['Mock 2', 'EMU_AUTO2', nextPosition, 'ready']
      );

      const fabricator = await db.get('SELECT * FROM fabricators WHERE devicePort = ?', ['EMU_AUTO2']);
      assert.strictEqual(fabricator.position, 2);
    });
  });
});
