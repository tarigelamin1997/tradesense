# TradeSense Microservices Quick Start

## Architecture Benefits

Your insight about the monolithic complexity is spot-on! With microservices:
- **Auth service crashes?** Trading still works
- **Bad ML model?** Only analytics affected
- **Stripe issues?** Core app unaffected
- **Deploy updates?** 30 seconds per service, not 5 minutes for everything

## Quick Test (Local)

```bash
# Test microservices locally
docker-compose -f docker-compose.microservices.yml up

# Gateway will be at http://localhost:8000
# Try: http://localhost:8000/health
```

## Deploy to Railway (Production)

### Option 1: Deploy Core Services First
```bash
# Just the essentials to get started
./deploy-microservices.sh
# Select option 4 (Core Services)
```

### Option 2: Manual Service Deployment
```bash
# Deploy Gateway
cd services/gateway
railway init
railway up

# Deploy Auth  
cd ../auth
railway init
railway up

# Deploy Trading
cd ../trading
railway init
railway up
```

## Service URLs (After Deployment)

- Gateway: https://[your-project]-gateway.up.railway.app
- Auth: https://[your-project]-auth.up.railway.app  
- Trading: https://[your-project]-trading.up.railway.app

## Testing the Services

1. **Check Gateway Health**
   ```bash
   curl https://[gateway-url]/health
   ```

2. **Register a User**
   ```bash
   curl -X POST https://[gateway-url]/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","username":"testuser","password":"testpass"}'
   ```

3. **Login**
   ```bash
   curl -X POST https://[gateway-url]/api/auth/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass"
   ```

4. **Create a Trade** (use token from login)
   ```bash
   curl -X POST https://[gateway-url]/api/trades \
     -H "Authorization: Bearer [token]" \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL","action":"buy","quantity":10,"price":150.0}'
   ```

## Service Communication Flow

```
User Request → Gateway → Auth Service → Validate
                ↓
            Trading Service → Database
                ↓
            Response → User
```

## Adding New Services

1. Create service directory:
   ```bash
   mkdir -p services/new-service/src
   ```

2. Copy template files from existing service

3. Deploy:
   ```bash
   cd services/new-service
   railway init
   railway up
   ```

4. Update Gateway route map

## Monitoring

Each service has `/health` endpoint:
- Gateway aggregates all service health
- Individual services report their own status
- Database connectivity included

## Cost Optimization

- Start each service with minimal resources
- Gateway: 256MB RAM
- Auth: 512MB RAM (bcrypt needs memory)
- Trading: 512MB RAM
- Scale only what's actually used

## Rollback Strategy

Service causing issues?
```bash
cd services/problematic-service
railway down  # Service stops but data persists
# Fix the issue
railway up    # Redeploy
```

## Next Steps

1. Deploy Gateway first (it can run standalone)
2. Deploy Auth Service
3. Test Gateway → Auth communication
4. Deploy Trading Service
5. Add remaining services as needed

This approach lets you build incrementally while keeping the system functional at each step!