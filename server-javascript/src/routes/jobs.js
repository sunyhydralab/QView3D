import express from 'express';
import multer from 'multer';
import zlib from 'zlib';
import database from '../database.js';
import fabricatorManager from '../fabricatorManager.js';

const router = express.Router();

// Configure multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

// Get job history
router.get('/getjobs', async (req, res) => {
  try {
    const {
      page = 1,
      pageSize = 10,
      printerIds,
      oldestFirst = 'false',
      searchJob = '',
      searchCriteria = '',
      searchTicketId = '',
      favoriteOnly = 'false',
      issueIds,
      startdate = '',
      enddate = '',
      fromError = 0,
      countOnly = 0
    } = req.query;

    let sql = 'SELECT * FROM jobs WHERE 1=1';
    const params = [];

    // Filter by printer IDs
    if (printerIds) {
      const ids = JSON.parse(printerIds);
      if (ids.length > 0) {
        sql += ` AND fabricator_id IN (${ids.map(() => '?').join(',')})`;
        params.push(...ids);
      }
    }

    // Search by job name
    if (searchJob) {
      sql += ' AND name LIKE ?';
      params.push(`%${searchJob}%`);
    }

    // Filter by favorite
    if (favoriteOnly === 'true') {
      sql += ' AND favorite = 1';
    }

    // Filter by issue IDs
    if (issueIds) {
      const ids = JSON.parse(issueIds);
      if (ids.length > 0) {
        sql += ` AND issue_id IN (${ids.map(() => '?').join(',')})`;
        params.push(...ids);
      }
    }

    // Filter by date range
    if (startdate) {
      sql += ' AND created_at >= ?';
      params.push(startdate);
    }
    if (enddate) {
      sql += ' AND created_at <= ?';
      params.push(enddate);
    }

    // Count only
    if (parseInt(countOnly) === 1) {
      const countSql = sql.replace('SELECT *', 'SELECT COUNT(*) as count');
      const result = await database.get(countSql, params);
      return res.json({ count: result.count });
    }

    // Ordering
    sql += oldestFirst === 'true' ? ' ORDER BY created_at ASC' : ' ORDER BY created_at DESC';

    // Pagination
    const offset = (parseInt(page) - 1) * parseInt(pageSize);
    sql += ' LIMIT ? OFFSET ?';
    params.push(parseInt(pageSize), offset);

    const jobs = await database.all(sql, params);
    res.json(jobs);
  } catch (error) {
    console.error('Error getting jobs:', error);
    res.status(500).json({ error: 'Failed to get jobs', details: error.message });
  }
});

// Add job to queue
router.post('/addjobtoqueue', upload.single('file'), async (req, res) => {
  try {
    const { name, printerid, favorite, td_id, filament, priority } = req.body;
    const file = req.file;

    if (!file) {
      return res.status(400).json({ error: 'File is required' });
    }

    // Compress file
    const compressed = zlib.gzipSync(file.buffer);

    // Insert job into database
    const result = await database.run(
      `INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob, favorite, td_id, filament)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        name,
        parseInt(printerid),
        'inqueue',
        file.originalname,
        compressed,
        favorite === 'true' ? 1 : 0,
        parseInt(td_id),
        filament
      ]
    );

    const jobId = result.id;

    // Update file name with ID
    const baseName = file.originalname.split('.').slice(0, -1).join('.');
    const extension = file.originalname.split('.').pop();
    const fileName = `${baseName}_${jobId}.${extension}`;

    await database.run('UPDATE jobs SET file_name = ? WHERE id = ?', [fileName, jobId]);

    // Get the job and add to queue
    const job = await database.get('SELECT * FROM jobs WHERE id = ?', [jobId]);
    const toFront = priority === 'high' || priority === 'front';
    fabricatorManager.addJobToQueue(parseInt(printerid), job, toFront);

    res.json({
      success: true,
      message: 'Job added to printer queue',
      id: jobId
    });
  } catch (error) {
    console.error('Error adding job:', error);
    res.status(500).json({ error: 'Failed to add job', details: error.message });
  }
});

// Auto queue job
router.post('/autoqueue', upload.single('file'), async (req, res) => {
  try {
    const { name, favorite, td_id, filament } = req.body;
    const file = req.file;

    if (!file) {
      return res.status(400).json({ error: 'File is required' });
    }

    // Find fabricator with smallest queue
    const fabricators = await database.all(`
      SELECT f.id, COUNT(j.id) as job_count
      FROM fabricators f
      LEFT JOIN jobs j ON f.id = j.fabricator_id AND j.status = 'inqueue'
      GROUP BY f.id
      ORDER BY job_count ASC
      LIMIT 1
    `);

    if (fabricators.length === 0) {
      return res.status(404).json({ error: 'No fabricators available' });
    }

    const fabricatorId = fabricators[0].id;

    // Compress file
    const compressed = zlib.gzipSync(file.buffer);

    // Insert job
    const result = await database.run(
      `INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob, favorite, td_id, filament)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        name,
        fabricatorId,
        'inqueue',
        file.originalname,
        compressed,
        favorite === 'true' ? 1 : 0,
        parseInt(td_id),
        filament
      ]
    );

    const jobId = result.id;

    // Update file name with ID
    const baseName = file.originalname.split('.').slice(0, -1).join('.');
    const extension = file.originalname.split('.').pop();
    const fileName = `${baseName}_${jobId}.${extension}`;

    await database.run('UPDATE jobs SET file_name = ? WHERE id = ?', [fileName, jobId]);

    // Get the job and add to queue
    const job = await database.get('SELECT * FROM jobs WHERE id = ?', [jobId]);
    fabricatorManager.addJobToQueue(fabricatorId, job, false);

    res.json({
      success: true,
      message: 'Job added to printer queue',
      id: jobId,
      fabricator_id: fabricatorId
    });
  } catch (error) {
    console.error('Error auto-queueing job:', error);
    res.status(500).json({ error: 'Failed to auto-queue job', details: error.message });
  }
});

// Cancel job
router.post('/canceljob', async (req, res) => {
  try {
    const { jobpk } = req.body;

    await database.run('UPDATE jobs SET status = ? WHERE id = ?', ['cancelled', jobpk]);

    res.json({ success: true, message: 'Job cancelled' });
  } catch (error) {
    console.error('Error cancelling job:', error);
    res.status(500).json({ error: 'Failed to cancel job', details: error.message });
  }
});

// Cancel jobs from queue
router.post('/cancelfromqueue', async (req, res) => {
  try {
    const { jobarr } = req.body;

    for (const jobpk of jobarr) {
      await database.run('UPDATE jobs SET status = ? WHERE id = ?', ['cancelled', jobpk]);
    }

    res.json({ success: true, message: 'Jobs cancelled' });
  } catch (error) {
    console.error('Error cancelling jobs:', error);
    res.status(500).json({ error: 'Failed to cancel jobs', details: error.message });
  }
});

// Update job status
router.post('/updatejobstatus', async (req, res) => {
  try {
    const { jobid, status } = req.body;

    await database.run('UPDATE jobs SET status = ? WHERE id = ?', [status, jobid]);

    res.json({ success: true, message: 'Job status updated' });
  } catch (error) {
    console.error('Error updating job status:', error);
    res.status(500).json({ error: 'Failed to update job status', details: error.message });
  }
});

// Delete job
router.post('/deletejob', async (req, res) => {
  try {
    const { jobid } = req.body;

    await database.run('DELETE FROM jobs WHERE id = ?', [jobid]);

    res.json({ success: true, message: 'Job deleted' });
  } catch (error) {
    console.error('Error deleting job:', error);
    res.status(500).json({ error: 'Failed to delete job', details: error.message });
  }
});

// Get file
router.get('/getfile', async (req, res) => {
  try {
    const { jobid } = req.query;

    const job = await database.get('SELECT file_blob, file_name_original FROM jobs WHERE id = ?', [jobid]);

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    // Decompress file
    const decompressed = zlib.gunzipSync(job.file_blob).toString('utf-8');

    res.json({
      file: decompressed,
      file_name: job.file_name_original
    });
  } catch (error) {
    console.error('Error getting file:', error);
    res.status(500).json({ error: 'Failed to get file', details: error.message });
  }
});

// Favorite job
router.post('/favoritejob', async (req, res) => {
  try {
    const { jobid, favorite } = req.body;

    await database.run('UPDATE jobs SET favorite = ? WHERE id = ?', [favorite ? 1 : 0, jobid]);

    res.json({ success: true, message: 'Job favorite status updated' });
  } catch (error) {
    console.error('Error updating favorite:', error);
    res.status(500).json({ error: 'Failed to update favorite', details: error.message });
  }
});

// Get favorite jobs
router.get('/getfavoritejobs', async (req, res) => {
  try {
    const jobs = await database.all('SELECT * FROM jobs WHERE favorite = 1 ORDER BY created_at DESC');
    res.json(jobs);
  } catch (error) {
    console.error('Error getting favorite jobs:', error);
    res.status(500).json({ error: 'Failed to get favorite jobs', details: error.message });
  }
});

// Assign issue to job
router.post('/assignissue', async (req, res) => {
  try {
    const { jobid, issueid } = req.body;

    await database.run('UPDATE jobs SET issue_id = ? WHERE id = ?', [issueid, jobid]);

    res.json({ success: true, message: 'Issue assigned to job' });
  } catch (error) {
    console.error('Error assigning issue:', error);
    res.status(500).json({ error: 'Failed to assign issue', details: error.message });
  }
});

// Remove issue from job
router.post('/removeissue', async (req, res) => {
  try {
    const { jobid } = req.body;

    await database.run('UPDATE jobs SET issue_id = NULL WHERE id = ?', [jobid]);

    res.json({ success: true, message: 'Issue removed from job' });
  } catch (error) {
    console.error('Error removing issue:', error);
    res.status(500).json({ error: 'Failed to remove issue', details: error.message });
  }
});

// Save comment
router.post('/savecomment', async (req, res) => {
  try {
    const { jobid, comments } = req.body;

    await database.run('UPDATE jobs SET comments = ? WHERE id = ?', [comments, jobid]);

    res.json({ success: true, message: 'Comment saved' });
  } catch (error) {
    console.error('Error saving comment:', error);
    res.status(500).json({ error: 'Failed to save comment', details: error.message });
  }
});

// Start print
router.post('/startprint', async (req, res) => {
  try {
    const { printerid, jobid } = req.body;

    await database.run(
      'UPDATE jobs SET status = ?, time_start = CURRENT_TIMESTAMP WHERE id = ?',
      ['printing', jobid]
    );

    res.json({ success: true, message: 'Print started' });
  } catch (error) {
    console.error('Error starting print:', error);
    res.status(500).json({ error: 'Failed to start print', details: error.message });
  }
});

/**
 * Reorder jobs in a fabricator's queue
 * This endpoint accepts an array of job IDs and reorders the queue to match
 * the order specified in the array. This is a frontend-friendly endpoint that
 * provides the same functionality as the Python backend's /reorderqueue.
 *
 * Request body:
 * - fabricator_id: ID of the fabricator whose queue should be reordered
 * - job_ids: Array of job IDs in the desired order
 *
 * Example:
 * {
 *   "fabricator_id": 1,
 *   "job_ids": [5, 3, 7, 2]
 * }
 */
router.post('/reorderqueue', async (req, res) => {
  try {
    const { fabricator_id, job_ids } = req.body;

    // Validate required fields
    if (!fabricator_id || !job_ids) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'Both fabricator_id and job_ids are required'
      });
    }

    // Validate job_ids is an array
    if (!Array.isArray(job_ids)) {
      return res.status(400).json({
        error: 'Invalid job_ids format',
        details: 'job_ids must be an array'
      });
    }

    // Get the queue for the specified fabricator
    const queue = fabricatorManager.getQueue(fabricator_id);

    if (!queue) {
      return res.status(404).json({
        error: 'Fabricator not found',
        details: `No queue found for fabricator ID ${fabricator_id}`
      });
    }

    // Reorder the queue using the provided job IDs
    queue.reorder(job_ids);

    console.log(`Queue reordered for fabricator ${fabricator_id}. New order: [${job_ids.join(', ')}]`);

    res.json({
      success: true,
      message: 'Queue reordered successfully'
    });
  } catch (error) {
    console.error('Error reordering queue:', error);
    res.status(500).json({
      error: 'Failed to reorder queue',
      details: error.message
    });
  }
});

// Bump job in queue
router.post('/bumpjob', async (req, res) => {
  try {
    const { printerid, jobid, choice } = req.body;

    // Validate required fields
    if (!printerid || !jobid || choice === undefined) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'printerid, jobid, and choice are required'
      });
    }

    // Get the queue for the specified fabricator
    const queue = fabricatorManager.getQueue(printerid);

    if (!queue) {
      return res.status(404).json({
        error: 'Fabricator not found',
        details: `No queue found for fabricator ID ${printerid}`
      });
    }

    // Bump the job based on choice
    // 1 = bump up, 2 = bump down, 3 = bump to front, 4 = bump to back
    if (choice === 1) {
      queue.bump(true, jobid);
    } else if (choice === 2) {
      queue.bump(false, jobid);
    } else if (choice === 3) {
      queue.bumpExtreme(true, jobid);
    } else if (choice === 4) {
      queue.bumpExtreme(false, jobid);
    } else {
      return res.status(400).json({
        error: 'Invalid choice',
        details: 'Choice must be 1 (up), 2 (down), 3 (front), or 4 (back)'
      });
    }

    res.json({
      success: true,
      message: 'Job bumped in printer queue'
    });
  } catch (error) {
    console.error('Error bumping job:', error);
    res.status(500).json({
      error: 'Failed to bump job',
      details: error.message
    });
  }
});

// Move job between fabricators
router.post('/movejob', async (req, res) => {
  try {
    const { printerid, arr } = req.body;

    // Validate required fields
    if (!printerid || !arr) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'Both printerid and arr are required'
      });
    }

    // Validate arr is an array
    if (!Array.isArray(arr)) {
      return res.status(400).json({
        error: 'Invalid arr format',
        details: 'arr must be an array of job IDs'
      });
    }

    // Get the queue for the specified fabricator
    const queue = fabricatorManager.getQueue(printerid);

    if (!queue) {
      return res.status(404).json({
        error: 'Fabricator not found',
        details: `No queue found for fabricator ID ${printerid}`
      });
    }

    // Reorder the queue using the provided job IDs
    queue.reorder(arr);

    console.log(`Queue reordered for fabricator ${printerid}. New order: [${arr.join(', ')}]`);

    res.json({
      success: true,
      message: 'Queue updated successfully'
    });
  } catch (error) {
    console.error('Error moving job:', error);
    res.status(500).json({
      error: 'Failed to move job',
      details: error.message
    });
  }
});

// Release job back to pool
router.post('/releasejob', async (req, res) => {
  try {
    const { jobpk, key, printerid } = req.body;

    // Validate required fields
    if (!jobpk || key === undefined || !printerid) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'jobpk, key, and printerid are required'
      });
    }

    // Get the job from database
    const job = await database.get('SELECT * FROM jobs WHERE id = ?', [jobpk]);

    if (!job) {
      return res.status(404).json({
        error: 'Job not found',
        details: `No job found with ID ${jobpk}`
      });
    }

    // Get the fabricator
    const fabricatorId = job.fabricator_id;
    const queue = fabricatorManager.getQueue(fabricatorId);

    if (!queue) {
      return res.status(404).json({
        error: 'Fabricator not found',
        details: `No queue found for fabricator ID ${fabricatorId}`
      });
    }

    // Remove job from queue if it's at the front
    if (queue.length > 0 && queue[0].id === jobpk) {
      queue.removeJob();
    }

    // Get current fabricator status
    const fabricator = await database.get('SELECT * FROM fabricators WHERE id = ?', [printerid]);

    // Handle different release scenarios
    // key 3 = mark as error and set fabricator to ready
    // key 2 = rerun job at front of queue
    // key 1 = just set fabricator to ready
    if (key === 3) {
      // Mark job as error
      await database.run('UPDATE jobs SET status = ? WHERE id = ?', ['error', jobpk]);

      // Set fabricator to ready
      if (fabricator && fabricator.status !== 'offline') {
        await database.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', printerid]);
      }
    } else if (key === 2) {
      // Rerun job at front of queue
      if (fabricator && fabricator.status !== 'offline') {
        await database.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', printerid]);
      }

      // Create a new job for rerun
      const newResult = await database.run(
        `INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob, favorite, td_id, filament)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          job.name,
          printerid,
          'inqueue',
          job.file_name_original,
          job.file_blob,
          job.favorite,
          job.td_id,
          job.filament
        ]
      );

      const newJobId = newResult.id;

      // Update file name with new ID
      const baseName = job.file_name_original.split('.').slice(0, -1).join('.');
      const extension = job.file_name_original.split('.').pop();
      const fileName = `${baseName}_${newJobId}.${extension}`;

      await database.run('UPDATE jobs SET file_name = ? WHERE id = ?', [fileName, newJobId]);

      // Get the new job and add to front of queue
      const newJob = await database.get('SELECT * FROM jobs WHERE id = ?', [newJobId]);
      const newQueue = fabricatorManager.getQueue(printerid);
      if (newQueue) {
        newQueue.addToFront(newJob);
      }

      return res.json({
        success: true,
        message: 'Job requeued at front',
        id: newJobId
      });
    } else if (key === 1) {
      // Just set fabricator to ready
      if (fabricator && fabricator.status !== 'offline') {
        await database.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', printerid]);
      }
    }

    res.json({
      success: true,
      message: 'Job released successfully'
    });
  } catch (error) {
    console.error('Error releasing job:', error);
    res.status(500).json({
      error: 'Failed to release job',
      details: error.message
    });
  }
});

// Rerun job
router.post('/rerunjob', async (req, res) => {
  try {
    const { printerpk, jobpk } = req.body;

    // Validate required fields
    if (!printerpk || !jobpk) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'Both printerpk and jobpk are required'
      });
    }

    // Get the job from database
    const job = await database.get('SELECT * FROM jobs WHERE id = ?', [jobpk]);

    if (!job) {
      return res.status(404).json({
        error: 'Job not found',
        details: `No job found with ID ${jobpk}`
      });
    }

    // Check if the fabricator exists
    const queue = fabricatorManager.getQueue(printerpk);
    if (!queue) {
      return res.status(404).json({
        error: 'Fabricator not found',
        details: `No queue found for fabricator ID ${printerpk}`
      });
    }

    // Create a new job for rerun
    const result = await database.run(
      `INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_blob, favorite, td_id, filament)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        job.name,
        printerpk,
        'inqueue',
        job.file_name_original,
        job.file_blob,
        job.favorite,
        job.td_id,
        job.filament
      ]
    );

    const newJobId = result.id;

    // Update file name with new ID
    const baseName = job.file_name_original.split('.').slice(0, -1).join('.');
    const extension = job.file_name_original.split('.').pop();
    const fileName = `${baseName}_${newJobId}.${extension}`;

    await database.run('UPDATE jobs SET file_name = ? WHERE id = ?', [fileName, newJobId]);

    // Get the new job and add to back of queue
    const newJob = await database.get('SELECT * FROM jobs WHERE id = ?', [newJobId]);
    fabricatorManager.addJobToQueue(printerpk, newJob, false);

    res.json({
      success: true,
      message: 'Job added to printer queue',
      id: newJobId
    });
  } catch (error) {
    console.error('Error rerunning job:', error);
    res.status(500).json({
      error: 'Failed to rerun job',
      details: error.message
    });
  }
});

/**
 * GET/POST /downloadcsv - Export job history to CSV format
 *
 * Request body:
 * - allJobs: 1 to export all jobs, 0 to export specific jobs
 * - jobIds: Array of job IDs to export (required if allJobs is 0)
 *
 * Returns CSV file data as string
 */
router.post('/downloadcsv', async (req, res) => {
  try {
    const { allJobs, jobIds } = req.body;

    let jobs;
    if (allJobs === 1) {
      // Get all jobs with issue information
      jobs = await database.all(`
        SELECT
          j.*,
          i.name as issue_name,
          f.name as fabricator_name
        FROM jobs j
        LEFT JOIN issues i ON j.issue_id = i.id
        LEFT JOIN fabricators f ON j.fabricator_id = f.id
        ORDER BY j.created_at DESC
      `);
    } else {
      // Get specific jobs
      if (!jobIds || !Array.isArray(jobIds) || jobIds.length === 0) {
        return res.status(400).json({
          error: 'Missing required field',
          details: 'jobIds array is required when allJobs is not 1'
        });
      }

      const placeholders = jobIds.map(() => '?').join(',');
      jobs = await database.all(`
        SELECT
          j.*,
          i.name as issue_name,
          f.name as fabricator_name
        FROM jobs j
        LEFT JOIN issues i ON j.issue_id = i.id
        LEFT JOIN fabricators f ON j.fabricator_id = f.id
        WHERE j.id IN (${placeholders})
        ORDER BY j.created_at DESC
      `, jobIds);
    }

    // Create CSV header
    const csvHeaders = ['td_id', 'printer', 'name', 'file_name_original', 'status', 'date', 'issue', 'comments'];
    let csvContent = csvHeaders.join(',') + '\n';

    // Add data rows
    for (const job of jobs) {
      const row = [
        job.td_id || '',
        job.fabricator_name || '',
        `"${(job.name || '').replace(/"/g, '""')}"`,
        `"${(job.file_name_original || '').replace(/"/g, '""')}"`,
        job.status || '',
        job.created_at || '',
        job.issue_name || '',
        `"${(job.comments || '').replace(/"/g, '""')}"`
      ];
      csvContent += row.join(',') + '\n';
    }

    // Return CSV content
    res.json({
      success: true,
      csv: csvContent,
      filename: `jobs_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.csv`
    });

  } catch (error) {
    console.error('Error generating CSV:', error);
    res.status(500).json({
      error: 'Failed to generate CSV',
      details: error.message
    });
  }
});

/**
 * GET/POST /removeCSV - Clean up generated CSV files
 * This endpoint is for compatibility with Python backend
 * In the JavaScript version, CSVs are generated in-memory and returned directly,
 * so this endpoint simply returns success
 */
router.post('/removeCSV', async (req, res) => {
  try {
    // In the JavaScript backend, we don't store CSV files on disk
    // They are generated in-memory and sent directly to the client
    // This endpoint exists for API compatibility
    res.json({
      success: true,
      message: 'CSV file removed successfully.'
    });
  } catch (error) {
    console.error('Error removing CSV:', error);
    res.status(500).json({
      error: 'Failed to remove CSV',
      details: error.message
    });
  }
});

/**
 * POST /refetchtimedata - Recalculate job timing data from files
 *
 * Request body:
 * - jobid: ID of the job
 * - printerid: ID of the printer/fabricator
 *
 * Returns current timing information for the job
 */
router.post('/refetchtimedata', async (req, res) => {
  try {
    const { jobid, printerid } = req.body;

    if (!jobid || !printerid) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'Both jobid and printerid are required'
      });
    }

    // Get the queue for this fabricator
    const queue = fabricatorManager.getQueue(printerid);
    if (!queue) {
      return res.status(404).json({
        error: 'Fabricator not found',
        details: `No queue found for fabricator ID ${printerid}`
      });
    }

    // Get the current job from the queue
    const queueData = queue.toJSON();
    if (queueData.length === 0) {
      return res.status(404).json({
        error: 'No job found',
        details: 'No job currently in queue'
      });
    }

    const currentJob = queueData[0];

    // Get job details from database
    const job = await database.get('SELECT * FROM jobs WHERE id = ?', [jobid]);
    if (!job) {
      return res.status(404).json({
        error: 'Job not found',
        details: `No job found with ID ${jobid}`
      });
    }

    // Calculate timing data
    const now = new Date();
    const timeStart = job.time_start ? new Date(job.time_start) : now;
    const totalSeconds = job.time_total || 0;
    const eta = new Date(timeStart.getTime() + (totalSeconds * 1000));
    const pauseTime = job.time_paused ? new Date(job.time_paused) : now;

    res.json({
      total: totalSeconds,
      eta: eta.toISOString(),
      timestart: timeStart.toISOString(),
      pause: pauseTime.toISOString()
    });

  } catch (error) {
    console.error('Error refetching time data:', error);
    res.status(500).json({
      error: 'Failed to refetch time data',
      details: error.message
    });
  }
});

/**
 * POST /clearspace - Storage cleanup (delete old completed jobs)
 * Removes file blobs from jobs older than 6 months that are not marked as favorites
 */
router.post('/clearspace', async (req, res) => {
  try {
    // Calculate date 6 months ago
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    const sixMonthsAgoISO = sixMonthsAgo.toISOString();

    // Find old jobs that are not favorites
    const oldJobs = await database.all(
      'SELECT id, file_name_original FROM jobs WHERE created_at < ? AND favorite = 0 AND file_blob IS NOT NULL',
      [sixMonthsAgoISO]
    );

    // Update jobs to remove file blobs and mark as removed
    for (const job of oldJobs) {
      const newFileName = job.file_name_original.includes('Removed after 6 months')
        ? job.file_name_original
        : `${job.file_name_original}: Removed after 6 months`;

      await database.run(
        'UPDATE jobs SET file_blob = NULL, file_name_original = ? WHERE id = ?',
        [newFileName, job.id]
      );
    }

    console.log(`Cleared ${oldJobs.length} old job files`);

    res.json({
      success: true,
      message: 'Space cleared successfully.',
      cleaned: oldJobs.length
    });

  } catch (error) {
    console.error('Error clearing space:', error);
    res.status(500).json({
      error: 'Failed to clear space',
      details: error.message
    });
  }
});

/**
 * POST /jobdbinsert - Direct database insert for bulk operations
 * Allows direct insertion of job data into the database
 *
 * Request body:
 * - jobdata: JSON string or object containing job information
 *   - name: Job name
 *   - printer_id: Fabricator ID
 *   - status: Job status
 *   - file_name: File name
 *   - file_path: Path to file (optional)
 *
 * Returns success message
 */
router.post('/jobdbinsert', async (req, res) => {
  try {
    let jobdata = req.body.jobdata || req.body;

    // Parse JSON string if needed
    if (typeof jobdata === 'string') {
      jobdata = JSON.parse(jobdata);
    }

    // Extract fields from jobdata
    const {
      name,
      printer_id,
      status,
      file_name,
      file_path
    } = jobdata;

    // Validate required fields
    if (!name || !printer_id || !status) {
      return res.status(400).json({
        error: 'Missing required fields',
        details: 'name, printer_id, and status are required'
      });
    }

    // Read file if path is provided
    let fileBlob = null;
    if (file_path) {
      try {
        const fs = await import('fs/promises');
        const fileContent = await fs.readFile(file_path);
        const zlib = await import('zlib');
        fileBlob = zlib.gzipSync(fileContent);
      } catch (err) {
        console.error('Error reading file:', err);
      }
    }

    // Insert job into database
    const result = await database.run(
      `INSERT INTO jobs (name, fabricator_id, status, file_name_original, file_name, file_blob)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [
        name,
        printer_id,
        status,
        file_name || 'unknown',
        file_name || 'unknown',
        fileBlob
      ]
    );

    console.log(`Job inserted via jobdbinsert: ID ${result.id}`);

    res.json({
      success: true,
      message: 'Job inserted successfully',
      id: result.id
    });

  } catch (error) {
    console.error('Error inserting job:', error);
    res.status(500).json({
      error: 'Failed to insert job',
      details: error.message
    });
  }
});

/**
 * POST /nullifyjobs - Bulk nullify jobs operation
 * Sets the fabricator_id to 0 for all jobs associated with a specific printer
 * Used when removing a fabricator to preserve job history
 *
 * Request body:
 * - printerid: ID of the printer/fabricator to nullify jobs for
 *
 * Returns success message
 */
router.post('/nullifyjobs', async (req, res) => {
  try {
    const { printerid } = req.body;

    if (!printerid) {
      return res.status(400).json({
        error: 'Missing required field',
        details: 'printerid is required'
      });
    }

    // Get count of jobs to be nullified
    const countResult = await database.get(
      'SELECT COUNT(*) as count FROM jobs WHERE fabricator_id = ?',
      [printerid]
    );

    // Nullify fabricator_id for all jobs associated with this printer
    await database.run(
      'UPDATE jobs SET fabricator_id = 0 WHERE fabricator_id = ?',
      [printerid]
    );

    console.log(`Nullified ${countResult.count} jobs for fabricator ${printerid}`);

    res.json({
      success: true,
      message: 'Printer ID nullified successfully.',
      count: countResult.count
    });

  } catch (error) {
    console.error('Error nullifying jobs:', error);
    res.status(500).json({
      error: 'Failed to nullify jobs',
      details: error.message
    });
  }
});

export default router;
