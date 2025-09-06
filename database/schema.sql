-- TrackGuard AI Database Schema
-- PostgreSQL Schema for Production Deployment

-- Create database
-- CREATE DATABASE trackguard_ai;

-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'Operator',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT valid_role CHECK (role IN ('Operator', 'Supervisor', 'Admin'))
);

-- User Sessions
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Permissions
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE user_permissions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, permission_id)
);

-- Video Processing
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_path TEXT,
    file_size BIGINT,
    duration FLOAT,
    fps FLOAT,
    resolution VARCHAR(20),
    uploaded_by INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'error'))
);

-- Detection Results
CREATE TABLE detection_results (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id) ON DELETE CASCADE,
    frame_number INTEGER NOT NULL,
    timestamp_ms FLOAT NOT NULL,
    overall_decision VARCHAR(20),
    overall_risk FLOAT,
    speed_kmph FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual Detections
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    result_id INTEGER REFERENCES detection_results(id) ON DELETE CASCADE,
    class_name VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x1 FLOAT NOT NULL,
    bbox_y1 FLOAT NOT NULL,
    bbox_x2 FLOAT NOT NULL,
    bbox_y2 FLOAT NOT NULL,
    distance FLOAT,
    ttc FLOAT, -- time to collision
    risk_score FLOAT,
    decision VARCHAR(20)
);

-- Alerts and Notifications
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    severity INTEGER DEFAULT 1,
    video_id INTEGER REFERENCES videos(id),
    detection_id INTEGER REFERENCES detections(id),
    location_lat FLOAT,
    location_lng FLOAT,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_alert_type CHECK (type IN ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY'))
);

-- GPS and Route Data
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE route_points (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    risk_level VARCHAR(10) DEFAULT 'low',
    alert_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_risk_level CHECK (risk_level IN ('low', 'medium', 'high'))
);

-- System Analytics
CREATE TABLE analytics_summary (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_videos_processed INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    average_risk_score FLOAT DEFAULT 0,
    alerts_count INTEGER DEFAULT 0,
    system_uptime_seconds BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- System Configuration
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_uploaded_by ON videos(uploaded_by);
CREATE INDEX idx_detection_results_video_id ON detection_results(video_id);
CREATE INDEX idx_detections_result_id ON detections(result_id);
CREATE INDEX idx_alerts_type ON alerts(type);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_route_points_route_id ON route_points(route_id);
CREATE INDEX idx_analytics_summary_date ON analytics_summary(date);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- Insert default permissions
INSERT INTO permissions (name, description) VALUES 
    ('view_videos', 'Can view uploaded videos and processing results'),
    ('upload_videos', 'Can upload new videos for processing'),
    ('view_analytics', 'Can access analytics dashboard'),
    ('manage_alerts', 'Can manage and acknowledge alerts'),
    ('view_gps', 'Can access GPS mapping features'),
    ('manage_users', 'Can manage user accounts and permissions'),
    ('system_config', 'Can modify system configuration'),
    ('view_audit', 'Can view audit logs');

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES 
    ('max_video_size_mb', '500', 'Maximum video file size in megabytes'),
    ('supported_video_formats', 'mp4,avi,mov,mkv', 'Comma-separated list of supported video formats'),
    ('detection_confidence_threshold', '0.40', 'Minimum confidence threshold for detections'),
    ('alert_sound_enabled', 'true', 'Enable sound alerts for critical situations'),
    ('websocket_enabled', 'true', 'Enable WebSocket for real-time updates'),
    ('gps_update_interval', '5000', 'GPS position update interval in milliseconds'),
    ('analytics_retention_days', '90', 'Number of days to retain analytics data');

-- Insert default route (from existing backend code)
INSERT INTO routes (name, description, is_active) VALUES 
    ('Main Railway Line', 'Primary railway route with TrackGuard monitoring', true);

-- Insert route points
INSERT INTO route_points (route_id, sequence_number, latitude, longitude, risk_level, alert_type) VALUES 
    (1, 1, 22.5726, 88.3639, 'low', NULL),
    (1, 2, 22.5742, 88.3658, 'low', NULL),
    (1, 3, 22.5760, 88.3676, 'medium', 'Track inspection needed'),
    (1, 4, 22.5775, 88.3695, 'low', NULL),
    (1, 5, 22.5790, 88.3714, 'high', 'Obstacle detected'),
    (1, 6, 22.5805, 88.3733, 'low', NULL);

-- Create a sample admin user (password: trackguard123)
-- Note: In production, use proper password hashing (bcrypt, etc.)
INSERT INTO users (username, email, password_hash, role) VALUES 
    ('admin', 'admin@trackguard.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBc.K9CPmwp9Uy', 'Admin'),
    ('supervisor1', 'supervisor@trackguard.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBc.K9CPmwp9Uy', 'Supervisor'),
    ('operator1', 'operator@trackguard.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBc.K9CPmwp9Uy', 'Operator');

-- Grant permissions based on roles
-- Admin gets all permissions
INSERT INTO user_permissions (user_id, permission_id) 
SELECT 1, id FROM permissions;

-- Supervisor gets most permissions except user management
INSERT INTO user_permissions (user_id, permission_id) 
SELECT 2, id FROM permissions WHERE name NOT IN ('manage_users', 'system_config', 'view_audit');

-- Operator gets basic permissions
INSERT INTO user_permissions (user_id, permission_id) 
SELECT 3, id FROM permissions WHERE name IN ('view_videos', 'view_analytics');