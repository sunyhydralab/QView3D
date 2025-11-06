/**
 * Queue class for managing job queues per fabricator
 * Extends Array to provide deque-like operations
 */
export class Queue extends Array {
  constructor(fabricatorId, wsManager) {
    super();
    this.fabricatorId = fabricatorId;
    this.wsManager = wsManager;
  }

  /**
   * Add a job to the back of the queue
   * @param {Object} job - The job to add
   * @returns {boolean} - True if added, false if job already in queue
   */
  addToBack(job) {
    if (this.some(j => j.id === job.id)) {
      return false;
    }
    this.push(job);
    this.emitQueueUpdate();
    return true;
  }

  /**
   * Add a job to the front of the queue
   * @param {Object} job - The job to add
   * @returns {boolean} - True if added, false if job already in queue
   */
  addToFront(job) {
    if (this.some(j => j.id === job.id)) {
      return false;
    }

    // If first job is printing, insert at position 1
    if (this.length >= 1 && this[0].status === 'printing') {
      this.splice(1, 0, job);
    } else {
      this.unshift(job);
    }

    this.emitQueueUpdate();
    return true;
  }

  /**
   * Remove a job from the queue by ID
   * @param {number} jobId - The job ID to remove
   * @returns {Object|null} - The removed job or null if not found
   */
  deleteJob(jobId) {
    const index = this.findIndex(j => j.id === jobId);
    if (index === -1) {
      return null;
    }

    const deletedJob = this.splice(index, 1)[0];
    this.emitQueueUpdate();
    return deletedJob;
  }

  /**
   * Move a job up or down in the queue
   * @param {boolean} up - True to move up, false to move down
   * @param {number} jobId - The job ID to move
   */
  bump(up, jobId) {
    const index = this.findIndex(j => j.id === jobId);
    if (index === -1) {
      console.log('Job not found in queue.');
      return;
    }

    const job = this[index];
    this.splice(index, 1);

    if (up && index > 0) {
      this.splice(index - 1, 0, job);
    } else if (!up && index < this.length) {
      this.splice(index + 1, 0, job);
    } else {
      // Put it back if can't move
      this.splice(index, 0, job);
    }

    this.emitQueueUpdate();
  }

  /**
   * Move a job to the front or back of the queue
   * @param {boolean} front - True for front, false for back
   * @param {number} jobId - The job ID to move
   */
  bumpExtreme(front, jobId) {
    const index = this.findIndex(j => j.id === jobId);
    if (index === -1) {
      console.log('Job not found in queue.');
      return;
    }

    const job = this.splice(index, 1)[0];

    if (front) {
      // If first job is printing, insert at position 1
      if (this.length >= 1 && this[0].status === 'printing') {
        this.splice(1, 0, job);
      } else {
        this.unshift(job);
      }
    } else {
      this.push(job);
    }

    this.emitQueueUpdate();
  }

  /**
   * Reorder the queue based on an array of job IDs
   * @param {number[]} jobIds - Array of job IDs in desired order
   */
  reorder(jobIds) {
    const newQueue = [];

    for (const jobId of jobIds) {
      const job = this.find(j => j.id === jobId);
      if (job) {
        newQueue.push(job);
      }
    }

    // Clear and repopulate
    this.length = 0;
    this.push(...newQueue);

    this.emitQueueUpdate();
  }

  /**
   * Get the next job in the queue
   * @returns {Object|null} - The next job or null if queue is empty
   */
  getNext() {
    return this.length > 0 ? this[0] : null;
  }

  /**
   * Remove and return the first job from the queue
   * @returns {Object|null} - The removed job or null if queue is empty
   */
  removeJob() {
    if (this.length === 0) {
      return null;
    }
    const job = this.shift();
    this.emitQueueUpdate();
    return job;
  }

  /**
   * Check if a job exists in the queue
   * @param {number} jobId - The job ID to check
   * @returns {boolean} - True if job exists, false otherwise
   */
  jobExists(jobId) {
    return this.some(j => j.id === jobId);
  }

  /**
   * Get a job by ID
   * @param {number} jobId - The job ID to find
   * @returns {Object|null} - The job or null if not found
   */
  getJobById(jobId) {
    return this.find(j => j.id === jobId) || null;
  }

  /**
   * Set all jobs in the queue to 'inqueue' status
   */
  setToInQueue() {
    this.forEach(job => {
      job.status = 'inqueue';
    });
  }

  /**
   * Convert queue to JSON-serializable array
   * @returns {Array} - Array of job objects
   */
  toJSON() {
    return this.filter(j => j !== null);
  }

  /**
   * Emit WebSocket event for queue updates
   */
  emitQueueUpdate() {
    if (this.wsManager) {
      this.wsManager.broadcast({
        event: 'queue_update',
        data: {
          queue: this.toJSON(),
          fabricator_id: this.fabricatorId
        }
      });
    }
  }
}
