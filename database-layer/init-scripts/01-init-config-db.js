// Create config database user
db.createUser({
    user: 'config_user',
    pwd: 'config_password',  // Should be changed in production
    roles: [
        {
            role: 'readWrite',
            db: 'config_db'
        }
    ]
});

// Switch to config database
db = db.getSiblingDB('config_db');

// Create collections with validation
db.createCollection('tenant_configs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['tenant_id', 'config_key', 'config_value', 'created_by', 'updated_by'],
            properties: {
                tenant_id: {
                    bsonType: 'string',
                    description: 'Tenant identifier'
                },
                config_key: {
                    bsonType: 'string',
                    description: 'Configuration key'
                },
                config_value: {
                    bsonType: 'object',
                    description: 'Configuration value'
                },
                metadata: {
                    bsonType: 'object',
                    description: 'Additional metadata'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                created_by: {
                    bsonType: 'string',
                    description: 'User who created the config'
                },
                updated_by: {
                    bsonType: 'string',
                    description: 'User who last updated the config'
                }
            }
        }
    }
});

db.createCollection('config_schemas', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['key', 'schema'],
            properties: {
                key: {
                    bsonType: 'string',
                    description: 'Schema key'
                },
                schema: {
                    bsonType: 'object',
                    description: 'JSON schema definition'
                },
                metadata: {
                    bsonType: 'object',
                    description: 'Additional metadata'
                },
                required: {
                    bsonType: 'bool',
                    description: 'Whether this config is required'
                },
                default_value: {
                    bsonType: 'object',
                    description: 'Default configuration value'
                }
            }
        }
    }
});

// Create indexes
db.tenant_configs.createIndex(
    { tenant_id: 1, config_key: 1 },
    { unique: true }
);

db.config_schemas.createIndex(
    { key: 1 },
    { unique: true }
); 