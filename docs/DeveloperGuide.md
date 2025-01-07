# Developer Guide

Welcome to the Developer Guide for this project. This document aims to outline the development processes, architecture details, and best practices to ensure efficient, secure, and maintainable code.

## Table of Contents
1. [Project Overview](#project-overview)
2. [MACH Architecture](#mach-architecture)
3. [Git Flow Strategy](#git-flow-strategy)
4. [Error Handling & Input Validation](#error-handling--input-validation)
5. [Security Considerations](#security-considerations)
6. [Testing Guidelines](#testing-guidelines)
7. [Docker Image Management](#docker-image-management)
8. [System Architecture Diagrams](#system-architecture-diagrams)

## Project Overview
This project follows a structured approach by adhering to the existing directory layout. We focus on writing code with clear docstrings and robust error handling, along with a disciplined approach to version control.

## MACH Architecture
MACH stands for:
- **Microservices-based**: Each part of the application is designed to be a separate service.
- **API-first**: All functionalities are exposed via APIs.
- **Cloud-native**: The application is architected and designed for cloud environments.
- **Headless**: The system's back-end services are decoupled from the front-end/UI components.

![MACH Architecture](./diagrams/mach_architecture.png)

## Git Flow Strategy
This repository uses the Git Flow branching model to manage development and releases. Below is the initialization step, which you can reproduce by running:

```bash
git flow init -f
```

During the initialization, you'll be prompted for several options. Here are the choices to make:

- **Branch name for production releases**: `main`
- **Branch name for "next release" development**: `develop`
- **Feature branch prefix**: `feature/`
- **Bugfix branch prefix**: `bugfix/`
- **Release branch prefix**: `release/`
- **Hotfix branch prefix**: `hotfix/`
- **Support branch prefix**: `support/`
- **Version tag prefix**: `v`

## Error Handling & Input Validation
- **Input Validation**: Validate all inputs from external sources to prevent injection attacks and data corruption.
- **Error Handling**: Use try/catch blocks or equivalent mechanisms to handle runtime errors gracefully.
- **Logging**: Log errors where they occur for better observability and debugging.

## Security Considerations
- **Sensitive Data Management**: Store and manage sensitive data securely using environment variables or secure key stores.
- **Dependency Updates**: Regularly update dependencies to mitigate known vulnerabilities.
- **Access Control**: Enforce least privilege for services and APIs.

![Security Architecture](./diagrams/security_architecture.png)

## Testing Guidelines
- **Unit Tests**: Write comprehensive unit tests for all functions and classes.
- **Integration Tests**: Include integration tests if the feature interacts with external systems.
- **Automation**: Automate tests via a CI/CD pipeline.

## Docker Image Management

To manage Docker images and ensure they are available on Docker Hub:

1. **Build the Image**:
   ```bash
   docker build -t monolith-app .
   ```

2. **Tag the Image**:
   ```bash
   docker tag monolith-app:latest atalrani/ai-saas-platform:latest
   docker tag analysis-base:latest atalrani/ai-saas-platform-analysis-base:latest
   ```

3. **Push the Image**:
   ```bash
   docker push atalrani/ai-saas-platform:latest
   docker push atalrani/ai-saas-platform-analysis-base:latest
   ```

![Microservices Deployment](./diagrams/microservices_deployment.png)

## System Architecture Diagrams

### Event Flow
The following diagram illustrates how events flow through our system using the event_manager.py:

![Event Flow](./diagrams/event_flow.png)

### CI/CD Pipeline
Our continuous integration and deployment pipeline:

![CI/CD Pipeline](./diagrams/ci_cd_pipeline.png)

## Concurrency, State, and Event Management
Our application handles concurrent operations by leveraging asyncio-based workers in the microservices/analysis-base/src/analysis_main.py. Within each microservice, a dedicated event management system (common/event_manager.py) tracks service state transitions and publishes relevant events to downstream services.

Key points:
- We use asyncio gather() methods for parallel I/O tasks
- Event subscription and publishing is handled by the event_manager.py
- Shared state is safely updated within a dedicated concurrency-aware data structure

## Docker and Kubernetes
Our microservices are containerized via Dockerfiles found in their respective directories. Environment variables for security tokens and production credentials are only injected in the production stage.

Kubernetes deployment uses:
- Individual Deployments per microservice
- Shared ConfigMap for environment-specific details
- Rolling updates for zero-downtime deployments

---
