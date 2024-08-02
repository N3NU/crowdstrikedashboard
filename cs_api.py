import requests
from datetime import datetime
import pytz

#GET LOCAL DATE
dt_us_central = datetime.now(pytz.timezone('US/Eastern'))
new_york_date = dt_us_central.strftime("%d")
new_york_month = dt_us_central.strftime("%m")
new_york_year = dt_us_central.strftime("%Y")

#GET ACCESS TOKEN
def get_access_token():
    data = {}
    response = requests.post('https://api.crowdstrike.com/oauth2/token', data=data)
    response_result = response.json()
    access_token = response_result["access_token"]
    return access_token

#GET LIST OF DETECTIONS
def get_detections_list(token):
    headers = {'Content-Type': 'application/json', 'Authorization': 'bearer ' + token}
    response = requests.get(f"https://api.crowdstrike.com/alerts/queries/alerts/v2?filter=created_timestamp:>'{new_york_year}-03-01T04:00:00.0Z'&limit=1000", headers=headers)
    response_result = response.json()
    detection_id_list = response_result["resources"]
    return detection_id_list

#GET DATA ON EACH DETECTION IN DETECTION LIST
def get_detection_data(id_list, token):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json','Authorization': 'bearer ' + token}
    data = {'composite_ids': id_list}
    response = requests.post('https://api.crowdstrike.com/alerts/entities/alerts/v2', headers=headers, json=data)
    response_result = response.json()
    detection_data = response_result["resources"]
    return detection_data

if __name__ == '__main__':
    None
