from locust import HttpUser, task, between
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Define the host as variable
HOST_URL = os.environ.get('HOST_URL')

class DataFetcherUser(HttpUser):
    wait_time = between(1, 5)  # Simulate wait time between requests (1-5 seconds)

    @task
    def fetch_data(self):
        """Simulates fetching places on webpage loading"""

        try:
            response = self.client.get(f"{HOST_URL}/places")
            response.raise_for_status()  # Raise an exception for non-2xx status codes
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
        else:
            try:
                json_data = response.json()
                if not json_data:
                    raise ValueError("JSON response for places is empty")
                elif len(json_data) != 9:
                    raise ValueError("Incorrect number of places returned")
            except Exception as json_error:
                logger.error(f"Response is not valid JSON: {json_error}")

if __name__ == "__main__":
    from locust import User

    num_users = 2  # Number of simulated users

    # Run locust with the specified number of users and host
    User.locust_class = DataFetcherUser
    os.environ['LOCUST_HOST'] = HOST_URL
    os.system("locust -f locust_get_places_load_balancer.py")
