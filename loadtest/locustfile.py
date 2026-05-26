from locust import HttpUser, between, task


class NodeRegistryUser(HttpUser):
    """Simulates a client hammering the Node Registry API."""

    wait_time = between(0.5, 2)

    @task(5)
    def health_check(self):
        """GET /health — lightweight probe; keeps the HPA CPU metric warm."""
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(4)
    def list_nodes(self):
        """GET /api/nodes — list all registered nodes."""
        with self.client.get("/api/nodes", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(3)
    def get_node(self):
        """GET /api/nodes/{name} — fetch a specific node (may 404, that's fine)."""
        with self.client.get("/api/nodes/load-test-node-0", catch_response=True) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(2)
    def register_and_delete_node(self):
        """POST /api/nodes then DELETE — full lifecycle in one task."""
        import random
        import string

        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        name = f"load-test-{suffix}"
        payload = {"name": name, "host": "10.0.0.1", "port": random.randint(1024, 65535)}

        with self.client.post("/api/nodes", json=payload, catch_response=True) as resp:
            if resp.status_code in (201, 409):
                resp.success()
            else:
                resp.failure(f"POST /api/nodes returned {resp.status_code}")
                return 
            
        with self.client.delete(f"/api/nodes/{name}", catch_response=True) as resp:
            if resp.status_code in (204, 404):
                resp.success()
            else:
                resp.failure(f"DELETE /api/nodes/{name} returned {resp.status_code}")

    @task(1)
    def update_node(self):
        """PUT /api/nodes/{name} — update host/port of a known node."""
        import random

        payload = {"host": "10.0.0.2", "port": random.randint(1024, 65535)}
        with self.client.put(
            "/api/nodes/load-test-node-0", json=payload, catch_response=True
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"PUT returned {resp.status_code}")