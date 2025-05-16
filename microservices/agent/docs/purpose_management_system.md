# Purpose Management System

## Overview

The Purpose Management System provides a centralized way to define, manage, and access purpose definitions for the Agent microservice. Purposes represent different user intentions that the system can recognize and respond to, each mapped to appropriate execution templates.

## Components

### 1. `purpose.py` (Domain Entity)

The Purpose entity represents the purpose concept in the domain model.

- **Location**: `src/domain/entities/purpose.py`
- **Primary Role**: Provides a structured representation of purpose data
- **Key Features**:
  - Defines purpose properties (ID, name, description, keywords, etc.)
  - Provides methods to convert to/from dictionaries
  - Includes utility methods for adding/removing keywords and template IDs

### 2. `purpose_mapping.json` (Configuration File)

This is the central configuration file containing all purpose definitions.

- **Location**: `src/config/purpose_mapping.json`
- **Primary Role**: Single source of truth for purpose data
- **Key Features**:
  - Defines purpose IDs and their properties
  - Contains keywords for NLP purpose detection
  - Maps purposes to template IDs
  - Can be manually updated without code changes

### 3. `purpose_repository.py` (Repository Interface)

Defines the standard interface for accessing purpose data.

- **Location**: `src/application/interfaces/purpose_repository.py`
- **Primary Role**: Defines a consistent API for accessing purposes
- **Key Features**:
  - Declares methods for retrieving, listing, and managing purposes
  - Uses Protocol for interface definition (structural typing)
  - Enables dependency injection and testing

### 4. `file_purpose_repository.py` (Repository Implementation)

Loads and converts purpose definitions from JSON to domain entities.

- **Location**: `src/infrastructure/repositories/file_purpose_repository.py`
- **Primary Role**: Reads purpose_mapping.json and provides structured access to purposes
- **Key Features**:
  - Loads data from the JSON file
  - Converts JSON data to Purpose domain entities
  - Reloads data on each request to always have fresh data
  - Read-only implementation (writes are done manually to the JSON file)

## Data Flow

```
                 ┌────────────────┐
Manual Edit ────►│                │
                 │purpose_mapping.│
                 │json            │
                 │                │
                 └────────┬───────┘
                          │ reads
                          ▼
┌─────────────────────────────────────┐
│                                     │
│      FilePurposeRepository          │
│                                     │
│  Loads and converts to Purpose      │
│  entities                           │
│                                     │
└─┬───────────────────────────────────┘
  │ injected into
  │
  ├─────────────────┬─────────────────┐
  │                 │                 │
  ▼                 ▼                 ▼
┌────────────┐ ┌──────────────┐ ┌────────────┐
│            │ │              │ │            │
│ NLPService │ │TemplateService│ │Other       │
│            │ │              │ │Services    │
│            │ │              │ │            │
└────────────┘ └──────────────┘ └────────────┘
     │                 │              │
     │                 │              │
     ▼                 ▼              ▼
┌──────────────────────────────────────────┐
│                                          │
│            Business Logic                │
│                                          │
└──────────────────────────────────────────┘
```

## How to Update Purpose Mappings

### Manual Updates to purpose_mapping.json

1. **Locate the File**:
   ```
   microservices/agent/src/config/purpose_mapping.json
   ```

2. **Edit the File**:
   - Add, modify, or remove purpose entries using any text editor
   - Follow the JSON structure format

3. **Format of a Purpose Entry**:
   ```json
   "unique.purpose.id": {
     "id": "SHORTCODE",
     "service_type": "GENERATIVE|ANALYSIS|COMMUNICATION",
     "template_id": "associated_template_id",
     "keywords": [
       "keyword phrase 1", 
       "keyword phrase 2",
       "important keyword:1.5"  // with importance weight
     ],
     "description": "Optional human-readable description"
   }
   ```

4. **Example of Adding a New Purpose**:
   ```json
   "email.draft.generation": {
     "id": "EDG001",
     "service_type": "GENERATIVE",
     "template_id": "email_draft_generator",
     "keywords": [
       "draft email",
       "write email",
       "compose message",
       "email draft"
     ],
     "description": "Generates draft emails based on user input"
   }
   ```

5. **Save the File**:
   - Changes take effect immediately (no need to restart the service)
   - The repository will reload the file on the next request

## Using Purpose Repository in Code

If you're developing a new service that needs to work with purposes:

1. **Add Repository Dependency**:
   ```python
   def __init__(self, purpose_repository: IPurposeRepository):
       self.purpose_repository = purpose_repository
   ```

2. **Get a Purpose by ID**:
   ```python
   purpose = await self.purpose_repository.get_purpose("email.draft.generation")
   if purpose:
       template_id = purpose.template_ids[0]  # Get first template ID
   ```

3. **List All Purposes**:
   ```python
   purposes = await self.purpose_repository.list_purposes()
   for purpose in purposes:
       print(f"Purpose: {purpose.name} ({purpose.id})")
   ```

4. **Find Purpose by Keywords**:
   ```python
   # Similar to the NLP service detection logic
   purposes = await self.purpose_repository.list_purposes()
   for purpose in purposes:
       if any(keyword in user_text.lower() for keyword in purpose.keywords):
           return purpose
   ```

5. **Wire in `main.py`**:
   ```python
   # Initialize repository
   purpose_repository = FilePurposeRepository()
   
   # Pass to your service
   your_service = YourService(purpose_repository=purpose_repository)
   ```

## Benefits

1. **Separation of Concerns**:
   - Clear separation between data (JSON), access (repository), and structure (entity)
   - Services don't need to know where/how purpose data is stored

2. **Easy Configuration**:
   - Purposes can be updated by editing a simple JSON file
   - No code changes or deployments needed for purpose updates

3. **Consistent Interface**:
   - All services use the same IPurposeRepository interface
   - Enables future changes to storage mechanism without affecting services

4. **Central Management**:
   - All purposes are defined in a single file for easy management
   - No duplication of purpose definitions across the codebase

5. **Immediate Updates**:
   - Changes to the JSON file take effect immediately
   - Repository reloads on each request to ensure latest data

## Example Purpose Map

Here's an example of a purpose mapping configuration:

```json
{
  "insta.post.generation": {
    "id": "IPG001",
    "service_type": "GENERATIVE",
    "template_id": "instagram_post_generator",
    "keywords": [
      "create instagram post", 
      "generate instagram post", 
      "instagram content",
      "make instagram post",
      "insta post"
    ]
  },
  "insta.post.analysis": {
    "id": "IPA001", 
    "service_type": "ANALYSIS",
    "template_id": "instagram_post_analyzer",
    "keywords": [
      "analyze instagram post", 
      "post performance", 
      "instagram analytics",
      "analyze post engagement",
      "post statistics"
    ]
  }
}
``` 