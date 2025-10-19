# QView3D Project Documentation

Welcome to the documentation for the QView3D project.

## Overview

QView3D is a web-based platform for managing 3D printer arrays with intelligent backend routing.
The system uses a hybrid architecture with dual backends and automatic fallback capabilities.

## Architecture

- **Frontend**: Vue 3 with Composition API and TailwindCSS
- **Middleware**: Express.js intelligent router (port 3500)
- **Python Backend**: Flask with SQLAlchemy for database operations (port 8000)
- **JavaScript Backend**: Node.js for serial communication and real-time control (port 3000)
- **WebSocket**: Dual WebSocket servers for real-time updates (ports 8001, 3001)

## Backend Modes

The system can run in three modes:
- **Python**: Traditional Flask backend only
- **JavaScript**: Node.js backend for serial communication
- **Hybrid** (default): Both backends with intelligent middleware routing

## Contents

- [Architecture](ARCHITECTURE.md)
- [Setup Guide](SETUP.md)
- [Server-Python Documentation](server/index.md)
- [Server-JavaScript Documentation](server-javascript/index.md)
- [Frontend Documentation](frontend/index.md)
