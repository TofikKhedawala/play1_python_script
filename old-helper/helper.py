
import requests
import os
def store_output(data):
    response = requests.post(f'http://build.play1.io:5000/process-output/{os.getppid()}', json=data)
