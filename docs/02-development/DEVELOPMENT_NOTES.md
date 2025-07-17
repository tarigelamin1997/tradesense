# TradeSense Development Notes
**Last Updated:** January 15, 2025  
**For:** Development Team Reference

## Architecture Decisions

### Frontend Architecture
- **Framework:** SvelteKit chosen for performance and DX
- **Routing:** File-based routing without route groups (caused issues)
- **State Management:** Svelte stores for auth, minimal global state
- **Styling:** CSS-in-JS approach, mobile-first responsive design
- **Icons:** Lucide-svelte for consistency and tree-shaking

### Backend Architecture
- **Framework:** FastAPI for async performance and automatic docs
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** JWT with refresh tokens
- **Email:** SMTP service with HTML templates
- **File Handling:** Local filesystem (ready for S3 migration)

### Key Design Patterns

#### Component Patterns
```svelte
<!-- Reusable component with props -->
<script lang="ts">
  export let type: 'primary' | 'secondary' = 'primary';
  export let loading: boolean = false;
  
  // Event dispatching
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
</script>
```

#### API Integration Pattern
```typescript
// Consistent API client usage
import { api } from '$lib/api/client';

async function fetchData() {
  try {
    loading = true;
    const response = await api.get('/endpoint');
    data = response.data;
  } catch (error) {
    // Fallback to sample data
    data = sampleData;
  } finally {
    loading = false;
  }
}
```

#### Mobile-First CSS Pattern
```css
/* Mobile first approach */
.component {
  /* Mobile styles */
}

@media (min-width: 768px) {
  .component {
    /* Desktop enhancements */
  }
}
```

## Common Issues & Solutions

### 1. Route Groups Problem
**Issue:** SvelteKit route groups `(app)` caused routing conflicts  
**Solution:** Use flat route structure without grouping

### 2. String Matching in MultiEdit
**Issue:** MultiEdit tool failed due to whitespace differences  
**Solution:** 
- Always use Read tool first
- Copy exact strings including whitespace
- Use single Edit when MultiEdit fails

### 3. Mobile Tables
**Issue:** Tables unreadable on mobile devices  
**Solution:** Card-based layout with key information

### 4. Authentication State
**Issue:** Auth state not persisting on refresh  
**Solution:** 
```typescript
// Check localStorage on mount
onMount(() => {
  const token = localStorage.getItem('access_token');
  if (token) {
    auth.validateToken(token);
  }
});
```

### 5. CORS Issues
**Issue:** Frontend can't reach backend API  
**Solution:** Configure CORS in FastAPI middleware
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Optimizations

### 1. Loading States
- Use skeleton loaders for perceived performance
- Show skeletons immediately while fetching
- Match skeleton shape to actual content

### 2. API Calls
- Debounce search inputs (300ms)
- Use Promise.all() for parallel requests
- Cache responses where appropriate

### 3. Mobile Performance
- Reduce DOM complexity on mobile
- Use CSS transforms for animations
- Lazy load images and heavy components

### 4. Bundle Size
- Tree-shake icon imports
- Dynamic imports for large components
- Minimize CSS with PurgeCSS

## Testing Approach

### Manual Testing Checklist
1. **Auth Flow**
   - Register new user
   - Verify email
   - Login/logout
   - Password reset

2. **Core Features**
   - Create/edit/delete trades
   - Import CSV
   - Create journal entries
   - View analytics

3. **Mobile Testing**
   - Test on iPhone Safari
   - Test on Android Chrome
   - Check touch targets
   - Verify responsive layouts

4. **Edge Cases**
   - Empty states
   - Error states
   - Large datasets
   - Slow connections

## Security Considerations

### Frontend Security
- Sanitize all user inputs
- Use HTTPS only in production
- Store tokens in httpOnly cookies (future)
- Implement CSP headers

### Backend Security
- Parameterized SQL queries (via ORM)
- Rate limiting on all endpoints
- Input validation with Pydantic
- Secure password hashing (bcrypt)

### API Security
- JWT expiration (1 hour access, 7 days refresh)
- Refresh token rotation
- API key for external integrations
- Request signing for webhooks

## Debugging Tips

### Frontend Debugging
```javascript
// Enable debug logging
localStorage.setItem('debug', 'true');

// Check auth state
console.log(get(isAuthenticated));
console.log(get(auth));

// Inspect API calls
window.__api_calls = [];
api.interceptors.request.use(config => {
  window.__api_calls.push(config);
  return config;
});
```

### Backend Debugging
```python
# Enable SQL query logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Debug specific endpoint
@router.get("/debug")
async def debug_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "user": current_user.dict(),
        "db_connected": db.is_active
    }
```

## Code Snippets

### Protected Route Pattern
```svelte
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { get } from 'svelte/store';
  import { isAuthenticated } from '$lib/api/auth';
  
  onMount(() => {
    if (!get(isAuthenticated)) {
      goto('/login');
    }
  });
</script>
```

### Loading State Pattern
```svelte
{#if loading}
  <LoadingSkeleton type="table" lines={5} />
{:else if error}
  <div class="error">{error}</div>
{:else if data.length === 0}
  <EmptyState message="No data found" />
{:else}
  <!-- Render data -->
{/if}
```

### API Error Handling
```typescript
try {
  const response = await api.post('/trades', tradeData);
  // Success handling
} catch (error: any) {
  if (error.response?.status === 400) {
    // Validation error
    errors = error.response.data.detail;
  } else if (error.response?.status === 401) {
    // Auth error - redirect to login
    goto('/login');
  } else {
    // Generic error
    errorMessage = 'An error occurred. Please try again.';
  }
}
```

## Environment Setup

### Development
```bash
# Backend
cd src/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Backend tests
pytest tests/ -v

# Frontend tests (when implemented)
npm run test
```

### Building
```bash
# Frontend production build
npm run build
npm run preview  # Test production build

# Backend production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Git Workflow

### Branch Strategy
- `main` - Production ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Emergency fixes

### Commit Messages
```
feat: Add global search functionality
fix: Resolve mobile navigation display issue
docs: Update API documentation
style: Format code with Black
refactor: Simplify auth flow
test: Add trade service tests
chore: Update dependencies
```

## Monitoring & Logs

### Key Metrics to Monitor
- API response times (p50, p95, p99)
- Error rates by endpoint
- Active user sessions
- Database query performance
- Background job completion

### Log Locations
- Frontend errors: Browser console + Sentry
- Backend logs: `/var/log/tradesense/app.log`
- Nginx logs: `/var/log/nginx/access.log`
- Database logs: PostgreSQL log directory

### Common Log Queries
```bash
# Find errors in last hour
grep ERROR app.log | tail -n 100

# Monitor API endpoints
grep "POST /api/v1/trades" access.log | tail -f

# Database slow queries
grep "duration:" postgresql.log | awk '{if ($2 > 1000) print}'
```

## Troubleshooting Guide

### Frontend Issues

**Blank page on load**
1. Check browser console for errors
2. Verify API URL in environment
3. Check CORS configuration
4. Clear browser cache

**Authentication not persisting**
1. Check token storage
2. Verify refresh token logic
3. Check cookie settings
4. Review CORS credentials

**Mobile layout broken**
1. Check viewport meta tag
2. Review media queries
3. Test actual devices
4. Check CSS specificity

### Backend Issues

**Database connection errors**
1. Verify DATABASE_URL
2. Check connection pool settings
3. Review firewall rules
4. Test with psql directly

**Email not sending**
1. Verify SMTP credentials
2. Check spam folder
3. Review email logs
4. Test with different provider

**Stripe webhooks failing**
1. Verify webhook secret
2. Check webhook URL
3. Review Stripe logs
4. Test with Stripe CLI

## Future Improvements

### Technical Debt
1. Add comprehensive test suite
2. Implement proper caching strategy
3. Optimize database queries
4. Add request validation middleware

### Feature Enhancements
1. Real-time updates with WebSockets
2. Advanced charting with D3.js
3. Mobile app with React Native
4. AI-powered trade insights

### Infrastructure
1. Implement CI/CD pipeline
2. Add container orchestration
3. Set up blue-green deployments
4. Implement database sharding

## Team Contacts

- **Frontend Issues:** Check with UI/UX team first
- **Backend Issues:** Review logs before escalating
- **Database Issues:** Check query performance first
- **DevOps Issues:** Verify configuration before calling

---

**Remember:** Always test on mobile, handle errors gracefully, and keep the user experience smooth!