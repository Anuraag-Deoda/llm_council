-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create HNSW index function for later use
-- This will be called after the tables are created by SQLAlchemy
-- HNSW provides fast approximate nearest neighbor search
