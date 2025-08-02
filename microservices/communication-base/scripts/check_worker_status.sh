#!/bin/bash

# Script to check the status of the communication-base worker service

# Configuration
MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017"}
MONGO_DB=${MONGO_DB:-"communication_base"}
BATCH_COLLECTION=${BATCH_COLLECTION:-"agent_batch_requests"}
CAMPAIGNS_COLLECTION=${CAMPAIGNS_COLLECTION:-"campaigns"}

echo "=== Communication Base Worker Status ==="
echo "Time: $(date)"
echo

# Check if the worker process is running
if pgrep -f "python -m src.main" > /dev/null; then
    echo "✓ Worker service is running"
else
    echo "✗ Worker service is NOT running"
fi

echo

# Check MongoDB connection
if command -v mongosh &> /dev/null; then
    echo "=== Batch Request Processing Stats ==="
    
    # Count requests by status
    echo "Batch Requests by Status:"
    mongosh "$MONGO_URI/$MONGO_DB" --quiet --eval "
        const stats = db.$BATCH_COLLECTION.aggregate([
            { \$match: { servicetype: 'communication' } },
            { \$group: { _id: '\$status', count: { \$sum: 1 } } },
            { \$sort: { count: -1 } }
        ]).toArray();
        
        stats.forEach(s => {
            print(` - ${s._id}: ${s.count}`);
        });
    "
    
    echo
    
    # Count campaigns by status
    echo "Campaigns by Status:"
    mongosh "$MONGO_URI/$MONGO_DB" --quiet --eval "
        const campaignStats = db.$CAMPAIGNS_COLLECTION.aggregate([
            { \$group: { _id: '\$status', count: { \$sum: 1 } } },
            { \$sort: { count: -1 } }
        ]).toArray();
        
        campaignStats.forEach(s => {
            print(` - ${s._id}: ${s.count}`);
        });
    "
    
    echo
    
    # Show recent batch requests
    echo "Recent Batch Requests (last 5):"
    mongosh "$MONGO_URI/$MONGO_DB" --quiet --eval "
        const recentRequests = db.$BATCH_COLLECTION.find(
            { servicetype: 'communication' },
            { _id: 1, name: 1, status: 1, created_at: 1, updated_at: 1 }
        ).sort({ created_at: -1 }).limit(5).toArray();
        
        recentRequests.forEach(r => {
            print(` - ${r._id}: ${r.name} (${r.status}) - Created: ${r.created_at}`);
        });
    "
    
    echo
    
    # Show recent campaigns
    echo "Recent Campaigns (last 5):"
    mongosh "$MONGO_URI/$MONGO_DB" --quiet --eval "
        const recentCampaigns = db.$CAMPAIGNS_COLLECTION.find(
            {},
            { _id: 1, name: 1, status: 1, created_at: 1, recipient_count: { \$size: '\$recipients' } }
        ).sort({ created_at: -1 }).limit(5).toArray();
        
        recentCampaigns.forEach(c => {
            print(` - ${c._id}: ${c.name} (${c.status}) - Recipients: ${c.recipient_count}`);
        });
    "
else
    echo "MongoDB client (mongosh) not found. Cannot retrieve statistics."
fi

echo
echo "=== End of Status Report ===" 