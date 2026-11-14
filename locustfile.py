import os

from gevent.lock import Semaphore
from locust import HttpUser, between, task
from locust.exception import StopUser

REQUEST_LIMIT = int(os.getenv("REQUEST_LIMIT", "100"))
claimed_requests = 0
# Gevent users share this lock so each benchmark CSV has an exact request total.
counter_lock = Semaphore()


def claim_request() -> bool:
    global claimed_requests
    with counter_lock:
        if claimed_requests >= REQUEST_LIMIT:
            return False
        claimed_requests += 1
        return True


class ReadUser(HttpUser):
    wait_time = between(0.01, 0.05)

    @task
    def list_products(self) -> None:
        if not claim_request():
            raise StopUser
        self.client.get("/resource?skip=0&limit=10", name="GET /resource")
