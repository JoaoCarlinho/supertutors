-- PostgreSQL initialization script for SuperTutors
-- Creates both dev and production database names for flexibility

-- Create the production database name (if it doesn't exist)
SELECT 'CREATE DATABASE supertutors'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'supertutors')\gexec

-- Grant all privileges to the supertutors user
GRANT ALL PRIVILEGES ON DATABASE supertutors TO supertutors;
GRANT ALL PRIVILEGES ON DATABASE supertutors_dev TO supertutors;
