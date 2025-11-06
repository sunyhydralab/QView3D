# QView3D Frontend Client

Vue 3 + TypeScript + Vite frontend application for QView3D printer management system.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Development Workflow

### Hot Module Replacement (HMR) Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant FS as File System
    participant Vite as Vite Server<br/>Port 5173
    participant Browser as Browser<br/>localhost:8002
    participant MW as Middleware<br/>Port 8002

    Dev->>FS: Edit Vue Component
    FS->>Vite: File change detected
    Vite->>Vite: Recompile module
    Vite->>Browser: HMR Update via WebSocket
    Browser->>Browser: Apply changes without reload
    Browser->>Browser: Preserve component state

    Note over Dev,Browser: Total Time: < 100ms

    alt Component has errors
        Vite->>Browser: Show error overlay
        Browser->>Dev: Display compile error
    end
```

### Build and Deployment Flow

```mermaid
flowchart LR
    Dev[Developer] -->|npm run dev| ViteDev[Vite Dev Mode<br/>HMR Enabled]
    Dev -->|npm run build| Build[Production Build]

    ViteDev --> Compile[On-demand<br/>Compilation]
    Compile --> Serve[Serve via<br/>Middleware]

    Build --> TypeCheck[Type Check<br/>vue-tsc]
    TypeCheck --> Bundle[Bundle Assets<br/>Optimize]
    Bundle --> Output[dist/ Directory]
    Output --> Deploy[Deploy to<br/>Production]

    style ViteDev fill:#ffd700
    style Build fill:#90ee90
    style Deploy fill:#4169e1
```

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
npm run test:unit
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## Frontend Architecture

### Component Structure

```mermaid
flowchart TB
    App[App.vue<br/>Root Component]

    subgraph Views[Main Views]
        Dashboard[Dashboard.vue]
        Jobs[JobHistory.vue]
        Queue[Queues.vue]
        Registration[Registration.vue]
        Issues[Issues.vue]
        Emulator[EmulatorView.vue]
    end

    subgraph Components[Shared Components]
        JobTable[JobHistoryTable.vue]
        QueueList[QueueList.vue]
        FabCard[RegisteredFabricatorCard.vue]
        GCodeViewer[GCodePreview.vue]
        IssueModal[IssueModal.vue]
        Toast[Toast.vue]
        Navbar[Navbar.vue]
    end

    subgraph Services[Services & Composables]
        API[API Service<br/>Fetch Wrapper]
        WS[WebSocket Service<br/>Socket.IO Client]
        Store[Pinia Stores<br/>State Management]
    end

    App --> Views
    Views --> Components
    Components --> Services

    API -->|HTTP| Backend[Backend API<br/>via Middleware]
    WS -->|WebSocket| Backend

    style App fill:#42b883
    style Views fill:#ffd700
    style Components fill:#90ee90
    style Services fill:#4169e1
```
