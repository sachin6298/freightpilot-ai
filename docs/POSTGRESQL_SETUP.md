# PostgreSQL Database Setup and Migration Guide

## Overview

FreightPilot AI now uses PostgreSQL as the primary production database, replacing SQLite. This guide covers PostgreSQL setup, migration from SQLite, and database configuration.

## PostgreSQL Requirements

- PostgreSQL 13 or higher
- Python PostgreSQL driver: `psycopg[binary]`
- Database connection pooling support

## Quick Start

### 1. Install PostgreSQL

**Windows:**
- Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
- Run the installer with default settings
- Note the password you set during installation

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database and User

```sql
-- Connect to PostgreSQL as admin
psql -U postgres

-- Create database
CREATE DATABASE freightpilot;

-- Create dedicated user
CREATE USER freightpilot_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE freightpilot TO freightpilot_user;

-- Connect to the database and grant schema privileges
\c freightpilot
GRANT ALL ON SCHEMA public TO freightpilot_user;
```

### 3. Update Environment Configuration

Edit `backend/.env`:

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://freightpilot_user:your_secure_password@localhost/freightpilot

# PostgreSQL Connection Pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Keep SQLite for development if needed (comment out DATABASE_URL above)
# DATABASE_URL=sqlite:///./freightpilot.db
```

## Database Migration from SQLite

### Option A: Fresh Database (Recommended for Production)

1. **Ensure PostgreSQL is running**
2. **Apply Alembic migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```
3. **Seed initial data:**
   ```bash
   python -m app.db.seed
   ```

### Option B: Migrate Existing SQLite Data

1. **Backup your SQLite database:**
   ```bash
   cp freightpilot.db freightpilot.db.backup
   ```

2. **Run the migration utility:**
   ```bash
   python -m app.db.migrate_to_postgresql --sqlite-path freightpilot.db --verify
   ```

3. **Verify migration:**
   ```bash
   python -m app.db.migrate_to_postgresql --verify
   ```

### Migration Utility Options

```bash
# Basic migration
python -m app.db.migrate_to_postgresql

# Custom SQLite file
python -m app.db.migrate_to_postgresql --sqlite-path /path/to/database.db

# Custom PostgreSQL URL
python -m app.db.migrate_to_postgresql --postgresql-url postgresql://user:pass@host/db

# Verify after migration
python -m app.db.migrate_to_postgresql --verify
```

## Database Configuration

### Connection Pooling

PostgreSQL connection pooling is configured in `backend/app/db/session.py`:

- **DB_POOL_SIZE**: Number of persistent connections (default: 10)
- **DB_MAX_OVERFLOW**: Additional connections allowed beyond pool size (default: 20)
- **DB_POOL_TIMEOUT**: Connection wait timeout in seconds (default: 30)
- **DB_POOL_RECYCLE**: Connection recycle time in seconds (default: 3600)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | `postgresql://freightpilot:password@localhost/freightpilot` |
| DB_POOL_SIZE | Connection pool size | 10 |
| DB_MAX_OVERFLOW | Maximum overflow connections | 20 |
| DB_POOL_TIMEOUT | Pool timeout in seconds | 30 |
| DB_POOL_RECYCLE | Connection recycle time in seconds | 3600 |

## Alembic Database Migrations

### Common Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Show current revision
alembic current
```

### Migration Workflow

1. **Create migration:**
   ```bash
   alembic revision --autogenerate -m "add_new_feature"
   ```

2. **Review the generated migration file** in `alembic/versions/`

3. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

4. **Test the application** with the new schema

## Production Configuration

### 1. Secure Database Credentials

Never commit database credentials to version control. Use environment variables or a secret manager:

```bash
# Production .env (not committed to Git)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

### 2. Enable SSL (Recommended for Production)

```env
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

### 3. Connection Health Checks

The application automatically enables `pool_pre_ping=True` to validate connections before use.

### 4. Monitoring

Monitor PostgreSQL performance:

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Connection pool utilization
SELECT max_conn, used, reserved_for_super, free FROM pg_stat_database;
```

## Troubleshooting

### Connection Issues

1. **"Connection refused" error:**
   - Ensure PostgreSQL is running: `sudo systemctl status postgresql`
   - Check firewall settings
   - Verify connection string format

2. **"Database does not exist" error:**
   - Create the database: `CREATE DATABASE freightpilot;`
   - Check user permissions

3. **Authentication failures:**
   - Verify username and password in connection string
   - Check `pg_hba.conf` configuration

### Migration Issues

1. **Alembic migration fails:**
   - Check PostgreSQL user has CREATE TABLE permissions
   - Verify database exists
   - Check for conflicting migrations: `alembic history`

2. **Data migration errors:**
   - Ensure both databases are accessible
   - Check data type compatibility
   - Review migration utility logs

### Performance Issues

1. **Connection pool exhaustion:**
   - Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
   - Implement connection reuse in application code

2. **Slow queries:**
   - Add database indexes for frequently queried columns
   - Use PostgreSQL query optimization tools

## Development vs Production

### Development (SQLite)
- Fast setup and iteration
- Single file database
- Limited concurrency support
- Use for local development only

### Production (PostgreSQL)
- High concurrency support
- ACID compliance
- Connection pooling
- Advanced indexing and query optimization
- Required for multi-user deployment

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
pg_dump -U freightpilot_user -h localhost -d freightpilot > backup.sql

# SQLite backup (if still using)
cp freightpilot.db freightpilot.db.backup
```

### Restore from Backup

```bash
# PostgreSQL restore
psql -U freightpilot_user -h localhost -d freightpilot < backup.sql

# SQLite restore
cp freightpilot.db.backup freightpilot.db
```

## Security Best Practices

1. **Use environment variables** for credentials
2. **Enable SSL** for production connections
3. **Limit database user permissions** to required operations only
4. **Regularly update PostgreSQL** and security patches
5. **Monitor database logs** for suspicious activity
6. **Implement connection timeout** to prevent resource exhaustion

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Alembic Migration Documentation](https://alembic.sqlalchemy.org/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)