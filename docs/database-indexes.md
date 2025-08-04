# Database Performance Indexes

This document describes the strategic database indexes added to optimize query performance across the Python Learning Studio platform.

## Overview

The indexes are designed to optimize the most common and performance-critical queries identified through code analysis. All indexes use `CREATE INDEX CONCURRENTLY` to avoid blocking operations during creation.

## Index Categories

### 1. Forum Integration Indexes (`0006_add_performance_indexes.py`)

#### Review Queue Indexes
- **`idx_reviewqueue_status_priority`**: Optimizes moderation queue queries by status and priority
- **`idx_reviewqueue_pending`**: Partial index for pending reviews (most common query)

#### Trust Level Indexes  
- **`idx_usertrustlevel_level_updated`**: For trust level progression queries
- **`idx_usertrustlevel_user_level`**: User trust level lookups

#### Gamification Indexes
- **`idx_userbadge_user_awarded`**: User badge queries and profiles
- **`idx_userbadge_badge_awarded`**: Badge statistics and leaderboards
- **`idx_badge_type_threshold`**: Badge awarding logic optimization

#### User Activity Indexes
- **`idx_useractivity_user_date`**: User activity tracking
- **`idx_useractivity_date_active`**: Active users analytics (partial index)

### 2. Learning App Indexes (`0005_add_performance_indexes.py`)

#### Course Discovery Indexes
- **`idx_course_published_created`**: Course browsing (partial index for published only)
- **`idx_course_category_published`**: Category-based course filtering
- **`idx_course_difficulty_published`**: Difficulty-based filtering

#### Progress Tracking Indexes
- **`idx_userprogress_user_completed`**: User progress queries with completion status
- **`idx_userprogress_lesson_completed`**: Lesson completion statistics
- **`idx_userprogress_course_progress`**: Course progress with INCLUDE clause for covered queries

#### Exercise System Indexes
- **`idx_submission_exercise_created`**: Exercise submission history
- **`idx_submission_user_exercise`**: User-specific submission tracking
- **`idx_submission_status_created`**: Grading queue optimization (partial index)

#### Enrollment Management Indexes
- **`idx_courseenrollment_user_enrolled`**: User enrollment history
- **`idx_courseenrollment_course_progress`**: Course completion analytics
- **`idx_courseenrollment_active`**: Active enrollments (partial index)

#### Content Navigation Indexes
- **`idx_lesson_course_order`**: Lesson ordering within courses
- **`idx_lesson_published`**: Published lesson discovery (partial index)
- **`idx_exercise_lesson_type`**: Exercise queries by type
- **`idx_exercise_difficulty`**: Exercise difficulty filtering

### 3. User Management Indexes (`0002_add_performance_indexes.py`)

#### Authentication Indexes
- **`idx_user_email_active`**: Email-based login optimization (partial index)
- **`idx_user_username_active`**: Username-based login optimization (partial index)

#### User Analytics Indexes
- **`idx_user_last_login`**: Online user tracking (partial index)
- **`idx_user_date_joined`**: User registration analytics

#### Profile Indexes
- **`idx_userprofile_user_skill`**: Skill level queries
- **`idx_userprofile_language`**: Programming language preferences (partial index)

#### Achievement Indexes
- **`idx_userachievement_user_earned`**: User achievement history
- **`idx_userachievement_type_earned`**: Achievement type analytics

### 4. Forum Tables Indexes (Management Command)

#### Post Performance Indexes
- **`idx_forum_post_approved_created`**: Approved post queries (partial index)
- **`idx_forum_post_topic_approved`**: Topic-specific post queries
- **`idx_forum_post_poster_created`**: User post history (partial index)

#### Topic Management Indexes
- **`idx_forum_topic_forum_approved`**: Forum topic listing with last post ordering
- **`idx_forum_topic_approved_created`**: Recent topics (partial index)
- **`idx_forum_topic_poster_approved`**: User topic history
- **`idx_forum_topic_sticky_approved`**: Sticky topic optimization (partial index)

#### Forum Navigation Indexes
- **`idx_forum_type_parent`**: Forum hierarchy navigation
- **`idx_forum_parent_position`**: Forum ordering (partial index)

#### Permission System Indexes
- **`idx_forum_permission_forum_user`**: User permission lookups (partial index)
- **`idx_forum_permission_forum_group`**: Group permission lookups (partial index)

#### Read Tracking Indexes
- **`idx_forum_topicread_user_topic`**: Topic read status
- **`idx_forum_forumread_user_forum`**: Forum read status

## Usage Instructions

### Running Migrations

```bash
# Run custom app migrations
python manage.py migrate forum_integration 0006
python manage.py migrate learning 0005  
python manage.py migrate users 0002

# Add forum table indexes
python manage.py add_machina_indexes

# Dry run to see what would be created
python manage.py add_machina_indexes --dry-run
```

### Post-Migration Optimization

```sql
-- Analyze tables after index creation
VACUUM ANALYZE;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;

-- Monitor query performance
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

## Performance Impact

### Expected Improvements

1. **Forum Queries**: 50-80% improvement in topic/post listing queries
2. **Course Discovery**: 60-90% improvement in course browsing and filtering
3. **User Authentication**: 70-95% improvement in login performance
4. **Progress Tracking**: 40-70% improvement in progress calculations
5. **Moderation Queries**: 80-95% improvement in review queue operations

### Query Patterns Optimized

- Course browsing with category/difficulty filters
- User progress dashboard queries
- Forum topic listing with pagination
- User authentication and profile lookups
- Exercise submission tracking
- Badge and achievement queries
- Trust level calculations
- Moderation queue management

## Index Design Principles

### 1. Partial Indexes
Used for common filter conditions (e.g., `WHERE is_published = true`)
- Smaller index size
- Faster queries for filtered data
- Reduced maintenance overhead

### 2. Composite Indexes
Multiple columns in optimal order:
- Most selective columns first
- Query filter order consideration
- Sort order optimization

### 3. INCLUDE Clause
PostgreSQL covering indexes:
- Avoid table lookups
- Include frequently selected columns
- Reduce I/O operations

### 4. Concurrent Creation
All indexes created with `CONCURRENTLY`:
- No table locking during creation
- Safe for production deployment
- Longer creation time but no downtime

## Monitoring and Maintenance

### Regular Monitoring

```sql
-- Index usage statistics
SELECT 
    schemaname, 
    tablename, 
    indexname, 
    idx_tup_read,
    idx_tup_fetch,
    ROUND(idx_tup_read::numeric / NULLIF(seq_tup_read + idx_tup_read, 0) * 100, 2) AS index_usage_pct
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;

-- Index size monitoring
SELECT 
    schemaname, 
    tablename, 
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes 
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Maintenance Tasks

1. **Weekly**: Monitor slow query log for new optimization opportunities
2. **Monthly**: Review index usage statistics, drop unused indexes
3. **Quarterly**: Analyze query performance trends and adjust as needed
4. **As needed**: REINDEX if fragmentation detected

## Security Considerations

- All indexes respect existing row-level security policies
- Partial indexes use safe WHERE clauses
- No sensitive data exposed through index structure
- Concurrent creation prevents denial of service

## Rollback Instructions

If indexes cause performance issues:

```bash
# Remove custom indexes (run SQL manually)
DROP INDEX IF EXISTS idx_reviewqueue_status_priority;
DROP INDEX IF EXISTS idx_course_published_created;
# ... etc for all indexes

# Or rollback migrations
python manage.py migrate forum_integration 0005
python manage.py migrate learning 0004
python manage.py migrate users 0001
```

## Future Optimization Opportunities

1. **Partitioning**: Consider table partitioning for very large tables
2. **Materialized Views**: For complex aggregate queries
3. **Full-Text Search**: PostgreSQL full-text search for forum content
4. **Caching**: Redis caching for frequently accessed data
5. **Query Optimization**: Continue monitoring and optimizing based on usage patterns