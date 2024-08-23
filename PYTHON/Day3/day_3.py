# NASA API Usage Limits and Policies:
# 1. Rate Limits: The default rate limit is 1000 requests per hour.
# 2. API Key: Each user must use their own API key. You can request a personal API key from https://api.nasa.gov/.
# 3. Usage: The API is intended for educational and research purposes.
# 4. Attribution: Proper attribution to NASA is required when using the data.
# 5. Data Integrity: Do not modify the data received from the API.
#%%

# %%
#1-4
import requests
import pprint as pp
import os
import json

def fetch_apod(api_key, start_date, end_date):
    url_apod = "https://api.nasa.gov/planetary/apod" 
    params = {
        'api_key': api_key,
        'start_date': start_date,
        'end_date': end_date,
        'hd': 'True'
    }
    response = requests.get(url_apod, params=params)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return
    
    data = response.json()
    pp.pprint(data)
    
    remaining_requests = response.headers.get('X-RateLimit-Remaining', 'Unknown')
    print("Task 3:")
    print(f"Remaining requests: {remaining_requests}")

    script_directory = os.path.dirname(os.path.abspath(__file__))
    for apod in data:
        date = apod['date']
        filename = f"apod_{date}.json"
        filepath = os.path.join(script_directory, filename)
        with open(filepath, 'w') as file:
            json.dump(apod, file, indent=4)

# Set parameters 
api_key = 'ohnCtAPxXzOOfC09PZZ7tEfvCCEUh75oEKhgIBfZ'
start_date = '2024-08-05'
end_date = '2024-08-06'

print("Task 2:")
fetch_apod(api_key, start_date, end_date)


# %%
#EXTRA 1-2
import requests
import os
import json
from datetime import datetime, timedelta
import time

def fetch_neo_feed(api_key, start_date, nr_of_days, retries=5, backoff_factor=1):
    url_neo_feed = "https://api.nasa.gov/neo/rest/v1/feed"
    
    neo_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neo')
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
            
            print(f"Request URL: {response.url}")
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                for date, neo_data in data['near_earth_objects'].items():
                    filename = f"neo_{date}.json"
                    filepath = os.path.join(neo_directory, filename)
                    with open(filepath, 'w') as file:
                        json.dump(neo_data, file, indent=4)
                
                print(f"Data saved for {current_days} days starting from {start_date_obj.strftime('%Y-%m-%d')}")
                
                remaining_requests = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                print(f"Remaining requests: {remaining_requests}")
                break
            
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {backoff_factor * (2 ** attempt)} seconds...")
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                print(f"Error: Received status code {response.status_code}")
                return
        
        start_date_obj = end_date_obj + timedelta(days=1)
        days_remaining -= current_days
    print("Task EXTRA:")
    print("Data fetching complete.")

api_key = 'ohnCtAPxXzOOfC09PZZ7tEfvCCEUh75oEKhgIBfZ'
start_date = '2024-06-01'
nr_of_days = 20

fetch_neo_feed(api_key, start_date, nr_of_days)


#extra extra
#%%
import socket
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
    available_days = 0

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
                available_days += 1
        
        start_date_obj = end_date_obj + timedelta(days=1)
        days_remaining = 0

    if not all_data:
        return None

    if nr_of_days > available_days:
        return {"error": f"Requested {nr_of_days} days, but only {available_days} days are available locally"}

    return all_data

def format_neo_data(neo_data):
    formatted_data = json.dumps(neo_data, indent=4)
    return formatted_data

api_key = 'ohnCtAPxXzOOfC09PZZ7tEfvCCEUh75oEKhgIBfZ'
start_date = '2024-06-01'

#DEAR COLLEGUE  YOU CAN CHANGE THE NUMBER OF DAYS TO FETCH HERE
nr_of_days = 21

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
    
    if neo_data is None:
        return jsonify({"error": "Data for the specified date range does not exist locally"}), 404
    
    if isinstance(neo_data, dict) and "error" in neo_data:
        return jsonify(neo_data), 400
    
    formatted_neo_data = format_neo_data(neo_data)
    return jsonify(json.loads(formatted_neo_data))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"Running on http://{local_ip}:5000")
    app.run(host='0.0.0.0', port=5000)

#%%
#YOU CAN TEST WITH THIS  /neo_data?start_date=2024-06-01&nr_of_days=10