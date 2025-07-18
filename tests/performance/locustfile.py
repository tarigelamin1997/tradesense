"""
Load Testing Suite for TradeSense API

Uses Locust for distributed load testing with realistic user scenarios.
"""
import random
import json
import time
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import pandas as pd
import numpy as np


class TradesenseUser(HttpUser):
    """Simulates a typical TradeSense user"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.user_id = None
        self.trade_ids = []
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Try to login or register
        if random.random() < 0.8:  # 80% login, 20% register
            self.login()
        else:
            self.register()
    
    def on_stop(self):
        """Called when a simulated user stops"""
        pass
    
    def login(self):
        """Login with test credentials"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"testuser{random.randint(1, 100)}@example.com",
                "password": "testpassword123"
            },
            catch_response=True
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
    
    def register(self):
        """Register a new user"""
        timestamp = int(time.time())
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": f"newuser{timestamp}@example.com",
                "password": "testpassword123",
                "full_name": f"Test User {timestamp}"
            },
            catch_response=True
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
            response.success()
        else:
            response.failure(f"Registration failed: {response.status_code}")
    
    @task(3)
    def view_dashboard(self):
        """View dashboard (most common action)"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get dashboard data
        self.client.get("/api/v1/analytics/dashboard", headers=headers)
        
        # Get recent trades
        self.client.get("/api/v1/trades?limit=20", headers=headers)
    
    @task(2)
    def view_analytics(self):
        """View analytics pages"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Random analytics endpoint
        endpoints = [
            "/api/v1/analytics/performance",
            "/api/v1/analytics/win-rate",
            "/api/v1/analytics/profit-loss",
            "/api/v1/analytics/streaks",
            "/api/v1/analytics/heatmap"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=headers)
    
    @task(1)
    def create_trade(self):
        """Create a new trade"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Generate realistic trade data
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "AMD"]
        
        trade_data = {
            "symbol": random.choice(symbols),
            "trade_type": random.choice(["BUY", "SELL"]),
            "quantity": random.randint(1, 100),
            "entry_price": round(random.uniform(100, 500), 2),
            "exit_price": round(random.uniform(100, 500), 2),
            "entry_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "exit_date": datetime.now().isoformat(),
            "profit_loss": round(random.uniform(-1000, 1000), 2),
            "notes": "Load test trade"
        }
        
        response = self.client.post(
            "/api/v1/trades",
            json=trade_data,
            headers=headers,
            catch_response=True
        )
        
        if response.status_code in [200, 201]:
            trade_id = response.json().get("id")
            if trade_id:
                self.trade_ids.append(trade_id)
            response.success()
        else:
            response.failure(f"Trade creation failed: {response.status_code}")
    
    @task(1)
    def upload_csv(self):
        """Upload trades via CSV"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Generate CSV data
        csv_data = self._generate_csv_data()
        
        files = {"file": ("trades.csv", csv_data, "text/csv")}
        
        response = self.client.post(
            "/api/v1/trades/upload",
            files=files,
            headers=headers,
            catch_response=True
        )
        
        if response.status_code in [200, 201]:
            response.success()
        else:
            response.failure(f"CSV upload failed: {response.status_code}")
    
    @task(1)
    def search_trades(self):
        """Search and filter trades"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Random search parameters
        params = {
            "symbol": random.choice(["AAPL", "GOOGL", "MSFT", ""]),
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "min_profit": random.choice([-100, 0, 100, ""]),
            "limit": 50
        }
        
        # Remove empty params
        params = {k: v for k, v in params.items() if v}
        
        self.client.get("/api/v1/trades", params=params, headers=headers)
    
    @task(1)
    def view_journal(self):
        """View journal entries"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get journal entries
        self.client.get("/api/v1/journal/entries", headers=headers)
        
        # Create journal entry
        if random.random() < 0.3:  # 30% chance
            self.client.post(
                "/api/v1/journal/entries",
                json={
                    "title": f"Test Entry {int(time.time())}",
                    "content": "Load test journal entry",
                    "mood": random.choice(["positive", "neutral", "negative"]),
                    "tags": ["test", "load-testing"]
                },
                headers=headers
            )
    
    def _generate_csv_data(self):
        """Generate realistic CSV trade data"""
        num_trades = random.randint(5, 20)
        trades = []
        
        for _ in range(num_trades):
            symbol = random.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"])
            entry_price = round(random.uniform(100, 500), 2)
            exit_price = round(entry_price * random.uniform(0.95, 1.05), 2)
            quantity = random.randint(1, 100)
            
            trades.append({
                "symbol": symbol,
                "trade_type": random.choice(["BUY", "SELL"]),
                "quantity": quantity,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "entry_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                "exit_date": datetime.now().strftime("%Y-%m-%d"),
                "profit_loss": round((exit_price - entry_price) * quantity, 2)
            })
        
        df = pd.DataFrame(trades)
        return df.to_csv(index=False)


class PowerUser(TradesenseUser):
    """Simulates a power user with more intensive usage patterns"""
    
    wait_time = between(0.5, 2)  # Faster interactions
    
    @task(5)
    def complex_analytics(self):
        """Run complex analytics queries"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Multiple analytics requests in sequence
        endpoints = [
            "/api/v1/analytics/advanced/confidence-analysis",
            "/api/v1/analytics/advanced/pattern-detection",
            "/api/v1/analytics/advanced/risk-assessment",
            "/api/v1/analytics/advanced/market-correlation"
        ]
        
        for endpoint in random.sample(endpoints, 2):
            self.client.get(endpoint, headers=headers)
    
    @task(3)
    def bulk_operations(self):
        """Perform bulk operations"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Bulk trade creation
        trades = []
        for _ in range(50):
            trades.append({
                "symbol": random.choice(["AAPL", "GOOGL", "MSFT"]),
                "trade_type": "BUY",
                "quantity": random.randint(1, 100),
                "entry_price": round(random.uniform(100, 200), 2),
                "entry_date": datetime.now().isoformat()
            })
        
        self.client.post(
            "/api/v1/trades/bulk",
            json={"trades": trades},
            headers=headers
        )
    
    @task(2)
    def export_data(self):
        """Export data in various formats"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Export trades
        format_type = random.choice(["csv", "json", "pdf"])
        self.client.get(
            f"/api/v1/trades/export?format={format_type}",
            headers=headers
        )


class APIUser(HttpUser):
    """Simulates API integration usage"""
    
    wait_time = between(0.1, 1)  # Very fast API calls
    
    def on_start(self):
        """Get API key"""
        # In real scenario, this would use API key authentication
        self.api_key = "test_api_key_12345"
    
    @task(10)
    def api_get_trades(self):
        """API endpoint to get trades"""
        headers = {"X-API-Key": self.api_key}
        
        self.client.get(
            "/api/v1/trades",
            headers=headers,
            params={"limit": 100}
        )
    
    @task(5)
    def api_create_trade(self):
        """API endpoint to create trade"""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        trade_data = {
            "symbol": random.choice(["BTC", "ETH", "SOL"]),
            "trade_type": "BUY",
            "quantity": round(random.uniform(0.01, 1), 4),
            "entry_price": round(random.uniform(1000, 50000), 2),
            "entry_date": datetime.now().isoformat()
        }
        
        self.client.post(
            "/api/v1/trades",
            json=trade_data,
            headers=headers
        )
    
    @task(2)
    def api_analytics(self):
        """API endpoint for analytics"""
        headers = {"X-API-Key": self.api_key}
        
        self.client.get(
            "/api/v1/analytics/summary",
            headers=headers
        )


# Event hooks for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Custom metric collection"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response.status_code >= 400:
        print(f"HTTP error: {name} - {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")
    print(f"Total users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate test report"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failure rate: {environment.stats.total.fail_ratio:.2%}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.current_rps:.2f}")


# Custom load shape for realistic traffic patterns
from locust import LoadTestShape

class StagesShape(LoadTestShape):
    """
    A load test shape that gradually increases users in stages
    
    Stages:
    1. Warm-up: 0-2 min, 0-10 users
    2. Normal load: 2-5 min, 10-50 users
    3. Peak load: 5-8 min, 50-100 users
    4. Stress test: 8-10 min, 100-200 users
    5. Cool down: 10-12 min, 200-10 users
    """
    
    stages = [
        {"duration": 120, "users": 10, "spawn_rate": 1},      # Warm-up
        {"duration": 300, "users": 50, "spawn_rate": 2},      # Normal
        {"duration": 480, "users": 100, "spawn_rate": 5},     # Peak
        {"duration": 600, "users": 200, "spawn_rate": 10},    # Stress
        {"duration": 720, "users": 10, "spawn_rate": 5},      # Cool down
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        
        return None