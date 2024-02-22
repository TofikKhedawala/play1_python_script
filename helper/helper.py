
import requests
import os
def store_output(data):
    response = requests.post(f'http://127.0.0.1:5000/process-output', json=data, verify=False)
