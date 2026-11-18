# Backend-Frontend Coordination Points

## 🚨 CRITICAL: Authentication Pattern

### The Agreement
Frontend and Backend MUST agree on authentication pattern **before any implementation**.

### Current Status
- **Frontend**: Built expecting **httpOnly cookies** ✅ (More secure)
- **Backend**: Might use **JWT in response body** ❌ (Will break)

### Why This Matters
If backend returns JWT in response body but frontend expects cookies:
1. Login appears to work
2. But ALL subsequent API calls fail with 401
3. Users cannot access any protected features
4. **100% authentication failure**

### Required Implementation

#### Backend MUST:
```python
# Set httpOnly cookie on login
response.set_cookie(
    key="auth-token",
    value=access_token,
    httponly=True,
    secure=True,  # HTTPS only
    samesite="lax",
    max_age=86400
)

# Accept cookies for authentication
token = Cookie(None, alias="auth-token")
```

#### Frontend Already:
```typescript
// Sends credentials
credentials: 'include'

// Does NOT store tokens
// Does NOT set Authorization headers
// Relies on browser cookie handling
```

### CORS Requirements
```python
# Backend MUST configure CORS for cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins
    allow_credentials=True,  # ← REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## Other Coordination Points

### 1. API Response Format
- Frontend expects consistent error format
- All errors should include: `{ error: string, message: string, details?: any }`

### 2. Date/Time Format
- All timestamps in ISO 8601 format
- UTC timezone for storage
- Frontend handles timezone conversion

### 3. File Upload
- Frontend sends multipart/form-data
- Backend must handle file size limits
- Progress tracking via WebSocket

### 4. WebSocket Events
- Event names must match exactly
- Payload structure agreed upon
- Authentication via query param or cookie

### 5. Pagination
- Consistent pagination structure
- Frontend expects: `{ data: [], total: number, page: number, limit: number }`

## Communication Protocol

1. **Before implementing any API endpoint:**
   - Backend provides endpoint specification
   - Frontend reviews and confirms
   - Both implement with agreed contract

2. **Before changing authentication:**
   - Must be discussed in team meeting
   - Both sides must update together
   - Requires coordinated deployment

3. **API Breaking Changes:**
   - Use versioning (/v1, /v2)
   - Deprecation notice period
   - Migration guide required

## Testing Coordination

### Integration Tests Must Cover:
- Authentication flow (login → protected endpoint)
- Error handling
- File uploads
- WebSocket connections
- CORS behavior

### Shared Test Data:
```json
{
  "testUser": {
    "email": "test@example.com",
    "password": "TestPass123!",
    "name": "Test User"
  }
}
```

## Deployment Coordination

1. **Backend deployed first** (new endpoints)
2. **Frontend deployed after** (uses new endpoints)
3. **Database migrations** before backend
4. **Feature flags** for gradual rollout

## Current Action Items

- [ ] Backend: Implement httpOnly cookie authentication
- [ ] Backend: Test with frontend locally
- [ ] DevOps: Ensure CORS configured correctly
- [ ] QA: Test full authentication flow
- [ ] Team: Document any other mismatches

---

**Remember**: A mismatch in expectations = production failure. Always coordinate!