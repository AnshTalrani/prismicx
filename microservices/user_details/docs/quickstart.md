# Quick Start Guide: Working with Structure Templates

This guide provides a quick overview of how to work with the configuration-driven structure templates in the User Details Microservice.

## Initial Setup

When the microservice starts, it automatically:

1. Creates the templates directory structure if it doesn't exist
2. Generates default template files if they're missing
3. Loads all configuration templates into memory

No additional setup is required to get started.

## Viewing Current Configurations

To view the current configuration templates:

1. **User Insight Structure**:
   ```
   GET /api/v1/config/insight-structure
   ```

2. **Default Topics**:
   ```
   GET /api/v1/config/default-topics
   ```

3. **Extension Types**:
   ```
   GET /api/v1/config/extension-types
   ```

## Modifying Templates: 3 Simple Steps

### 1. Edit the JSON Files

Locate and edit the appropriate JSON template file:

- User Insight Structure: `config/templates/user_insight_structure.json`
- Default Topics: `config/templates/default_topics.json`
- Extension Types: `config/templates/extension_types/*.json`

### 2. Reload the Configuration

After saving your changes, reload the configuration:

```
POST /api/v1/admin/config/reload
```

(Include the `X-Tenant-ID` header with your tenant ID)

### 3. Verify Your Changes

Check that your changes were applied by viewing the configuration:

```
GET /api/v1/config/insight-structure
```

## Mandatory Migration System: Updating Existing Data

When you modify structure templates, the system automatically detects these changes. You MUST trigger a migration to ensure all existing user data is updated to match the new structure. This step is not optional and is critical for maintaining data consistency across the system.

### Triggering a Migration

After making changes to your templates and reloading the configuration, you MUST trigger a migration:

```
POST /api/v1/admin/config/migrate
```

This mandatory step will:
1. Detect changes between the previous and current templates
2. Update all existing user insights across all tenants
3. Apply new default topics to existing users
4. Return a detailed migration report

⚠️ **IMPORTANT**: Skipping this step will result in inconsistent data structures between new and existing users.

### Migration Capabilities

The migration system handles:

- Adding new metadata fields to all user insights
- Removing fields that are no longer in the schema
- Adding new default topics to existing users
- Updating extension configurations based on template changes

### Migration Report

The migration endpoint returns a detailed report:

```json
{
  "status": "completed",
  "total_insights": 150,
  "updated_insights": 145,
  "failed_updates": 5,
  "tenant_summaries": [
    {
      "tenant_id": "tenant1",
      "total_insights": 100,
      "updated_insights": 98,
      "failed_updates": 2
    },
    {
      "tenant_id": "tenant2",
      "total_insights": 50,
      "updated_insights": 47,
      "failed_updates": 3
    }
  ],
  "migration_operations": {
    "metadata": {
      "old": { /* old structure */ },
      "new": { /* new structure */ }
    },
    "add_default_topics": [
      /* list of added topics */
    ]
  }
}
```

## Example: Adding a New Default Topic

1. **Edit** `config/templates/default_topics.json`:
   ```json
   [
     {
       "name": "Getting Started",
       "description": "Initial topics to help new users get started",
       "subtopics": [
         {
           "name": "System Introduction",
           "content": {
             "expertise_level": "beginner",
             "key_points": ["Overview of system features", "How to navigate interfaces"]
           }
         }
       ]
     },
     {
       "name": "New Topic Example",
       "description": "This is a new topic added through template editing",
       "subtopics": [
         {
           "name": "Sample Subtopic",
           "content": {
             "expertise_level": "beginner",
             "key_points": ["Example point 1", "Example point 2"]
           }
         }
       ]
     }
   ]
   ```

2. **Reload** the configuration:
   ```
   POST /api/v1/admin/config/reload
   ```

3. **Verify** the changes:
   ```
   GET /api/v1/config/default-topics
   ```

4. **Migrate** existing user insights (mandatory):
   ```
   POST /api/v1/admin/config/migrate
   ```

After migration, both new and existing users will have this additional topic in their user insights.

## Example: Adding a New Extension Type

1. **Create** a new file `config/templates/extension_types/skill_tracker.json`:
   ```json
   {
     "extension_type": "skill_tracker",
     "schema": {
       "required": ["name", "enabled"],
       "metadata": {
         "required": ["version", "configuration"],
         "configuration": {
           "required": ["skill_levels", "track_history"]
         }
       }
     },
     "defaults": {
       "priority": 3,
       "enabled": true,
       "metadata": {
         "version": "1.0",
         "configuration": {
           "skill_levels": ["beginner", "intermediate", "advanced"],
           "track_history": true
         }
       }
     }
   }
   ```

2. **Reload** the configuration:
   ```
   POST /api/v1/admin/config/reload
   ```

3. **Verify** the extension type was added:
   ```
   GET /api/v1/config/extension-types
   ```

4. **Migrate** existing extensions (mandatory):
   ```
   POST /api/v1/admin/config/migrate
   ```

This required migration step ensures all existing extensions are updated with the new structure and default values. 