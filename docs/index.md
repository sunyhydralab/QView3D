# QView3D Project Documentation

Welcome to the documentation for the QView3D project.

## Overview

QView3D is a web-based platform for managing 3D printer arrays with flexible backend routing.
The system uses a multi-backend architecture with middleware-based proxy routing.

## Architecture

- **Frontend**: Vue 3 with Composition API and TailwindCSS
- **Middleware**: Express.js intelligent router (port 3500)
- **Python Backend**: Flask with SQLAlchemy for database operations (port 8000)
- **JavaScript Backend**: Node.js for serial communication and real-time control (port 3000)
- **WebSocket**: Dual WebSocket servers for real-time updates (ports 8001, 3001)

## Backend Modes

The system can run in two modes:
- **Python**: Traditional Flask backend
- **JavaScript**: Node.js backend for serial communication

The middleware proxies all requests to the configured backend based on the selected mode.

## Contents

- [Architecture](ARCHITECTURE.md)
- [Setup Guide](SETUP.md)
- [Server-Python Documentation](server/index.md)
- [Server-JavaScript Documentation](server-javascript/index.md)
- [Frontend Documentation](frontend/index.md)
