# 🚄 TrackGuard AI - Complete Railway Safety System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.3.1-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.3-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

## 📌 Overview

TrackGuard AI is a complete enterprise-ready railway safety management system that uses advanced AI and computer vision to detect obstacles, assess risks, and prevent train collisions. Built on the existing YOLO detection system, it provides real-time monitoring, analytics, and alert management for railway operations.

## ✨ Complete Feature Set

### 🎯 **AI-Powered Detection**
- **Real-time Obstacle Detection**: Advanced YOLO-based computer vision
- **Risk Assessment**: Dynamic risk scoring with collision prediction
- **Decision Engine**: AI-powered decision making (CLEAR, CAUTION, BRAKE)
- **Multi-Object Tracking**: Persistent tracking with confidence scoring

### 📊 **Analytics & Monitoring**
- **Live Dashboard**: Real-time KPIs and performance metrics
- **System Health**: Monitoring of AI engine, processing, and alerts
- **Risk Assessment**: Visual charts showing risk distribution
- **Historical Analytics**: Trend analysis and reporting

### 🚨 **Alert Management**
- **Multi-Level Alerts**: INFO, WARNING, CRITICAL, EMERGENCY
- **Real-time Notifications**: Pop-up alerts with sound notifications
- **Alert Acknowledgment**: User acknowledgment and escalation
- **Audit Trail**: Complete alert history and response tracking

### 🗺️ **GPS Mapping & Location**
- **Interactive Route Visualization**: Real-time train position tracking
- **Hazard Zone Mapping**: Risk-coded waypoints and danger areas
- **Location Services**: GPS coordinate tracking and route optimization
- **Geospatial Analytics**: Route statistics and hazard distribution

### 🔐 **User Authentication & Security**
- **Role-Based Access Control**: Operator, Supervisor, Admin roles
- **JWT Authentication**: Secure session management
- **Permission Management**: Granular access control
- **User Profiles**: Personal dashboards and activity logging

### 🏗️ **Enterprise Architecture**
- **Database Layer**: PostgreSQL with comprehensive schema
- **Caching**: Redis for real-time data and session management
- **API Gateway**: RESTful APIs with WebSocket support
- **Containerization**: Docker deployment with orchestration

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (for production)
- PostgreSQL 15+ (for production)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SaptarshiMondal123/TrackGuard_AI.git
   cd TrackGuard_AI
   ```

2. **Start the backend server**
   ```bash
   cd Backend
   python simple_server.py
   # Server will start at http://localhost:8000
   ```

3. **Install and start frontend**
   ```bash
   cd frontend1
   npm install
   npm run dev
   # Frontend will start at http://localhost:5173
   ```

4. **Access the application**
   - Open http://localhost:5173
   - Use demo credentials:
     - **Admin**: `admin` / `trackguard123`
     - **Supervisor**: `supervisor1` / `trackguard123`
     - **Operator**: `operator1` / `trackguard123`

### Production Deployment

1. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your production settings
   ```

2. **Deploy with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Initialize Database**
   ```bash
   docker-compose exec postgres psql -U trackguard -d trackguard_ai -f /docker-entrypoint-initdb.d/schema.sql
   ```

## 🏛️ Architecture

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   React TS      │◄──►│   FastAPI       │◄──►│   PostgreSQL    │
│   + Analytics   │    │   + WebSocket   │    │   + Redis       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Auth     │    │   AI Engine     │    │   File Storage  │
│   JWT + RBAC    │    │   YOLO Detection│    │   Videos/Models │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Database Schema
- **Users & Authentication**: Role-based access control
- **Video Processing**: Upload, processing status, results
- **Detection Results**: Frame-by-frame analysis data
- **Alerts & Notifications**: Multi-level alert management
- **GPS & Routes**: Location tracking and route management
- **Analytics**: System metrics and performance data

### Tech Stack
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Zustand
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL + Redis
- **AI/ML**: YOLO (Ultralytics) + OpenCV
- **Authentication**: JWT + bcrypt
- **Deployment**: Docker + Nginx
- **Monitoring**: Health checks + Audit logging

## 📱 User Interface

### Authentication System
- Secure login with role-based access
- User profile management with permissions
- Session persistence and logout functionality

### Main Dashboard
- **Video Upload**: Drag-and-drop with real-time processing
- **Analytics Dashboard**: KPIs, system status, recent alerts
- **GPS Mapping**: Interactive route visualization
- **Alert Manager**: Real-time notifications and testing

### Admin Features
- User management and role assignment
- System configuration and monitoring
- Audit logs and activity tracking
- Database management and backups

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trackguard_ai
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your_secure_jwt_secret
JWT_EXPIRATION=24h

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE=500MB

# AI Model Settings
YOLO_MODEL_PATH=/app/models/yolov8m-worldv2.pt
DETECTION_CONFIDENCE=0.40

# Alert Configuration
ALERT_SOUND_ENABLED=true
EMAIL_ALERTS_ENABLED=false
SMS_ALERTS_ENABLED=false
```

### Database Configuration
```sql
-- Core tables
users, user_sessions, permissions
videos, detection_results, detections
alerts, routes, route_points
analytics_summary, audit_log
```

## 🧪 Testing

### Demo Credentials
| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| Admin | `admin` | `trackguard123` | All permissions |
| Supervisor | `supervisor1` | `trackguard123` | Most features |
| Operator | `operator1` | `trackguard123` | Basic access |

### Testing Features
1. **Video Upload**: Upload sample railway videos
2. **Alert System**: Test emergency notifications
3. **GPS Tracking**: Monitor simulated train movement  
4. **Analytics**: View real-time system metrics
5. **User Roles**: Switch between different user types

## 🚀 API Documentation

### Core Endpoints
```
GET  /health              - Health check
GET  /analytics/summary   - System analytics
POST /upload-video/       - Video upload
GET  /video/{id}/results  - Processing results
WS   /ws                  - WebSocket connection
```

### Authentication Endpoints
```
POST /auth/login          - User login
POST /auth/logout         - User logout  
GET  /auth/me             - Current user info
POST /users/              - Create user (admin)
```

## 📈 Performance & Scalability

### Performance Optimizations
- **Frontend**: React optimization, code splitting, lazy loading
- **Backend**: Async processing, connection pooling, caching
- **Database**: Proper indexing, query optimization
- **AI Processing**: Batch processing, GPU acceleration ready

### Scalability Features
- **Horizontal Scaling**: Docker Compose orchestration
- **Load Balancing**: Nginx reverse proxy configuration
- **Caching Strategy**: Redis for session and real-time data
- **Database Sharding**: Ready for multi-tenant architecture

## 🛡️ Security

### Security Features
- **Authentication**: JWT tokens with expiration
- **Authorization**: Role-based access control (RBAC)
- **Input Validation**: Pydantic models and sanitization
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Content Security Policy headers
- **HTTPS**: SSL/TLS configuration ready

### Security Best Practices
- Password hashing with bcrypt
- Session timeout and refresh
- Audit logging for all activities
- Rate limiting on API endpoints
- File upload validation and scanning

## 🐳 Deployment

### Docker Deployment
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up -d

# Scaling
docker-compose up -d --scale backend=3
```

### Manual Deployment
1. **Database Setup**: PostgreSQL + Redis installation
2. **Backend Deployment**: Python environment + dependencies
3. **Frontend Build**: Static file generation and serving
4. **Reverse Proxy**: Nginx configuration and SSL

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **YOLO (Ultralytics)**: Object detection framework
- **React Community**: Frontend framework and ecosystem
- **FastAPI**: High-performance web framework
- **Railway Industry**: Domain expertise and requirements

---

**TrackGuard AI** - *Safety Beyond Sight — Powered by AI*

For questions or support, contact: [contact@trackguard.ai](mailto:contact@trackguard.ai)