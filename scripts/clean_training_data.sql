-- Script to clean all training data
-- Run this to start fresh

-- Delete all training progress
DELETE FROM training_progress;

-- Delete all model versions
DELETE FROM model_versions;

-- Delete all training jobs
DELETE FROM training_jobs;

-- Delete all notifications
DELETE FROM notifications;

-- Reset sequences if needed
-- ALTER SEQUENCE IF EXISTS training_jobs_id_seq RESTART WITH 1;
-- ALTER SEQUENCE IF EXISTS model_versions_id_seq RESTART WITH 1;

-- Verify deletion
SELECT 'Training Jobs' as table_name, COUNT(*) as count FROM training_jobs
UNION ALL
SELECT 'Model Versions', COUNT(*) FROM model_versions
UNION ALL
SELECT 'Training Progress', COUNT(*) FROM training_progress
UNION ALL
SELECT 'Notifications', COUNT(*) FROM notifications;
