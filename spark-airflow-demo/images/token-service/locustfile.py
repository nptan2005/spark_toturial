# from locust import HttpUser, task, between

# class TokenUser(HttpUser):
#     wait_time = between(0.1, 0.5)

#     @task
#     def generate_token(self):
#         self.client.post("/token", json={"value": "abc"})

#run test locust -f locustfile.py --host=http://localhost:5000
# http://localhost:8089 , user:1000, Spawn rate: 200