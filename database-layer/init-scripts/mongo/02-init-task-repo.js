// This script initializes the task repository database
db = db.getSiblingDB('task_repository');

// Create admin user for the task_repository database
db.createUser({
  user: 'task_service',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'task_repository' },
    { role: 'dbAdmin', db: 'task_repository' }
  ]
});

// Create tasks collection with validation schema
db.createCollection('tasks', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['_id', 'task_type', 'status', 'created_at'],
      properties: {
        _id: {
          bsonType: 'objectId',
          description: 'Unique identifier for the task'
        },
        task_id: {
          bsonType: 'string',
          description: 'Human-readable task identifier'
        },
        task_type: {
          bsonType: 'string',
          description: 'Type of task (e.g., "GENERATIVE", "ANALYSIS", "COMMUNICATION", "MARKETING")'
        },
        status: {
          enum: ['pending', 'processing', 'completed', 'failed', 'canceled'],
          description: 'Current status of the task'
        },
        priority: {
          bsonType: 'int',
          description: 'Priority level (1-10, lower is higher priority)'
        },
        created_at: {
          bsonType: 'date',
          description: 'Timestamp when the task was created'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Timestamp when the task was last updated'
        },
        processing_started_at: {
          bsonType: 'date',
          description: 'Timestamp when the task processing started'
        },
        completed_at: {
          bsonType: 'date',
          description: 'Timestamp when the task was completed'
        },
        processor_id: {
          bsonType: 'string',
          description: 'ID of the service instance processing the task'
        },
        batch_id: {
          bsonType: 'string',
          description: 'ID for grouping related tasks'
        },
        tenant_id: {
          bsonType: 'string',
          description: 'Tenant identifier for multi-tenant tasks'
        },
        request: {
          bsonType: 'object',
          description: 'Task request data'
        },
        template: {
          bsonType: 'object',
          description: 'Template data for the task'
        },
        results: {
          bsonType: 'object',
          description: 'Task results data'
        },
        error: {
          bsonType: 'string',
          description: 'Error message if the task failed'
        },
        tags: {
          bsonType: 'object',
          description: 'Task tags for categorization and filtering'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional metadata for the task'
        }
      }
    }
  }
});

// Create indexes for efficient querying
db.tasks.createIndex({ "status": 1, "task_type": 1, "created_at": 1 });
db.tasks.createIndex({ "processor_id": 1 });
db.tasks.createIndex({ "batch_id": 1 });
db.tasks.createIndex({ "tenant_id": 1 });
db.tasks.createIndex({ "created_at": 1 });
db.tasks.createIndex({ "priority": 1 });
db.tasks.createIndex({ "tags.service": 1 });
db.tasks.createIndex({ "tags.source": 1 });
db.tasks.createIndex({ "completed_at": 1 }, { expireAfterSeconds: 2592000 }); // 30 days TTL 