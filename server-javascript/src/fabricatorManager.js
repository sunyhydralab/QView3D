/**
 * FabricatorManager - Manages queues and state for all registered fabricators
 */
import { Queue } from './queue.js';
import database from './database.js';
import wsManager from './websocket.js';

class FabricatorManager {
  constructor() {
    // Map of fabricatorId -> Queue
    this.queues = new Map();

    // Map of fabricatorId -> Printer instance
    this.activePrinters = new Map();

    // Job processor interval
    this.processorInterval = null;

    // Processing state
    this.isProcessing = false;
  }

  /**
   * Initialize the manager by loading all fabricators and their jobs from the database
   */
  async initialize() {
    try {
      const fabricators = await database.all('SELECT * FROM fabricators ORDER BY position ASC');

      for (const fabricator of fabricators) {
        // Create queue for each fabricator
        const queue = new Queue(fabricator.id, wsManager);
        this.queues.set(fabricator.id, queue);

        // Load jobs for this fabricator
        const jobs = await database.all(
          'SELECT * FROM jobs WHERE fabricator_id = ? AND status IN (?, ?) ORDER BY id ASC',
          [fabricator.id, 'inqueue', 'printing']
        );

        // Add jobs to queue
        for (const job of jobs) {
          queue.push(job);
        }

        console.log(`Initialized queue for fabricator ${fabricator.id} with ${jobs.length} jobs`);
      }

      // Start job processor
      this.startProcessor();

      console.log('FabricatorManager initialized successfully');
    } catch (error) {
      console.error('Failed to initialize FabricatorManager:', error);
      throw error;
    }
  }

  /**
   * Get queue for a fabricator
   * @param {number} fabricatorId - The fabricator ID
   * @returns {Queue|null} - The queue or null if not found
   */
  getQueue(fabricatorId) {
    return this.queues.get(fabricatorId) || null;
  }

  /**
   * Create queue for a new fabricator
   * @param {number} fabricatorId - The fabricator ID
   */
  createQueue(fabricatorId) {
    if (!this.queues.has(fabricatorId)) {
      const queue = new Queue(fabricatorId, wsManager);
      this.queues.set(fabricatorId, queue);
      console.log(`Created queue for fabricator ${fabricatorId}`);
    }
  }

  /**
   * Remove queue for a deleted fabricator
   * @param {number} fabricatorId - The fabricator ID
   */
  removeQueue(fabricatorId) {
    if (this.queues.has(fabricatorId)) {
      this.queues.delete(fabricatorId);
      console.log(`Removed queue for fabricator ${fabricatorId}`);
    }
  }

  /**
   * Add job to fabricator queue
   * @param {number} fabricatorId - The fabricator ID
   * @param {Object} job - The job to add
   * @param {boolean} toFront - Whether to add to front of queue
   * @returns {boolean} - True if added successfully
   */
  addJobToQueue(fabricatorId, job, toFront = false) {
    const queue = this.getQueue(fabricatorId);
    if (!queue) {
      console.error(`Queue not found for fabricator ${fabricatorId}`);
      return false;
    }

    if (toFront) {
      return queue.addToFront(job);
    } else {
      return queue.addToBack(job);
    }
  }

  /**
   * Remove job from queue
   * @param {number} fabricatorId - The fabricator ID
   * @param {number} jobId - The job ID
   * @returns {Object|null} - The removed job or null
   */
  removeJobFromQueue(fabricatorId, jobId) {
    const queue = this.getQueue(fabricatorId);
    if (!queue) {
      return null;
    }
    return queue.deleteJob(jobId);
  }

  /**
   * Start the job processor event loop
   */
  startProcessor() {
    if (this.processorInterval) {
      console.log('Job processor already running');
      return;
    }

    console.log('Starting job processor...');

    // Process jobs every 2 seconds
    this.processorInterval = setInterval(() => {
      this.processJobs();
    }, 2000);
  }

  /**
   * Stop the job processor
   */
  stopProcessor() {
    if (this.processorInterval) {
      clearInterval(this.processorInterval);
      this.processorInterval = null;
      console.log('Job processor stopped');
    }
  }

  /**
   * Process jobs from all fabricator queues
   */
  async processJobs() {
    if (this.isProcessing) {
      return; // Skip if already processing
    }

    this.isProcessing = true;

    try {
      // Get all fabricators
      const fabricators = await database.all('SELECT * FROM fabricators');

      for (const fabricator of fabricators) {
        const queue = this.getQueue(fabricator.id);

        if (!queue || queue.length === 0) {
          continue;
        }

        const nextJob = queue.getNext();

        if (!nextJob) {
          continue;
        }

        // Check fabricator status
        if (fabricator.status === 'ready' && nextJob.status === 'inqueue') {
          // Start the job
          await this.startJob(fabricator.id, nextJob);
        } else if (nextJob.status === 'complete' || nextJob.status === 'cancelled' || nextJob.status === 'error') {
          // Remove completed/cancelled/error jobs from queue
          queue.removeJob();

          // Update fabricator status to ready if it was printing
          if (fabricator.status === 'printing') {
            await database.run('UPDATE fabricators SET status = ? WHERE id = ?', ['ready', fabricator.id]);
            wsManager.broadcast({
              event: 'status_update',
              data: {
                fabricator_id: fabricator.id,
                status: 'ready'
              }
            });
          }
        }
      }
    } catch (error) {
      console.error('Error in job processor:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Start a job on a fabricator
   * @param {number} fabricatorId - The fabricator ID
   * @param {Object} job - The job to start
   */
  async startJob(fabricatorId, job) {
    try {
      console.log(`Starting job ${job.id} on fabricator ${fabricatorId}`);

      // Update job status to printing
      await database.run('UPDATE jobs SET status = ? WHERE id = ?', ['printing', job.id]);
      job.status = 'printing';

      // Update fabricator status to printing
      await database.run('UPDATE fabricators SET status = ? WHERE id = ?', ['printing', fabricatorId]);

      // Emit status updates
      wsManager.broadcast({
        event: 'status_update',
        data: {
          fabricator_id: fabricatorId,
          status: 'printing',
          job_id: job.id
        }
      });

      wsManager.broadcast({
        event: 'job_started',
        data: {
          fabricator_id: fabricatorId,
          job_id: job.id,
          job_name: job.name
        }
      });

      // TODO: Integrate with actual printer/serial communication here
      // For now, this is just a stub that updates the database

    } catch (error) {
      console.error(`Failed to start job ${job.id}:`, error);

      // Update job status to error
      await database.run('UPDATE jobs SET status = ? WHERE id = ?', ['error', job.id]);

      wsManager.broadcast({
        event: 'job_error',
        data: {
          fabricator_id: fabricatorId,
          job_id: job.id,
          error: error.message
        }
      });
    }
  }

  /**
   * Get all queues as JSON
   * @returns {Object} - Map of fabricatorId -> queue JSON
   */
  getAllQueuesJSON() {
    const result = {};
    for (const [fabricatorId, queue] of this.queues.entries()) {
      result[fabricatorId] = queue.toJSON();
    }
    return result;
  }
}

// Export singleton instance
const fabricatorManager = new FabricatorManager();
export default fabricatorManager;
