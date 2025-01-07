# Project README

Welcome to this multi-service Python project! This repository includes a monolith application as well as microservices, each designed to perform different tasks within the overall system architecture. Below is a concise guide to help you get started with building, running, and contributing to the project.

---

## Table of Contents
1. [Overview](#overview)  
2. [Architecture](#architecture)  
3. [Prerequisites](#prerequisites)  
4. [Installation](#installation)  
5. [Usage](#usage)  
6. [Project Structure](#project-structure)  
7. [Contributing](#contributing)  
8. [License](#license)

---

## Overview
This project consists of:
- A set of microservices (e.g. the “analysis-base” service) built using Python (FastAPI, Uvicorn, etc.).  
- A “monolith” application demonstrating a more traditional single-application approach.  
- Shared libraries and requirements, making it easy to maintain consistent dependencies across services.

### New Microservices
- **communication-base**: Handles communication tasks and integrates with external APIs.
- **agent**: Manages agent-related functionalities and processes.
- **chatbot**: Provides chatbot capabilities for user interaction.
- **customer-support-bot**: Offers customer support functionalities.
- **expert-bots**: Hosts expert systems and AI-driven bots.
- **mlops-pipeline**: Manages MLOps workflows and pipelines.
- **management_systems**: Oversees management and administrative tasks.
- **generative-base**: Focuses on generative AI models and tasks.
- **marketing-base**: Supports marketing operations and analytics.

Each microservice is containerized using Docker and can be built and run independently.

The main goal is to showcase a modular, scalable approach using Docker and Docker Compose.

---

## Architecture
1. **Monolith**  
   - A single Python application (in “monolith/”) for users who prefer a simpler setup.
2. **Microservices**  
   - “analysis-base/” runs Uvicorn on port 8100 (by default) to handle data analysis tasks.  
3. **Docker Compose**  
   - A “docker-compose.yml” file orchestrates multiple containers for development or production.

Additionally, see the “Architectural_document.txt” file for more technical details about how the services communicate.

---

## Prerequisites
- Docker & Docker Compose installed  
- Python 3.10+ (if you prefer to run the applications locally instead of using Docker)

---

## Installation

### Docker-Based Installation
1. Clone this repository.  
2. From the root of the repository, run:
```bash
docker-compose build
docker-compose up
```
This will build and start the containers (including the “analysis-base” service and any other defined services) in detached mode.

### Local Python Installation
If you prefer, you can run the microservices locally:
1. Clone this repository.  
2. Navigate to the microservice folder:
   ```bash
   cd microservices/analysis-base
   ```
3. Install dependencies:
   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```
4. Start the service:
   ```bash
   uvicorn src.analysis_main:app --host 0.0.0.0 --port 8100
   ```
5. (Optional) Spin up other services or the monolith as needed.

---

## Usage
- By default, the “analysis-base” microservice listens on port 8100.  
- You can send requests to the endpoint (e.g., `http://localhost:8100/`) depending on your API design in `analysis_main.py`.
- The monolith can be run similarly, either via Docker or Python scripts, depending on your workflow.

---

## Project Structure
Below is a simplified overview of the repository:
```
.
├─ monolith/
│  ├─ main.py
│  └─ ...
├─ microservices/
│  ├─ analysis-base/
│  │  ├─ Dockerfile
│  │  ├─ requirements.txt
│  │  └─ src/
│  │     └─ analysis_main.py
│  └─ ...
├─ docker-compose.yml
├─ requirements.txt
├─ .gitignore
├─ Architectural_document.txt
└─ ...
```
- **analysis-base/src/** contains your FastAPI application code for analysis tasks.  
- **monolith/main.py** has the simpler, single-process approach.  
- **docker-compose.yml** orchestrates multi-container setups.

---

## Contributing
1. Fork the repository, then clone your fork for local development.  
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).  
3. Commit your changes (`git commit -m 'Add fantastic feature'`).  
4. Push to the branch (`git push origin feature/AmazingFeature`).  
5. Create a new Pull Request.

---

## License
This project is licensed under an open-source license (e.g., MIT or Apache 2.0). See the [LICENSE](LICENSE) file for details.

---

**Thank you for using this project!** If you have any questions or suggestions, feel free to open an issue or pull request. Happy coding! 