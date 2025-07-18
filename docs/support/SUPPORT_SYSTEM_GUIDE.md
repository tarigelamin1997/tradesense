# TradeSense Support System Guide

## Overview

The TradeSense support system provides comprehensive customer service through:
- Ticket management system
- Knowledge base with self-service articles
- Automated responses and suggestions
- SLA tracking and performance metrics
- Multi-channel notifications

## Architecture

### Components

1. **Ticket System** (`ticket_system.py`)
   - Full ticket lifecycle management
   - Priority-based routing
   - SLA tracking
   - Internal notes and collaboration

2. **Knowledge Base** (`knowledge_base.py`)
   - Searchable help articles
   - Quick answers for common questions
   - Article ratings and feedback
   - Related article suggestions

3. **Support API** (`support.py`)
   - RESTful endpoints
   - Authentication and authorization
   - File upload support
   - Admin statistics

## Features

### For Customers

#### Creating Tickets
- Subject and detailed description
- Category selection (billing, technical, etc.)
- Automatic priority assignment
- File attachments
- Suggested articles before submission

#### Ticket Management
- View all tickets and status
- Add messages and replies
- Track resolution progress
- Rate support experience
- Email notifications

#### Knowledge Base
- Full-text search
- Category browsing
- Popular articles
- Quick answers
- Article helpfulness ratings

### For Support Agents

#### Ticket Handling
- Advanced filtering and search
- Bulk actions
- Internal notes
- Status and priority updates
- Assignment management

#### Performance Metrics
- Response time tracking
- Resolution rates
- Customer satisfaction
- SLA compliance
- Agent productivity

## Ticket Workflow

### 1. Creation
```
Customer creates ticket → Auto-response sent → Priority determined → (Optional) Auto-assignment
```

### 2. Assignment
```
Open ticket → Agent assigned → Status: in_progress → First response tracked
```

### 3. Communication
```
Agent replies → Status: waiting_customer → Customer replies → Status: in_progress
```

### 4. Resolution
```
Issue resolved → Status: resolved → Customer notified → Satisfaction survey
```

## Priority System

### Automatic Priority Assignment

Priorities are determined by:
1. **Keywords** in subject/description
2. **User subscription tier**
3. **Category** of issue

### Priority Levels

- **Urgent** (2-hour SLA)
  - Keywords: "urgent", "critical", "down", "broken"
  - Premium users with critical issues
  
- **High** (8-hour SLA)  
  - Billing/payment issues
  - Premium users
  
- **Medium** (24-hour SLA)
  - Pro users
  - Feature requests
  
- **Low** (48-hour SLA)
  - Free users
  - General questions

## Knowledge Base

### Article Structure

```markdown
# Article Title

## Overview
Brief summary of the article

## Prerequisites (if applicable)
What users need before starting

## Steps/Solution
1. Step one
2. Step two
3. Step three

## Additional Resources
- Related articles
- External links
```

### Search Implementation

- PostgreSQL full-text search with tsvector
- Weighted search across title, summary, content, tags
- Relevance ranking
- Typo tolerance

### Quick Answers

Pre-configured instant responses for common queries:
- Password reset
- Plan changes
- Data export
- API access

## Email Notifications

### Customer Notifications

1. **Ticket Created**
   - Confirmation with ticket ID
   - Suggested articles
   - Expected response time

2. **Agent Reply**
   - New message notification
   - Direct link to ticket
   - Reply instructions

3. **Ticket Resolved**
   - Resolution confirmation
   - Satisfaction survey link
   - Reopen instructions

### Agent Notifications

1. **New Ticket** (if assigned)
2. **Customer Reply**
3. **SLA Warning**
4. **Escalation Required**

## SLA Management

### Tracking

```sql
-- First response time
UPDATE support_tickets 
SET first_response_at = NOW()
WHERE id = :ticket_id AND first_response_at IS NULL;

-- Resolution time
UPDATE support_tickets
SET resolved_at = NOW()
WHERE id = :ticket_id;
```

### Breach Detection

```python
sla_deadline = created_at + timedelta(hours=sla_hours[priority])
if datetime.utcnow() > sla_deadline and not first_response_at:
    # SLA breach - trigger alert
```

## Admin Features

### Dashboard Stats

```python
# Real-time metrics
- Total tickets (30 days)
- Open/In Progress/Resolved
- Average resolution time
- Customer satisfaction rate
- Agent performance
```

### Bulk Operations

- Assign multiple tickets
- Change priority/status
- Export ticket data
- Send bulk updates

## Best Practices

### For Support Agents

1. **First Response**
   - Acknowledge receipt
   - Set expectations
   - Request additional info if needed

2. **Communication**
   - Clear and concise
   - Professional tone
   - Regular updates for long issues

3. **Resolution**
   - Verify issue is resolved
   - Provide prevention tips
   - Document solution

### For Administrators

1. **Knowledge Base**
   - Regular content updates
   - Monitor helpfulness ratings
   - Add articles for frequent tickets

2. **Performance**
   - Weekly team reviews
   - SLA compliance monitoring
   - Customer satisfaction analysis

3. **Process Improvement**
   - Identify common issues
   - Update auto-responses
   - Refine priority rules

## API Reference

### Endpoints

#### Tickets
- `POST /api/v1/support/tickets` - Create ticket
- `GET /api/v1/support/tickets` - List tickets
- `GET /api/v1/support/tickets/{id}` - Get ticket details
- `PUT /api/v1/support/tickets/{id}` - Update ticket (admin)
- `POST /api/v1/support/tickets/{id}/messages` - Add message

#### Knowledge Base
- `GET /api/v1/support/kb/search` - Search articles
- `GET /api/v1/support/kb/categories` - List categories
- `GET /api/v1/support/kb/articles/{id}` - Get article
- `POST /api/v1/support/kb/articles/{id}/rate` - Rate article

### Request Examples

#### Create Ticket
```bash
curl -X POST https://api.tradesense.com/api/v1/support/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Cannot export data",
    "description": "Getting error when trying to export trades",
    "category": "technical"
  }'
```

#### Search Knowledge Base
```bash
curl -X GET "https://api.tradesense.com/api/v1/support/kb/search?q=export%20data" \
  -H "Authorization: Bearer $TOKEN"
```

## Database Schema

### Core Tables

1. **support_tickets**
   - Ticket metadata
   - Status tracking
   - Assignment info

2. **support_ticket_messages**
   - Conversation thread
   - Internal notes
   - Attachments

3. **kb_articles**
   - Article content
   - Search vectors
   - View/rating counts

4. **kb_article_ratings**
   - User feedback
   - Helpfulness tracking

## Monitoring

### Key Metrics

1. **Response Times**
   - First response
   - Resolution time
   - By priority/category

2. **Volume**
   - Tickets created
   - Messages sent
   - KB searches

3. **Quality**
   - Customer satisfaction
   - Article helpfulness
   - Reopen rate

### Alerts

Configure alerts for:
- SLA breaches
- High ticket volume
- Low satisfaction scores
- System errors

## Troubleshooting

### Common Issues

1. **Emails Not Sending**
   - Check email service configuration
   - Verify SMTP settings
   - Review email logs

2. **Search Not Working**
   - Rebuild search vectors
   - Check PostgreSQL FTS configuration
   - Verify index exists

3. **Slow Performance**
   - Check database indexes
   - Review query performance
   - Monitor ticket volume

### Maintenance

#### Regular Tasks
- Archive old resolved tickets
- Update KB search vectors
- Clean up orphaned attachments
- Review and update SLA rules

#### Database Maintenance
```sql
-- Rebuild search vectors
UPDATE kb_articles 
SET search_vector = to_tsvector('english', 
    title || ' ' || summary || ' ' || content);

-- Vacuum and analyze
VACUUM ANALYZE support_tickets;
VACUUM ANALYZE kb_articles;
```

## Integration Points

### Email Service
- Ticket notifications
- Auto-responses
- Satisfaction surveys

### Analytics System
- Track ticket metrics
- Monitor agent performance
- Measure customer satisfaction

### Billing System
- Priority based on tier
- Feature access control
- Usage tracking

## Security Considerations

1. **Access Control**
   - Users see only their tickets
   - Admins have full access
   - Internal notes hidden from customers

2. **Data Protection**
   - Sanitize user input
   - Secure file uploads
   - Audit trail for admin actions

3. **Rate Limiting**
   - Ticket creation limits
   - API request throttling
   - Search query limits