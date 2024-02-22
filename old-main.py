from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

import os
import subprocess
import time
import multiprocessing
import json
from flask_cors import CORS
running_processes = {}
process_output = {}


app = Flask(__name__)


CORS(app)
    
    



@app.route('/start-process', methods=['POST'])
def run_script():
    script_data = request.get_json()
    with open('prameters.json', 'w') as json_file:
        json.dump(script_data, json_file)

    if script_data:
        process = subprocess.Popen('/home/buildplay1/public_html/python_script/env/bin/python /home/buildplay1/public_html/python_script/process.py',shell=True, start_new_session=True)
        process_id = process.pid
        process_output[process_id] = 'Process running'
        return jsonify({"process_id": process_id}), 200
    else:
        return jsonify({"error": "Script not provided"}), 400



@app.route('/process-output/<int:process_id>', methods=['GET'])
def get_script_output(process_id):
    print(process_output)
    if process_id in process_output:
        output = process_output[process_id]
        return jsonify(output), 200
    else:
        return jsonify({"error": "Process ID not found"}), 200
    
@app.route('/process-output/<int:process_id>', methods=['POST'])
def add_script_output(process_id):
    print(process_output)
    script_data = request.get_json()
    process_output[process_id] = script_data
    print(process_output)
    return jsonify({}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
