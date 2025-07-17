# TradeSense Admin Dashboard Guide

## Overview

The TradeSense Admin Dashboard provides comprehensive tools for managing users, monitoring system health, analyzing usage patterns, and providing customer support. This guide covers all admin features and best practices.

## Access Control

### Admin Roles
- **Super Admin**: Full system access, can manage other admins
- **Admin**: User management, support, and analytics access
- **Support**: Limited to user support and viewing analytics

### Authentication
- Admin accounts require 2FA (when implemented)
- Session timeout after 30 minutes of inactivity
- All actions are logged for audit purposes

## Dashboard Features

### 1. Main Dashboard

The admin dashboard provides real-time insights:

#### Key Metrics
- **Total Users**: Current registered users
- **Active Users**: DAU, WAU, MAU
- **Revenue**: MRR, growth rate, churn
- **System Health**: Response times, error rates

#### Quick Actions
- View recent signups
- Monitor system issues
- Check revenue trends
- Access user reports

### 2. User Management

#### User List Features
- **Search**: By email, name, or ID
- **Filters**: 
  - Subscription tier (Free, Pro, Premium)
  - Status (Active, Inactive, Suspended)
  - Join date ranges
  - Last activity
- **Sorting**: By join date, last login, email
- **Bulk Actions**: Activate, deactivate, change tier

#### User Details
View comprehensive user information:
- Basic info (email, name, join date)
- Subscription history
- Activity statistics
- Recent actions
- Payment history
- Support tickets

#### User Actions
- **Edit**: Update user information
- **Impersonate**: Login as user (for support)
- **Delete**: Soft delete with data retention
- **Reset Password**: Send password reset email
- **Change Subscription**: Manual tier adjustment

### 3. Analytics Dashboard

#### User Analytics
- User growth trends
- Cohort retention analysis
- Feature adoption rates
- User journey mapping
- Conversion funnels

#### Business Metrics
- Revenue by tier
- Churn analysis
- LTV calculations
- Subscription conversions
- Payment failure rates

#### Engagement Metrics
- Feature usage statistics
- Session duration trends
- Active user patterns
- Peak usage times

### 4. Support System

#### Ticket Management
- View all support tickets
- Filter by status, priority, category
- Assign to team members
- Internal notes and collaboration
- Response time tracking

#### Ticket Actions
- Reply to users
- Change status/priority
- Escalate issues
- Add internal notes
- View user context

### 5. System Administration

#### Configuration
- Feature flags management
- System announcements
- Maintenance mode
- API rate limits
- Email templates

#### Monitoring
- Real-time system health
- Error logs and alerts
- Performance metrics
- Database statistics
- Cache performance

## Common Admin Tasks

### Managing Subscriptions

#### Upgrade User
1. Find user in Users list
2. Click Edit
3. Change subscription_tier to desired plan
4. Save changes
5. User receives confirmation email

#### Handle Failed Payments
1. View user's payment history
2. Check Stripe dashboard for details
3. Contact user if needed
4. Manually retry or update payment method

### User Support

#### Investigating Issues
1. Search for user
2. View recent activity
3. Check error logs
4. Review analytics events
5. Impersonate if needed

#### Common Support Scenarios

**Password Reset**
```
1. Verify user identity
2. Click "Send Password Reset"
3. Confirm email sent
4. Note in user record
```

**Data Issues**
```
1. Check user's recent trades
2. View activity logs
3. Verify data integrity
4. Restore from backup if needed
```

**Subscription Issues**
```
1. Check payment history
2. Verify Stripe status
3. Review subscription changes
4. Manually adjust if needed
```

### Bulk Operations

#### Export User Data
1. Go to Users page
2. Apply desired filters
3. Click "Export"
4. Choose format (CSV/JSON)
5. Download file

#### Bulk Email
1. Select target users
2. Choose "Send Email" action
3. Select template or custom
4. Preview and confirm
5. Monitor delivery

## Security Best Practices

### Access Control
- Use strong, unique passwords
- Enable 2FA when available
- Regularly review admin access
- Remove inactive admin accounts

### Data Protection
- Never share user passwords
- Use impersonation sparingly
- Log reasons for sensitive actions
- Follow data retention policies

### Audit Trail
All admin actions are logged:
- User modifications
- Impersonations
- Data exports
- System changes

## Monitoring & Alerts

### Key Metrics to Monitor
1. **User Growth**: New signups, activation rate
2. **Revenue**: MRR changes, churn rate
3. **Engagement**: Active users, feature usage
4. **Support**: Ticket volume, response time
5. **System**: Error rates, performance

### Alert Thresholds
- High error rate (>5%)
- Unusual user activity patterns
- Payment failure spikes
- Support ticket backlog
- System performance degradation

## Reports

### Available Reports
1. **User Growth Report**: Monthly/quarterly growth
2. **Revenue Report**: MRR, churn, LTV analysis
3. **Engagement Report**: Feature usage, retention
4. **Support Report**: Ticket metrics, satisfaction
5. **System Health Report**: Uptime, performance

### Generating Reports
1. Navigate to Analytics section
2. Select report type
3. Choose date range
4. Apply filters if needed
5. Export or schedule

## Troubleshooting

### Common Issues

#### User Can't Login
1. Check user status (active/inactive)
2. Verify email confirmation
3. Review recent password resets
4. Check for account locks

#### Missing Data
1. Check user's activity log
2. Verify data in database
3. Review recent changes
4. Check for sync issues

#### Payment Problems
1. Check Stripe webhook logs
2. Verify webhook configuration
3. Review payment method
4. Check for declined charges

### Escalation Path
1. **Level 1**: Support team handles basic issues
2. **Level 2**: Admin team for account/payment issues
3. **Level 3**: Technical team for bugs/data issues
4. **Level 4**: Engineering lead for critical issues

## Best Practices

### Daily Tasks
- Review overnight signups
- Check system health metrics
- Monitor support queue
- Address urgent tickets

### Weekly Tasks
- Review user growth metrics
- Analyze support trends
- Check payment failures
- Update team on issues

### Monthly Tasks
- Generate growth reports
- Review churn analysis
- Audit admin access
- Update documentation

## API Access

### Admin API Endpoints
- `GET /api/v1/admin/dashboard/stats` - Dashboard statistics
- `GET /api/v1/admin/users` - User list with filters
- `GET /api/v1/admin/users/{id}` - User details
- `PUT /api/v1/admin/users/{id}` - Update user
- `POST /api/v1/admin/users/bulk-action` - Bulk operations

### Authentication
Use admin role JWT token:
```
Authorization: Bearer <admin-token>
```

## Emergency Procedures

### High Error Rate
1. Check error logs
2. Identify affected endpoints
3. Scale services if needed
4. Notify engineering team

### Data Breach
1. Immediately notify security team
2. Disable affected accounts
3. Reset all passwords
4. Document incident
5. Follow breach protocol

### System Outage
1. Verify outage scope
2. Activate incident response
3. Communicate status
4. Coordinate recovery
5. Post-mortem analysis

## Contact Information

### Internal Escalation
- Support Team: support-team@tradesense.com
- Engineering: engineering@tradesense.com
- Security: security@tradesense.com
- Management: management@tradesense.com

### External Resources
- Stripe Support: https://support.stripe.com
- AWS Support: AWS Console
- Status Page: https://status.tradesense.com