-- Initial database setup script for SkillMap Nepal
-- Run this script to create the database and enable pgvector extension

-- Create database
CREATE DATABASE skillmap_db;

-- Create user
CREATE USER skillmap_user WITH PASSWORD 'skillmap_pass';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE skillmap_db TO skillmap_user;

-- Configure user settings
ALTER ROLE skillmap_user SET client_encoding TO 'utf8';
ALTER ROLE skillmap_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE skillmap_user SET timezone TO 'Asia/Kathmandu';

-- Connect to the database
\c skillmap_db

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO skillmap_user;

-- Verify pgvector installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Success message
\echo 'Database setup complete!'
\echo 'Database: skillmap_db'
\echo 'User: skillmap_user'
\echo 'pgvector extension: enabled'
\echo ''
\echo 'Next steps:'
\echo '1. Update .env file with database credentials'
\echo '2. Run: python manage.py migrate'
\echo '3. Run: python manage.py createsuperuser'
