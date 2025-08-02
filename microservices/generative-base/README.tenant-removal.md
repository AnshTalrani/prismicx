# Tenant Schema Switching Removal

This document explains the changes made to eliminate tenant schema switching in the generative-base microservice.

## Problem

The original implementation used tenant-specific database schemas, where database operations for each tenant would switch to a different schema. This approach created unnecessary overhead, particularly when:

1. Processing batches of items from different tenants
2. Switching schemas frequently during batch operations
3. Maintaining separate schema permissions and structures

## Solution

We've modified the generative-base microservice to use a single schema approach with a `batch_id` field for organization instead of schema switching. This change:

1. Eliminates schema switching overhead
2. Maintains batch processing capabilities
3. Preserves template customization for individual users
4. Simplifies database operations

## Changes Made

1. **Tenant Database Context**:
   - Replaced `apply_tenant_context` with `apply_batch_context` that doesn't switch schemas
   - Renamed `get_tenant_db_session` to `get_db_session_with_batch` that doesn't apply tenant schema switching
   - Maintained backward compatibility through aliasing

2. **Database Access**:
   - Modified the PostgreSQL database class to accept `batch_id` for monitoring
   - Removed tenant schema switching in database operations
   - Updated connection handling to use a single schema

3. **Dependencies**:
   - Added batch-aware dependencies (`get_batch_id`, `get_db`)
   - Maintained legacy dependencies for backward compatibility

4. **Middleware**:
   - Removed tenant schema switching middleware
   - Commented it out in app.py with an explanation

5. **Database Schema**:
   - Added a migration script that adds `batch_id` fields to relevant tables
   - Created indexes on `batch_id` for efficient queries
   - Preserved `tenant_id` as a reference field but not for schema switching

## Using Batch IDs

Instead of relying on tenant schemas, you should now:

1. Include a `batch_id` in your requests using the `X-Batch-ID` header
2. Pass `batch_id` to database operations for monitoring
3. Use `batch_id` for organizing and filtering batch operations
4. Query based on `batch_id` instead of relying on tenant isolation

## Backward Compatibility

We've maintained backward compatibility by:

1. Keeping tenant-related classes and functions but removing their schema-switching behavior
2. Aliasing new functions to old names where appropriate
3. Preserving tenant_id as a reference field

## Benefits

These changes provide:

1. **Improved Performance**: No schema switching overhead
2. **Simplified Architecture**: Single schema with batch organization
3. **Better Batch Processing**: More efficient handling of multi-tenant batches
4. **Maintained Functionality**: Template processing still works the same way 