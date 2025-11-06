import express from 'express';
import database from '../database.js';

const router = express.Router();

// Get all issues
router.get('/getissues', async (req, res) => {
  try {
    const { category, status } = req.query;
    let query = 'SELECT * FROM issues WHERE 1=1';
    const params = [];

    if (category) {
      query += ' AND category = ?';
      params.push(category);
    }

    if (status) {
      query += ' AND status = ?';
      params.push(status);
    }

    query += ' ORDER BY created_at DESC';

    const issues = await database.all(query, params);
    res.json(issues);
  } catch (error) {
    console.error('Error getting issues:', error);
    res.status(500).json({ error: 'Failed to get issues', details: error.message });
  }
});

// Create new issue
router.post('/createissue', async (req, res) => {
  try {
    const { title, description, category, severity, fabricator_id, job_id } = req.body;

    const result = await database.run(
      'INSERT INTO issues (title, description, category, severity, fabricator_id, job_id) VALUES (?, ?, ?, ?, ?, ?)',
      [title, description || '', category || 'printer', severity || 'low', fabricator_id || null, job_id || null]
    );

    res.json({
      success: true,
      message: 'Issue created successfully',
      id: result.id
    });
  } catch (error) {
    console.error('Error creating issue:', error);
    res.status(500).json({ error: 'Failed to create issue', details: error.message });
  }
});

// Update issue
router.post('/updateissue', async (req, res) => {
  try {
    const { id, title, description, severity, status, category } = req.body;

    const issue = await database.get('SELECT id FROM issues WHERE id = ?', [id]);

    if (!issue) {
      return res.status(404).json({ error: 'Issue not found' });
    }

    await database.run(
      'UPDATE issues SET title = ?, description = ?, severity = ?, status = ?, category = ? WHERE id = ?',
      [title, description, severity, status, category, id]
    );

    res.json({ success: true, message: 'Issue updated successfully' });
  } catch (error) {
    console.error('Error updating issue:', error);
    res.status(500).json({ error: 'Failed to update issue', details: error.message });
  }
});

// Delete issue
router.post('/deleteissue', async (req, res) => {
  try {
    const { id } = req.body;

    const issue = await database.get('SELECT id FROM issues WHERE id = ?', [id]);

    if (!issue) {
      return res.status(404).json({ error: 'Issue not found' });
    }

    // Remove issue references from jobs
    await database.run('UPDATE jobs SET issue_id = NULL WHERE issue_id = ?', [id]);

    // Delete issue
    await database.run('DELETE FROM issues WHERE id = ?', [id]);

    res.json({ success: true, message: 'Issue deleted successfully' });
  } catch (error) {
    console.error('Error deleting issue:', error);
    res.status(500).json({ error: 'Failed to delete issue', details: error.message });
  }
});

// Get issue by ID
router.get('/getissue', async (req, res) => {
  try {
    const { id } = req.query;

    const issue = await database.get('SELECT * FROM issues WHERE id = ?', [id]);

    if (!issue) {
      return res.status(404).json({ error: 'Issue not found' });
    }

    res.json(issue);
  } catch (error) {
    console.error('Error getting issue:', error);
    res.status(500).json({ error: 'Failed to get issue', details: error.message });
  }
});

// Resolve issue
router.post('/resolveissue', async (req, res) => {
  try {
    const { id } = req.body;

    const issue = await database.get('SELECT id FROM issues WHERE id = ?', [id]);

    if (!issue) {
      return res.status(404).json({ error: 'Issue not found' });
    }

    await database.run(
      'UPDATE issues SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?',
      ['resolved', id]
    );

    res.json({ success: true, message: 'Issue resolved successfully' });
  } catch (error) {
    console.error('Error resolving issue:', error);
    res.status(500).json({ error: 'Failed to resolve issue', details: error.message });
  }
});

// Get issues by category
router.get('/getissuesbycategory', async (req, res) => {
  try {
    const { category } = req.query;

    if (!category || !['printer', 'job', 'software'].includes(category)) {
      return res.status(400).json({ error: 'Invalid category. Must be printer, job, or software' });
    }

    const issues = await database.all(
      'SELECT * FROM issues WHERE category = ? ORDER BY created_at DESC',
      [category]
    );

    res.json(issues);
  } catch (error) {
    console.error('Error getting issues by category:', error);
    res.status(500).json({ error: 'Failed to get issues', details: error.message });
  }
});

export default router;
