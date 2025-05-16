// This script initializes the tenant registry database
db = db.getSiblingDB('tenant_registry');

// Create admin user for the tenant_registry database
db.createUser({
  user: 'tenant_service',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'tenant_registry' },
    { role: 'dbAdmin', db: 'tenant_registry' }
  ]
});

// Create tenants collection with validation schema
db.createCollection('tenants', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['tenant_id', 'name', 'database_config', 'created_at', 'status'],
      properties: {
        tenant_id: {
          bsonType: 'string',
          description: 'Unique identifier for the tenant'
        },
        name: {
          bsonType: 'string',
          description: 'Name of the tenant organization'
        },
        database_config: {
          bsonType: 'object',
          required: ['type', 'connection_string'],
          properties: {
            type: {
              enum: ['dedicated', 'shared'],
              description: 'Database isolation type (dedicated or shared)'
            },
            connection_string: {
              bsonType: 'string',
              description: 'Connection string to the tenant database'
            },
            database_name: {
              bsonType: 'string',
              description: 'Name of the tenant database'
            },
            shard_key: {
              bsonType: 'string',
              description: 'Shard key for the tenant (if applicable)'
            }
          }
        },
        created_at: {
          bsonType: 'date',
          description: 'Timestamp when the tenant was created'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Timestamp when the tenant was last updated'
        },
        status: {
          enum: ['active', 'inactive', 'suspended', 'provisioning'],
          description: 'Current status of the tenant'
        },
        settings: {
          bsonType: 'object',
          description: 'Tenant-specific settings'
        },
        tier: {
          bsonType: 'string',
          description: 'Service tier of the tenant'
        },
        region: {
          bsonType: 'string',
          description: 'Primary geographical region of the tenant'
        }
      }
    }
  }
});

// Create indexes for efficient querying
db.tenants.createIndex({ "tenant_id": 1 }, { unique: true });
db.tenants.createIndex({ "name": 1 });
db.tenants.createIndex({ "status": 1 });
db.tenants.createIndex({ "region": 1 });

// Insert sample tenants
db.tenants.insertMany([
  {
    tenant_id: 'tenant-001',
    name: 'Demo Organization 1',
    database_config: {
      type: 'dedicated',
      connection_string: 'mongodb://admin:password@mongodb-tenant:27017',
      database_name: 'tenant_001_db'
    },
    created_at: new Date(),
    updated_at: new Date(),
    status: 'active',
    settings: {
      max_users: 100,
      storage_limit_gb: 10
    },
    tier: 'standard',
    region: 'us-east'
  },
  {
    tenant_id: 'tenant-002',
    name: 'Demo Organization 2',
    database_config: {
      type: 'shared',
      connection_string: 'mongodb://admin:password@mongodb-tenant:27017',
      database_name: 'shared_tenant_db',
      shard_key: 'tenant-002'
    },
    created_at: new Date(),
    updated_at: new Date(),
    status: 'active',
    settings: {
      max_users: 50,
      storage_limit_gb: 5
    },
    tier: 'basic',
    region: 'eu-west'
  }
]);

// Create tenant_databases collection to track tenant database metadata
db.createCollection('tenant_databases', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['database_name', 'type', 'status', 'created_at'],
      properties: {
        database_name: {
          bsonType: 'string',
          description: 'Name of the tenant database'
        },
        type: {
          enum: ['dedicated', 'shared'],
          description: 'Database type (dedicated to one tenant or shared)'
        },
        tenants: {
          bsonType: 'array',
          description: 'List of tenant IDs using this database (for shared databases)'
        },
        status: {
          enum: ['active', 'provisioning', 'decommissioning', 'archived'],
          description: 'Current status of the database'
        },
        created_at: {
          bsonType: 'date',
          description: 'Timestamp when the database was created'
        },
        server: {
          bsonType: 'string',
          description: 'Database server hostname'
        },
        region: {
          bsonType: 'string',
          description: 'Geographical region of the database'
        }
      }
    }
  }
});

// Create indexes for tenant_databases
db.tenant_databases.createIndex({ "database_name": 1 }, { unique: true });
db.tenant_databases.createIndex({ "type": 1 });
db.tenant_databases.createIndex({ "status": 1 });
db.tenant_databases.createIndex({ "region": 1 });

// Insert sample tenant databases
db.tenant_databases.insertMany([
  {
    database_name: 'tenant_001_db',
    type: 'dedicated',
    tenants: ['tenant-001'],
    status: 'active',
    created_at: new Date(),
    server: 'mongodb-tenant',
    region: 'us-east'
  },
  {
    database_name: 'shared_tenant_db',
    type: 'shared',
    tenants: ['tenant-002'],
    status: 'active',
    created_at: new Date(),
    server: 'mongodb-tenant',
    region: 'eu-west'
  }
]); 