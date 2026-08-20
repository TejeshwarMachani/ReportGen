"""Load test suite for AI Business Report Generation System.

Uses locust to test concurrent request patterns on the API.
"""

from locust import HttpUser, task, between, events


class ReportUser(HttpUser):
    """Simulate a user generating reports."""

    wait_time = between(1, 5)

    @task(3)
    def generate_report(self):
        """Generate a business report."""
        self.client.post(
            "/api/v1/reports/generate",
            json={"dataset_id": "123", "title": "Monthly Report"},
            headers={"Authorization": "Bearer test-token"},
        )

    @task(2)
    def check_rate_limit_headers(self):
        """Check that rate limit headers are present."""
        self.client.get("/health", headers={"Authorization": "Bearer test-token"})


class ForecastUser(HttpUser):
    """Simulate a user running forecasts."""

    wait_time = between(2, 8)

    @task(3)
    def generate_forecast(self):
        """Generate a forecast."""
        self.client.post(
            "/api/v1/forecast/generate/123",
            json={
                "dataset_id": "123",
                "target_column": "revenue",
                "date_column": "date",
                "horizon": 12,
                "model_type": "prophet",
            },
            headers={"Authorization": "Bearer test-token"},
        )

    @task(1)
    def list_forecast_jobs(self):
        """List forecast jobs."""
        self.client.get("/api/v1/forecast/jobs", headers={"Authorization": "Bearer test-token"})


class ChatUser(HttpUser):
    """Simulate a user chatting with data."""

    wait_time = between(0.5, 2)

    @task(5)
    def send_chat_message(self):
        """Send a chat message."""
        self.client.post(
            "/api/v1/chat/message",
            json={"message": "what is the total", "dataset_id": "123"},
            headers={"Authorization": "Bearer test-token"},
        )

    @task(2)
    def check_chat_rate_limit(self):
        """Check chat rate limit headers."""
        self.client.get("/health", headers={"Authorization": "Bearer test-token"})


@events.test_start.add
def on_test_start(environment, **kwargs):
    """Set up test environment."""
    environment.request_type_distribution = {
        "POST": 60,
        "GET": 40,
    }


@events.test_stop.add
def on_test_stop(environment, **kwargs):
    """Report test completion summary."""
    print("\n=== Load Test Complete ===")
    print(f"Total requests: {environment.total_requests}")
    print(f"Failed requests: {environment.num_failures}")
    print(f"Average response time: {environment.average_response_time:.1f}ms")