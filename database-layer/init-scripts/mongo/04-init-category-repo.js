/**
 * MongoDB initialization script for Category Repository Service
 *
 * This script:
 * 1. Creates the category_repository database
 * 2. Creates a dedicated user for the service
 * 3. Creates and initializes required collections with indexes
 * 4. Adds sample data for testing
 */

print('================= Initializing Category Repository Database =================');

// Connect as admin
db = db.getSiblingDB('admin');
db.auth('admin', 'password');

// Create category repository database
print('Creating category_repository database...');
db = db.getSiblingDB('category_repository');

// Create dedicated user
print('Creating category_service user...');
db.createUser({
  user: 'category_service',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'category_repository' },
    { role: 'dbAdmin', db: 'category_repository' }
  ]
});

// Create collections
print('Creating collections...');
db.createCollection('categories');
db.createCollection('factors');
db.createCollection('campaigns');
db.createCollection('batch_as_objects');
db.createCollection('entity_assignments');

// Create indexes for optimized queries
print('Creating indexes...');

// Categories indexes
db.categories.createIndex({ "category_id": 1 }, { unique: true });
db.categories.createIndex({ "type": 1 });

// Factors indexes
db.factors.createIndex({ "factor_id": 1 }, { unique: true });
db.factors.createIndex({ "category_id": 1 });

// Campaigns indexes
db.campaigns.createIndex({ "campaign_id": 1 }, { unique: true });
db.campaigns.createIndex({ "category_id": 1 });

// Batch as objects indexes
db.batch_as_objects.createIndex({ "bao_id": 1 }, { unique: true });
db.batch_as_objects.createIndex({ "category_id": 1 });

// Entity assignments indexes
db.entity_assignments.createIndex(
  { "entity_type": 1, "entity_id": 1, "category_type": 1, "item_id": 1 }, 
  { unique: true }
);
db.entity_assignments.createIndex({ "entity_type": 1, "entity_id": 1 });
db.entity_assignments.createIndex({ "category_type": 1, "item_id": 1 });

// Add sample data
print('Adding sample data...');

// Sample categories
const sampleCategories = [
  {
    category_id: 'marketing_segment',
    name: 'Marketing Segment',
    description: 'Categories for marketing segmentation',
    type: 'segment',
    metadata: {
      display_order: 1,
      usage: 'segmentation'
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    category_id: 'user_type',
    name: 'User Type',
    description: 'Categories for user classification',
    type: 'user',
    metadata: {
      display_order: 2,
      usage: 'classification'
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    category_id: 'content_type',
    name: 'Content Type',
    description: 'Categories for content classification',
    type: 'content',
    metadata: {
      display_order: 3,
      usage: 'classification'
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    category_id: 'tag',
    name: 'Tags',
    description: 'Generic tags for various entities',
    type: 'tag',
    metadata: {
      display_order: 4,
      usage: 'tagging'
    },
    created_at: new Date(),
    updated_at: new Date()
  }
];

db.categories.insertMany(sampleCategories);

// Sample factors
const sampleFactors = [
  {
    factor_id: 'factor_industry_technology',
    factor_name: 'industry:technology',
    category_id: 'marketing_segment',
    value: 'technology',
    metadata: {
      description: 'Technology industry segment',
      priority: 1
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    factor_id: 'factor_industry_healthcare',
    factor_name: 'industry:healthcare',
    category_id: 'marketing_segment',
    value: 'healthcare',
    metadata: {
      description: 'Healthcare industry segment',
      priority: 2
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    factor_id: 'factor_user_enterprise',
    factor_name: 'user_type:enterprise',
    category_id: 'user_type',
    value: 'enterprise',
    metadata: {
      description: 'Enterprise users',
      priority: 1
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    factor_id: 'factor_user_small_business',
    factor_name: 'user_type:small_business',
    category_id: 'user_type',
    value: 'small_business',
    metadata: {
      description: 'Small business users',
      priority: 2
    },
    created_at: new Date(),
    updated_at: new Date()
  }
];

db.factors.insertMany(sampleFactors);

// Sample batch as objects
const sampleBatchObjects = [
  {
    bao_id: 'batch_marketing_campaign_2023',
    name: 'Marketing Campaign 2023',
    description: 'Annual marketing campaign targeting technology sector',
    category_id: 'marketing_segment',
    metadata: {
      start_date: '2023-01-01',
      end_date: '2023-12-31'
    },
    metrics: {
      conversion_rate: 0.15,
      click_through_rate: 0.25,
      engagement_score: 0.78
    },
    created_at: new Date(),
    updated_at: new Date()
  }
];

db.batch_as_objects.insertMany(sampleBatchObjects);

print('Category Repository Database initialization complete!'); 