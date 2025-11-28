"""
Load testing for Good Shepherd API using Locust.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --headless -u 100 -r 10 --run-time 60s
"""

import random
import uuid
from locust import HttpUser, task, between, events


class GoodShepherdUser(HttpUser):
    """Simulates a typical Good Shepherd API user."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.user_id = f"load-test-{uuid.uuid4().hex[:8]}"
        self.admin_key = "test-admin-key"  # For admin endpoints
    
    @task(10)
    def health_check(self):
        """High frequency: Health check endpoint."""
        self.client.get("/api/health")
    
    @task(5)
    def list_geofences(self):
        """Medium frequency: List all geofences."""
        self.client.get("/api/geofences")
    
    @task(3)
    def update_location(self):
        """Medium frequency: Update user location."""
        # Simulate location around New York area
        lat = 40.7128 + random.uniform(-0.1, 0.1)
        lon = -74.0060 + random.uniform(-0.1, 0.1)
        
        self.client.post(
            "/api/location/update",
            json={
                "user_id": self.user_id,
                "latitude": lat,
                "longitude": lon,
                "accuracy_meters": random.uniform(5, 50),
            },
        )
    
    @task(2)
    def get_threat_level(self):
        """Lower frequency: Get user threat level."""
        self.client.get(f"/api/location/{self.user_id}/threat-level")
    
    @task(1)
    def get_nearby_threats(self):
        """Low frequency: Get nearby threats."""
        lat = 40.7128 + random.uniform(-0.1, 0.1)
        lon = -74.0060 + random.uniform(-0.1, 0.1)
        
        self.client.get(
            "/api/location/nearby-threats",
            params={
                "latitude": lat,
                "longitude": lon,
                "radius_km": 50,
            },
        )


class AdminUser(HttpUser):
    """Simulates an admin user performing management tasks."""
    
    wait_time = between(5, 15)  # Admins are less frequent
    weight = 1  # 1 admin for every 10 regular users
    
    def on_start(self):
        """Called when admin user starts."""
        self.admin_key = "test-admin-key"
        self.headers = {"X-Admin-API-Key": self.admin_key}
        self.created_geofences = []
    
    @task(3)
    def create_geofence(self):
        """Create a test geofence."""
        lat = 40.7128 + random.uniform(-1, 1)
        lon = -74.0060 + random.uniform(-1, 1)
        
        response = self.client.post(
            "/api/geofences/circle",
            json={
                "name": f"Load Test Zone {uuid.uuid4().hex[:6]}",
                "center": {"latitude": lat, "longitude": lon},
                "radius_km": random.uniform(5, 50),
                "threat_level": random.choice(["caution", "warning", "danger"]),
                "description": "Created by load test",
            },
            headers=self.headers,
        )
        
        if response.status_code == 201:
            data = response.json()
            self.created_geofences.append(data["id"])
    
    @task(2)
    def list_subscriptions(self):
        """List digest subscriptions."""
        self.client.get(
            "/api/digests/subscriptions",
            headers=self.headers,
        )
    
    @task(1)
    def cleanup_geofence(self):
        """Delete a previously created geofence."""
        if self.created_geofences:
            geofence_id = self.created_geofences.pop()
            self.client.delete(
                f"/api/geofences/{geofence_id}",
                headers=self.headers,
            )


class WebSocketUser(HttpUser):
    """Simulates WebSocket connections (connection test only)."""
    
    wait_time = between(10, 30)
    weight = 2  # Some WebSocket users
    
    @task
    def websocket_stats(self):
        """Check WebSocket stats endpoint."""
        self.client.get("/api/ws/stats")


# Event hooks for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests."""
    if response_time > 1000:  # > 1 second
        print(f"SLOW REQUEST: {request_type} {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("=" * 60)
    print("Good Shepherd Load Test Starting")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("=" * 60)
    print("Good Shepherd Load Test Complete")
    print("=" * 60)
