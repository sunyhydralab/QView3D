import express from 'express';
import database from '../database.js';

const router = express.Router();

// Get all issues
router.get('/getissues', async (req, res) => {
  try {
    const issues = await database.all('SELECT * FROM issues ORDER BY created_at DESC');
    res.json(issues);
  } catch (error) {
    console.error('Error getting issues:', error);
    res.status(500).json({ error: 'Failed to get issues', details: error.message });
  }
});

// Create new issue
router.post('/createissue', async (req, res) => {
  try {
    const { title, description, severity } = req.body;

    const result = await database.run(
      'INSERT INTO issues (title, description, severity) VALUES (?, ?, ?)',
      [title, description || '', severity || 'low']
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
    const { id, title, description, severity } = req.body;

    const issue = await database.get('SELECT id FROM issues WHERE id = ?', [id]);

    if (!issue) {
      return res.status(404).json({ error: 'Issue not found' });
    }

    await database.run(
      'UPDATE issues SET title = ?, description = ?, severity = ? WHERE id = ?',
      [title, description, severity, id]
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

export default router;
