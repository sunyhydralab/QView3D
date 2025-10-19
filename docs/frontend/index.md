# Frontend Documentation

Welcome to the QView3D frontend documentation. This documentation covers the Vue 3-based client application that provides a modern, responsive interface for managing 3D printers and print jobs.

## Technology Stack

The frontend is built with modern web technologies:

### Core Framework
- **Vue 3** - Progressive JavaScript framework using the Composition API
- **TypeScript** - Type-safe JavaScript with enhanced developer experience
- **Vite** - Fast build tool and development server

### Styling
- **Tailwind CSS** - Utility-first CSS framework for rapid UI development
- **Custom CSS Variables** - Theme-based color system with dark mode support
- **FontAwesome** - Icon library for consistent iconography

### State Management
- **Reactive Refs** - Vue 3's reactivity system for local state management
- **Computed Properties** - Derived state computed from reactive sources
- **Global State** - Shared reactive state using module-level refs (fabricator list, toast notifications)

### Utilities
- **VueUse** - Collection of essential Vue composition utilities
- **Socket.io Client** - Real-time bidirectional communication with the backend
- **Vue Router** - Official routing library for navigation

### Development Tools
- **ESLint** - Code linting and style enforcement
- **Prettier** - Code formatting
- **TypeScript Compiler** - Type checking
- **Vitest** - Unit testing framework
- **Playwright** - End-to-end testing

## Architecture Overview

The frontend follows a component-based architecture with clear separation of concerns:

### Component Structure
```
client/src/
├── components/          # Reusable UI components
│   ├── base/           # Base/foundational components
│   ├── *Issues.vue     # Issue tracking components
│   └── *.vue           # Feature-specific components
├── views/              # Page-level components (routes)
├── composables/        # Reusable composition functions
├── models/             # Data models and API interfaces
└── services/           # External service integrations
```

### Key Principles

1. **Composition API First** - All components use Vue 3's Composition API with `<script setup>` syntax for better code organization and TypeScript support.

2. **Base Components** - Reusable foundational components (BaseCard, BaseBadge, BaseStatCard, BaseEmptyState) ensure consistency across the UI.

3. **Composables** - Business logic and utilities are extracted into composables for reusability and testability.

4. **Type Safety** - TypeScript interfaces define data structures, props, and emits for compile-time safety.

5. **Reactive State** - State is managed using Vue's reactivity system with refs and computed properties.

## Features

- **Real-time Updates** - WebSocket integration provides live updates for printer status, job progress, and system events
- **Dark Mode** - Full dark mode support with theme persistence
- **Responsive Design** - Mobile-first design that works on all screen sizes
- **Issue Tracking** - Built-in issue management for printers, jobs, and software
- **GCode Preview** - Visual preview of GCode files with layer-by-layer rendering
- **Job Queue Management** - Manage print queues across multiple fabricators
- **Settings Panel** - Configure API endpoints and debug options

## Documentation Sections

- [Component Structure](components.md) - Detailed documentation of UI components
- [Composables](composables.md) - Reusable composition functions and utilities
- [State Management](state.md) - How state is managed across the application

## Getting Started

### Installation

```bash
cd client
npm install
```

### Development

```bash
npm run dev
```

The development server will start at `http://localhost:5173` (or another available port).

### Building for Production

```bash
npm run build
```

### Type Checking

```bash
npm run type-check
```

### Linting and Formatting

```bash
npm run lint
npm run format
```

## Project Structure

### Components
Components are organized by functionality:
- `base/` - Foundational components used throughout the app
- Root level - Feature-specific components (Navbar, Toast, etc.)
- Issue components - PrinterIssues, JobIssues, SoftwareIssues, IssueModal

### Views
Page-level components that correspond to routes:
- `Dashboard.vue` - Main printer status dashboard
- `Queues.vue` - Job queue management
- `Issues.vue` - Issue tracking interface
- `JobHistory.vue` - Historical job data
- `Registration.vue` - Printer registration
- `EmulatorView.vue` - Printer emulator for testing

### Composables
Reusable composition functions:
- `useFormatting.ts` - Date, time, file size, and number formatting
- `useSeverity.ts` - Issue severity levels and styling
- `useIPSettings.ts` - API configuration management
- `useWebSockets.ts` - WebSocket connection and event handling
- `useMode.ts` - Dark mode management

### Models
Data models and API interfaces:
- `fabricator.ts` - Printer/fabricator data model and state
- `job.ts` - Print job data model
- `api.ts` - API client configuration

## Configuration

### API Configuration
The application uses localStorage to persist API settings:
- `apiIPAddress` - Backend server IP (default: "localhost")
- `apiPort` - Backend server port (default: "8000")
- `debugMode` - Enable debug logging (default: false)

### Theme Configuration
Theme preferences are stored in localStorage:
- `theme` - "light" or "dark"

## Contributing

When adding new features:
1. Create base components for reusable UI elements
2. Use composables for shared business logic
3. Follow TypeScript conventions with proper interfaces
4. Maintain responsive design principles
5. Support dark mode in all new components
6. Add appropriate error handling and loading states
