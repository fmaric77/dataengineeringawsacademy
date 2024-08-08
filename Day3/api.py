#%%
import requests
import os
import json
from datetime import datetime, timedelta
import time
from flask import Flask, jsonify, request
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def fetch_neo_feed(api_key, start_date, nr_of_days, retries=5, backoff_factor=1):
    url_neo_feed = "https://api.nasa.gov/neo/rest/v1/feed"
    
    neo_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neo_flask')
    if not os.path.exists(neo_directory):
        os.makedirs(neo_directory)

    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    days_remaining = nr_of_days

    while days_remaining > 0:
        current_days = min(days_remaining, 7)
        end_date_obj = start_date_obj + timedelta(days=current_days - 1)
        end_date = end_date_obj.strftime('%Y-%m-%d')
        
        params = {
            'api_key': api_key,
            'start_date': start_date_obj.strftime('%Y-%m-%d'),
            'end_date': end_date
        }

        for attempt in range(retries):
            response = requests.get(url_neo_feed, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for date, neo_data in data['near_earth_objects'].items():
                    filename = f"neo_{date}.json"
                    filepath = os.path.join(neo_directory, filename)
                    with open(filepath, 'w') as file:
                        json.dump(neo_data, file, indent=4)
                
                remaining_requests = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                break
            
            elif response.status_code == 429:
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                return

        start_date_obj = end_date_obj + timedelta(days=1)
        days_remaining -= current_days

def read_neo_data(start_date, nr_of_days):
    neo_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neo_flask')
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    days_remaining = nr_of_days

    all_data = []

    while days_remaining > 0:
        end_date_obj = start_date_obj + timedelta(days=days_remaining - 1)
        
        for single_date in (start_date_obj + timedelta(n) for n in range(days_remaining)):
            date_str = single_date.strftime('%Y-%m-%d')
            filename = f"neo_{date_str}.json"
            filepath = os.path.join(neo_directory, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    neo_data = json.load(file)
                    all_data.append({date_str: neo_data})
        
        start_date_obj = end_date_obj + timedelta(days=1)
        days_remaining = 0

    return all_data

def format_neo_data(neo_data):
    formatted_data = json.dumps(neo_data, indent=4)
    return formatted_data

api_key = 'ohnCtAPxXzOOfC09PZZ7tEfvCCEUh75oEKhgIBfZ'
start_date = '2024-06-01'
nr_of_days = 20

fetch_neo_feed(api_key, start_date, nr_of_days)

neo_data = read_neo_data(start_date, nr_of_days)

formatted_neo_data = format_neo_data(neo_data)
print(formatted_neo_data)

app = Flask(__name__)

@app.route('/neo_data', methods=['GET'])
def get_neo_data():
    start_date = request.args.get('start_date')
    nr_of_days = request.args.get('nr_of_days')
    
    if not start_date or not nr_of_days:
        return jsonify({"error": "Missing required parameters: start_date and/or nr_of_days"}), 400
    
    try:
        nr_of_days = int(nr_of_days)
    except ValueError:
        return jsonify({"error": "nr_of_days must be an integer"}), 400
    
    neo_data = read_neo_data(start_date, nr_of_days)
    formatted_neo_data = format_neo_data(neo_data)
    return jsonify(json.loads(formatted_neo_data))

if __name__ == '__main__':
    print("Running on http://192.168.144.208:5000")
    app.run(host='0.0.0.0', port=5000)

#%%
#TEST -http://192.168.144.208:5000/neo_data?start_date=2024-06-01&nr_of_days=10