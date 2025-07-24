import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import uvicorn
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense API Gateway",
    description="Central gateway for TradeSense microservices",
    version="1.0.0"
)

# CORS configuration
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app",
    "https://frontend-jj8nosjl0-tarig-ahmeds-projects.vercel.app",
    "https://frontend-*.vercel.app",
    "https://*.vercel.app",
    "https://tradesense.vercel.app",
    "https://tradesense-*.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Service registry with health status
SERVICES = {
    "auth": {
        "url": os.getenv("AUTH_SERVICE_URL", "http://auth:8000"),
        "health": "unknown",
        "last_check": None
    },
    "trading": {
        "url": os.getenv("TRADING_SERVICE_URL", "http://trading:8000"),
        "health": "unknown",
        "last_check": None
    },
    "analytics": {
        "url": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics:8000"),
        "health": "unknown",
        "last_check": None
    },
    "market-data": {
        "url": os.getenv("MARKET_DATA_SERVICE_URL", "http://market-data:8000"),
        "health": "unknown",
        "last_check": None
    },
    "billing": {
        "url": os.getenv("BILLING_SERVICE_URL", "http://billing:8000"),
        "health": "unknown",
        "last_check": None
    },
    "ai": {
        "url": os.getenv("AI_SERVICE_URL", "http://ai:8000"),
        "health": "unknown",
        "last_check": None
    }
}

# Route mapping
ROUTE_MAP = {
    "auth": ["auth", "users", "login", "register", "refresh"],
    "trading": ["trades", "portfolio", "journal", "notes", "milestones"],
    "analytics": ["analytics", "patterns", "performance", "leaderboard"],
    "market-data": ["market-data", "quotes", "instruments"],
    "billing": ["billing", "subscriptions", "checkout"],
    "ai": ["ai", "intelligence", "insights"]
}

async def check_service_health(service_name: str, service_info: dict):
    """Check health of a single service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{service_info['url']}/health",
                timeout=2.0
            )
            service_info["health"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            service_info["health"] = "unreachable"
            logger.error(f"Health check failed for {service_name}: {e}")
        
        service_info["last_check"] = datetime.utcnow().isoformat()

async def health_check_loop():
    """Background task to check service health"""
    while True:
        tasks = [
            check_service_health(name, info)
            for name, info in SERVICES.items()
        ]
        await asyncio.gather(*tasks)
        await asyncio.sleep(30)  # Check every 30 seconds

@app.on_event("startup")
async def startup_event():
    """Start background health checks"""
    asyncio.create_task(health_check_loop())
    logger.info("API Gateway started")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "TradeSense API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Aggregated health status of all services"""
    # Check our own health
    gateway_health = "healthy"
    
    # Aggregate service health
    services_health = {}
    all_healthy = True
    
    for name, info in SERVICES.items():
        services_health[name] = {
            "status": info["health"],
            "last_check": info["last_check"]
        }
        if info["health"] != "healthy":
            all_healthy = False
    
    overall_status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall_status,
        "gateway": gateway_health,
        "services": services_health,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/services")
async def list_services():
    """List all registered services and their status"""
    return {
        "services": {
            name: {
                "url": info["url"],
                "health": info["health"],
                "last_check": info["last_check"],
                "routes": [r for r, services in ROUTE_MAP.items() if name in r]
            }
            for name, info in SERVICES.items()
        }
    }

def get_target_service(path: str) -> tuple[str, str]:
    """Determine target service from request path"""
    # Remove /api prefix if present
    if path.startswith("api/"):
        path = path[4:]
    
    # Get first path segment
    segments = path.split("/")
    if not segments:
        return None, None
    
    first_segment = segments[0]
    
    # Find matching service
    for service, routes in ROUTE_MAP.items():
        if first_segment in routes:
            return service, path
    
    return None, None

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_api(request: Request, path: str):
    """Proxy requests to appropriate services"""
    # Determine target service
    service_name, service_path = get_target_service(path)
    
    if not service_name or service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"No service found for path: {path}")
    
    service = SERVICES[service_name]
    
    # Check if service is healthy
    if service["health"] == "unreachable":
        raise HTTPException(
            status_code=503,
            detail=f"Service '{service_name}' is currently unavailable"
        )
    
    # Build target URL
    target_url = f"{service['url']}/{service_path}"
    
    # Get request data
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
                timeout=30.0
            )
            
            # Return the response
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Request to service '{service_name}' timed out"
        )
    except Exception as e:
        logger.error(f"Error proxying to {service_name}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with service '{service_name}'"
        )

# Direct auth routes (without /api prefix)
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_auth(request: Request, path: str):
    """Proxy auth requests directly to auth service"""
    service = SERVICES["auth"]
    
    # Check if service is healthy
    if service["health"] == "unreachable":
        raise HTTPException(
            status_code=503,
            detail=f"Auth service is currently unavailable"
        )
    
    # Build target URL
    target_url = f"{service['url']}/auth/{path}"
    
    # Get request data
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
                timeout=30.0
            )
            
            # Return the response
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Request to auth service timed out"
        )
    except Exception as e:
        logger.error(f"Error proxying to auth service: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with auth service"
        )

# Direct routes for other services
@app.api_route("/trades/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_trades(request: Request, path: str):
    return await proxy_to_service(request, "trading", f"trades/{path}")

@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_analytics(request: Request, path: str):
    return await proxy_to_service(request, "analytics", f"analytics/{path}")

@app.api_route("/market-data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_market_data(request: Request, path: str):
    return await proxy_to_service(request, "market-data", f"market-data/{path}")

@app.api_route("/billing/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_billing(request: Request, path: str):
    return await proxy_to_service(request, "billing", f"billing/{path}")

@app.api_route("/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_ai(request: Request, path: str):
    return await proxy_to_service(request, "ai", f"ai/{path}")

async def proxy_to_service(request: Request, service_name: str, path: str):
    """Generic proxy function for services"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    service = SERVICES[service_name]
    
    # Check if service is healthy
    if service["health"] == "unreachable":
        raise HTTPException(
            status_code=503,
            detail=f"Service '{service_name}' is currently unavailable"
        )
    
    # Build target URL
    target_url = f"{service['url']}/{path}"
    
    # Get request data
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
                timeout=30.0
            )
            
            # Return the response
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Request to service '{service_name}' timed out"
        )
    except Exception as e:
        logger.error(f"Error proxying to {service_name}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with service '{service_name}'"
        )

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "gateway": {
            "uptime": "running",
            "version": "1.0.0"
        },
        "services": {
            name: {
                "health": info["health"],
                "last_check": info["last_check"]
            }
            for name, info in SERVICES.items()
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting API Gateway on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)