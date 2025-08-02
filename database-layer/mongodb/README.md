# MongoDB Database Layer

This directory contains the MongoDB database configuration and schemas for the PrismicX application.

## Structure

The MongoDB database layer is organized as follows:

- **User Insights Collections**: One collection per tenant to store user insights data
  - Each tenant has a dedicated database named `tenant_<tenant_id>_db`
  - Within each database, there is a `user_insights` collection

## Schema

### User Insights Collection

The `user_insights` collection follows this schema:

```javascript
{
  user_id: String,         // Unique identifier for the user
  tenant_id: String,       // Tenant identifier
  topics: [                // Array of user topics
    {
      topic_id: String,    // Unique identifier for the topic
      name: String,        // Name of the topic
      description: String, // Description of the topic
      subtopics: [         // Array of subtopics
        {
          subtopic_id: String,  // Unique identifier for the subtopic
          name: String,         // Name of the subtopic
          content: Object,      // Content data for the subtopic
          created_at: Date,     // Creation timestamp
          updated_at: Date      // Last update timestamp
        }
      ],
      created_at: Date,    // Creation timestamp
      updated_at: Date     // Last update timestamp
    }
  ],
  metadata: Object,        // Additional metadata
  created_at: Date,        // Creation timestamp
  updated_at: Date         // Last update timestamp
}
```

## Indexes

The following indexes are created for efficient querying:

- `user_id`: Unique index to quickly retrieve a specific user's insights
- `topics.name`: Index to search topics by name
- `updated_at`: Index to sort and filter by the last update time

## Access Control

- A dedicated service user `user_insights_service` is created with read/write permissions for all tenant databases
- Authentication is enforced for all connections

## Initialization

The MongoDB collections are initialized through scripts located in:
- `/database-layer/init-scripts/mongo/03-init-user-insights.js` 