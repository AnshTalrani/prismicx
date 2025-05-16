// User Insights MongoDB Initialization Script
// This script creates collections for user insights data with one collection per tenant

/**
 * This script initializes the MongoDB collections for user insights.
 * Each tenant will have their own dedicated user_insights collection.
 * The script creates collections with appropriate indexes for efficient querying.
 */

// Function to create user insights collection for a tenant
function createUserInsightsCollection(tenantId) {
  const dbName = `tenant_${tenantId}_db`;
  db = db.getSiblingDB(dbName);
  
  // Create user_insights collection if it doesn't exist
  if (!db.getCollectionNames().includes('user_insights')) {
    db.createCollection('user_insights');
    print(`Created user_insights collection for tenant ${tenantId}`);
  }
  
  // Create indexes for efficient querying
  db.user_insights.createIndex({ "user_id": 1 }, { unique: true });
  db.user_insights.createIndex({ "topics.name": 1 });
  db.user_insights.createIndex({ "updated_at": 1 });
  
  print(`Created indexes for user_insights collection in tenant ${tenantId}`);
}

// Create service-specific user for accessing user insights data
db = db.getSiblingDB('admin');
db.createUser({
  user: 'user_insights_service',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'tenant_001_db' },
    { role: 'readWrite', db: 'tenant_002_db' },
    { role: 'readWrite', db: 'tenant_003_db' }
  ]
});

print("Created user_insights_service user with appropriate permissions");

// Initialize collections for sample tenants
const tenants = ['001', '002', '003'];
tenants.forEach(tenantId => {
  createUserInsightsCollection(tenantId);
});

// Insert sample data for testing
db = db.getSiblingDB('tenant_001_db');
db.user_insights.insertOne({
  user_id: "user123",
  tenant_id: "001",
  topics: [
    {
      topic_id: "topic1",
      name: "AI Technologies",
      description: "Emerging AI technologies and their applications",
      subtopics: [
        {
          subtopic_id: "subtopic1",
          name: "Machine Learning",
          content: {
            key_points: ["Supervised learning", "Unsupervised learning", "Reinforcement learning"],
            resources: ["https://example.com/ml-resource"]
          },
          created_at: new Date(),
          updated_at: new Date()
        },
        {
          subtopic_id: "subtopic2",
          name: "Neural Networks",
          content: {
            key_points: ["Deep learning", "Convolutional networks", "Recurrent networks"],
            resources: ["https://example.com/nn-resource"]
          },
          created_at: new Date(),
          updated_at: new Date()
        }
      ],
      created_at: new Date(),
      updated_at: new Date()
    }
  ],
  metadata: {
    profile_completeness: 85,
    interest_score: 92
  },
  created_at: new Date(),
  updated_at: new Date()
});

print("Inserted sample user insight for tenant 001");

// Create another sample user insight
db.user_insights.insertOne({
  user_id: "user456",
  tenant_id: "001",
  topics: [
    {
      topic_id: "topic2",
      name: "Cloud Computing",
      description: "Modern cloud infrastructure and services",
      subtopics: [
        {
          subtopic_id: "subtopic3",
          name: "Serverless Computing",
          content: {
            key_points: ["FaaS", "BaaS", "Event-driven architecture"],
            resources: ["https://example.com/serverless-resource"]
          },
          created_at: new Date(),
          updated_at: new Date()
        }
      ],
      created_at: new Date(),
      updated_at: new Date()
    }
  ],
  metadata: {
    profile_completeness: 70,
    interest_score: 85
  },
  created_at: new Date(),
  updated_at: new Date()
});

print("Inserted second sample user insight for tenant 001");

// Add a different sample for tenant 002
db = db.getSiblingDB('tenant_002_db');
db.user_insights.insertOne({
  user_id: "user789",
  tenant_id: "002",
  topics: [
    {
      topic_id: "topic3",
      name: "Digital Marketing",
      description: "Modern digital marketing strategies",
      subtopics: [
        {
          subtopic_id: "subtopic4",
          name: "Social Media Marketing",
          content: {
            key_points: ["Platform selection", "Content strategy", "Analytics"],
            resources: ["https://example.com/smm-resource"]
          },
          created_at: new Date(),
          updated_at: new Date()
        }
      ],
      created_at: new Date(),
      updated_at: new Date()
    }
  ],
  metadata: {
    profile_completeness: 90,
    interest_score: 95
  },
  created_at: new Date(),
  updated_at: new Date()
});

print("Inserted sample user insight for tenant 002");

print("User insights initialization completed successfully"); 