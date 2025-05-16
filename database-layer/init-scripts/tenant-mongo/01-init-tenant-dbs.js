// Initialize MongoDB for tenant databases
// This script creates the initial tenant databases and users

// Initialize replica set (this might need to be run separately)
// rs.initiate()

// Create dedicated database for first tenant
db = db.getSiblingDB('tenant_001_db');

// Create tenant admin user
db.createUser({
  user: 'tenant001admin',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'tenant_001_db' },
    { role: 'dbAdmin', db: 'tenant_001_db' }
  ]
});

// Create collections for the tenant
db.createCollection('marketing_campaigns');
db.createCollection('user_interactions');
db.createCollection('content_items');

// Create some indexes for efficient querying
db.marketing_campaigns.createIndex({ "status": 1 });
db.marketing_campaigns.createIndex({ "scheduled_at": 1 });
db.user_interactions.createIndex({ "user_id": 1 });
db.user_interactions.createIndex({ "timestamp": 1 });
db.content_items.createIndex({ "type": 1 });

// Create shared database for multiple tenants
db = db.getSiblingDB('shared_tenant_db');

// Create admin user for the shared database
db.createUser({
  user: 'sharedadmin',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'shared_tenant_db' },
    { role: 'dbAdmin', db: 'shared_tenant_db' }
  ]
});

// Create collections with shard key field for tenant isolation
db.createCollection('marketing_campaigns');
db.createCollection('user_interactions');
db.createCollection('content_items');

// Create compound indexes with tenant_id as the first field
db.marketing_campaigns.createIndex({ "tenant_id": 1, "status": 1 });
db.marketing_campaigns.createIndex({ "tenant_id": 1, "scheduled_at": 1 });
db.user_interactions.createIndex({ "tenant_id": 1, "user_id": 1 });
db.user_interactions.createIndex({ "tenant_id": 1, "timestamp": 1 });
db.content_items.createIndex({ "tenant_id": 1, "type": 1 });

// Insert sample data for tenant-002 in the shared database
db.marketing_campaigns.insertMany([
  {
    tenant_id: 'tenant-002',
    name: 'Welcome Campaign',
    status: 'active',
    scheduled_at: new Date(),
    content: {
      subject: 'Welcome to our platform',
      body: 'Thank you for joining our platform! We are excited to have you on board.'
    },
    recipients: {
      count: 100,
      filter: { status: 'active' }
    },
    created_at: new Date(),
    updated_at: new Date()
  }
]);

db.user_interactions.insertMany([
  {
    tenant_id: 'tenant-002',
    user_id: 'user123',
    interaction_type: 'page_view',
    page: '/dashboard',
    timestamp: new Date(),
    metadata: {
      browser: 'Chrome',
      device: 'Desktop'
    }
  }
]);

db.content_items.insertMany([
  {
    tenant_id: 'tenant-002',
    title: 'Getting Started Guide',
    type: 'article',
    content: 'This is a guide to help you get started with our platform.',
    status: 'published',
    created_at: new Date(),
    updated_at: new Date()
  }
]); 