![QView3D Logo](assets/QView3Dlogo.png)

# QView3D

## Overview

QView3D, developed at SUNY's Hydra Lab, is an open-source software project designed to streamline the management and communication of 3D printing files to printer arrays. It offers users an expandable framework to enhance their workflow and take control of their process. Embracing an open community ethos, QView3D continuously evolves, actively seeking collaboration and feedback from users to improve and innovate.

The project is maintained by computer science students at SUNY New Paltz, under the guidance of Professor Michael Curry. Team members are responsible for the development, testing, and documentation of the software. The project is part of the Computer Science Department's capstone course, where students work on real-world projects to gain experience in software development.

## Lab Development Team

- [**Michael Curry**](https://github.com/currymike123)
- [**Lars Palombi**](https://github.com/Lars-Codes)
- [**Jack Gusler**](https://github.com/jackgusler)
- [**Olamide Kumapayi**](https://github.com/olakuma)
- [**Nathan Gopee**](https://github.com/ndg8743)
- [**Ari Yeger**](https://github.com/L10nhunter)
- [**CJ Jenks**](https://github.com/iron768)
- [**Stiviyan Dragiev**](https://github.com/dragiev1)
- [**Christopher Jamieson**](https://github.com/shift16)
- [**Matthew Toro**](https://github.com/Matt0108/)

## Features

- **Concurrent Communication**: Manage multiple 3D printers simultaneously.
- **Job Management**:
  - Local storage of database.
  - Load balancing to distribute jobs across multiple printers.
  - Storage management for purging old files while retaining essential data.
  - Job prioritization and favoring.
  - Comprehensive job filtering and history tracking.
  - Initiate printer pauses and filament color changes.
  - Supports various printer models.
- **Error Logging**: Assign comments and track issues for past jobs to analyze job success and error rates.
- **Advanced Viewing**:
  - Real-time 3D model previews before and during printing.
  - Layer-by-layer virtual print monitoring via GCode Viewer.
- **Virtual Printer Emulator**: A Go-based emulator to simulate printer behavior, enabling testing without physical hardware.
- **Cross-Platform Compatibility**: Runs on Windows, macOS, and Linux, ensuring accessibility across systems.

## Technologies

- **Frontend**: Vue.js with Bootstrap for styling.
- **Backend**: Flask integrated with SQLite, handling data through Node.js.
- **Communication**: Serial communication via PySerial.
- **Database**: SQLite.
- **Testing**: Virtual printer emulator built in Go for G-code simulation and testing.

## Architecture Diagram

![QView3D Diagram](assets/QViewDiagram.png)

## Setup and Installation

The software is currently designed to run on Ubuntu 20.04 LTS and later. MacOS and Windows are supported; but Windows compatibility is still being worked on, and works with npm run start.

Clone the repository:

```sh
git clone https://github.com/sunyhydralab/QView3D.git
```

Enter the project directory.

```sh
cd QView3D
``` 

## Development Setup

QView3D uses GNU Make for project setup and development.
Project settings such as IP addresses, ports, and database configuration are stored in `.env`.
If `.env` does not exist, it is created from `.env.example`.
### Other Make Commands

```bash
make setup
make build
make reset-db
make fresh-dev
make clean
make check-serial 
```

### Start the development environment

```bash
make dev
```
## Production
start production 
```bash
make production
```

Check serial-port permissions:

```bash
make check-serial

Production builds the Vue/Vite frontend into static files, serves them with Nginx, and runs the Flask backend with Gunicorn.


### Production prerequisites

On Ubuntu, install Nginx:

```bash
sudo apt update
sudo apt install nginx
```

## Pull Requests

We welcome contributions to QView3D. Please follow the guidelines in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Version

1.0.0
