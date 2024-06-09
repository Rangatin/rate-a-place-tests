from locust import HttpUser, SequentialTaskSet, task, between
import os
import logging
import random
import json

from locust import User
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Define the host as variable
HOST_URL = os.environ.get('HOST_URL')

class UpdatePlaceTaskSet(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.place = {}
        self.place_id = ""
        self.user_rating = random.randint(0, 5)
        self.rounded_new_rating = 0

    @task
    def get_initial_places(self):
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
                else:
                    self.place = random.choice(json_data)
                    self.place_id = self.place["PlaceId"]
                    logger.info(f"Random place selected {self.place_id}")
            except Exception as json_error:
                logger.error(f"Response is not valid JSON: {json_error}")

    @task
    def update_place(self):
        new_num_ratings =  int(self.place["NumRatings"]) + 1
        calculated_new_rating = (float(self.place["AverageRating"]) * (new_num_ratings - 1) + self.user_rating) / (new_num_ratings)
        self.rounded_new_rating = round(calculated_new_rating, 2)

        data = {
            "PlaceId": self.place_id,
            "AverageRating": self.rounded_new_rating,
            "NumRatings": new_num_ratings
        }
        
        try:
            response = self.client.patch(f"{HOST_URL}/places", json=data)
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            logger.info(f"Updated place: {self.place_id}")
        except Exception as e:
            logger.error(f"Error updating place {self.place_id}: {e}")

    @task
    def verify_update(self):
        try:
            response = self.client.get(f"{HOST_URL}/places?PlaceId={self.place_id}")
            response.raise_for_status()  # Raise an exception for non-2xx status codes
        except Exception as e:
            logger.error(f"Error fetching place {self.place_id}: {e}")
            return

        try:
            place_data = response.json()
            expected_structure = {
                "PlaceId": self.place["PlaceId"],
                "AverageRating": self.rounded_new_rating,
                "NumRatings": int(self.place["NumRatings"]) + 1,
                "Longitude": self.place["Longitude"],
                "ImageUrl": self.place["ImageUrl"],
                "Latitude":self.place["Latitude"],
                "Description": self.place["Description"],
                "Name": self.place["Name"]
            }
            assert place_data == expected_structure, f"Response structure mismatch for place {self.place_id}"
            logger.info(f"Place {self.place_id} data: {place_data}")
        except Exception as json_error:
            logger.error(f"Response for place {self.place_id} is not valid JSON: {json_error}")

class UpdatePlaceUser(HttpUser):
  wait_time = between(1, 5)  # Optional wait time between user iterations
  tasks = [UpdatePlaceTaskSet]


if __name__ == "__main__":
    num_users = 2  # Number of simulated users

    # Run locust with the specified number of users and host
    User.locust_class = UpdatePlaceUser
    os.environ['LOCUST_HOST'] = HOST_URL
    os.system("locust -f locust_rate_place_load_balancer.py")
