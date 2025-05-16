// Initialize MongoDB for Agent Microservice
// This script runs when the MongoDB container starts for the first time

// Connect to the agent_context database
db = db.getSiblingDB('agent_context');

// Create collections
db.createCollection('contexts');
db.createCollection('batch_contexts');
db.createCollection('context_references');

// Create indexes for the contexts collection
db.contexts.createIndex({ "status": 1 }, { background: true });
db.contexts.createIndex({ "request.user_id": 1 }, { background: true });
db.contexts.createIndex({ "request.purpose_id": 1 }, { background: true });
db.contexts.createIndex({ "created_at": 1 }, { background: true });

// Create TTL index for completed contexts (auto-delete after 24 hours)
db.contexts.createIndex({ "completed_at": 1 }, { 
    expireAfterSeconds: 86400, 
    background: true 
});

// Create indexes for batch contexts
db.batch_contexts.createIndex({ "status": 1 }, { background: true });
db.batch_contexts.createIndex({ "created_at": 1 }, { background: true });

// Create TTL index for completed batch contexts
db.batch_contexts.createIndex({ "completed_at": 1 }, { 
    expireAfterSeconds: 604800,  // 7 days 
    background: true 
});

// Create indexes for references
db.context_references.createIndex({ "user_id": 1 }, { background: true });
db.context_references.createIndex({ "purpose_id": 1 }, { background: true });

// Print confirmation message
print("MongoDB initialized for Agent Microservice");
print("Created collections: contexts, batch_contexts, context_references");
print("Created indexes for efficient queries and TTL expiration"); 