from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import subprocess
import time
import multiprocessing
import json
from flask_cors import CORS
running_processes = False
process_output = {}


app = Flask(__name__)
CORS(app)
    
    



@app.route('/start-process', methods=['POST'])
def run_script():
    global running_processes
    if running_processes:
        return jsonify({"error": "process is running please wait"}), 400

    script_data = request.get_json()
    with open('prameters.json', 'w') as json_file:
        json.dump(script_data, json_file)

    if script_data:
        try:
            os.remove('output.json')
        except OSError:
            print()
        process = subprocess.Popen('/home/ubuntu/Desktop/projects/play1/python-script/python_script/env/bin/python /home/ubuntu/Desktop/projects/play1/python-script/python_script/process.py', shell=True)        
        print("*****",process)
        running_processes=True
        return jsonify({"process_id": 0,"message":'process started'}), 200
    else:
        return jsonify({"error": "Script not provided"}), 400



@app.route('/process-output', methods=['GET'])
def get_script_output():
    try:
        with open('output.json', 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "No result to display"}), 200

    
@app.route('/process-output', methods=['POST'])
def add_script_output():
    global running_processes
    script_data = request.get_json()
    if "COMPLETED" in script_data:
        running_processes = False
    else:
        with open('output.json', 'w') as json_file:
            json.dump(script_data, json_file)
    return jsonify({}), 200


if __name__ == '__main__':
    # context = ('/home/buildplay1/ssl/certs/build_play1_io_afaba_bff63_1710547199_0d929fb9539bac1444fa8583cab7fe4c.crt', '/home/buildplay1/ssl/keys/afaba_bff63_38270abaadba48d0ba500830aa8717e7.key')#certificate and key files
    # app.run(debug=True,ssl_context=context,host='0.0.0.0')
    app.run(debug=True)
