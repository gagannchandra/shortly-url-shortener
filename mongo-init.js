// MongoDB initialization script
// Creates the 'shortly' database with proper user and collections.

db = db.getSiblingDB('shortly');

db.createCollection('urls');

// Indexes are also created in app/db.py at startup,
// but defining them here ensures they exist even before first app boot.
db.urls.createIndex({ short_code: 1 }, { unique: true, name: 'idx_short_code' });
db.urls.createIndex(
  { expires_at: 1 },
  { expireAfterSeconds: 0, sparse: true, name: 'idx_ttl_expiry' }
);

print('✓ Shortly database initialized');
