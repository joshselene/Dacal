// src/server.js
// Minimal Express server exposing a mock API endpoint for generation requests.
// In the final product replace this with the full authenticated API as described in the architecture.

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { Queue } = require('bullmq');
const { Job } = require('./models');
const logger = require('./utils/logger');

const app = express();
app.use(cors());
app.use(express.json());

// Initialise BullMQ queue (uses default Redis connection – for prototype we fall back to in‑memory via a mock).
const generationQueue = new Queue('generation', {
  connection: {
    host: process.env.REDIS_HOST || '127.0.0.1',
    port: process.env.REDIS_PORT || 6379
  }
});

// POST /api/generate – receives a natural‑language description and enqueues a job.
app.post('/api/generate', async (req, res) => {
  const { tutorId, classId, moduleId, projectName, description } = req.body;
  if (!tutorId || !projectName || !description) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // Create a project row (simplified).
  const project = await Project.create({
    tutorId,
    classId,
    moduleId,
    name: projectName,
    description,
    state: 'Draft'
  });

  // Enqueue background job.
  const job = await generationQueue.add('generateScene', {
    projectId: project.id,
    description
  });

  // Persist job metadata.
  await Job.create({
    id: job.id,
    projectId: project.id,
    status: 'Queued'
  });

  logger.info(`Enqueued generation job ${job.id} for project ${project.id}`);
  res.status(202).json({ jobId: job.id, projectId: project.id });
});

// GET /api/jobs/:id/status – simple polling endpoint for UI.
app.get('/api/jobs/:id/status', async (req, res) => {
  const jobRecord = await Job.findByPk(req.params.id);
  if (!jobRecord) return res.status(404).json({ error: 'Job not found' });
  res.json({ jobId: jobRecord.id, status: jobRecord.status, details: jobRecord.details || null });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => logger.info(`API server listening on port ${PORT}`));
