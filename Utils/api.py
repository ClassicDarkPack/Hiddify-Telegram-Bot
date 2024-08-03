import json
import logging
import datetime
import requests
from urllib.parse import urlparse
from Utils import utils
from config import API_PATH

def interaction(url, endpoint, method='GET', data=None, max_retries=3, timeout=10):
    logging.debug(f'base_url: {url}')
    api_url, api_key = utils.extract_key_from_url(url)
    api_url = api_url + endpoint
    logging.debug(f'api_key: {api_key}')
    logging.debug(f'api_url: {api_url}')
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Hiddify-API-Key': api_key
    }
    
    retries = 0
    while retries < max_retries:
        try:
            logging.debug(f'Trying to fetch API response from {api_url}')
            if method == 'GET':
                response = requests.get(api_url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=timeout)
            
            response.raise_for_status()
            logging.debug(f'Response received: {response.json()}')
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from {endpoint}. Error: {e}")
            retries += 1
    logging.error(f"Maximum retries exceeded for {endpoint}. Returning None.")
    return None

def select(url, endpoint="/admin/user"):
    try:
        response = interaction(url, endpoint)
        if response is None:
            logging.error("No response received from the API.")
            return None
        
        logging.info("Response received from API:", response)
        
        users_dict = utils.users_to_dict(response)
        if not users_dict:
            logging.error("No users found in response.")
            return None
        
        res = utils.dict_process(url, users_dict, server_id=None)  # ارسال url و users_dict و server_id
        return res
    except Exception as e:
        logging.error(f"API error: {e}")
        return None

def find(url, uuid, endpoint="/admin/user"):
    logging.debug(f'find: url={url}, uuid={uuid}, endpoint={endpoint}')
    try:
        response = interaction(url, f"{endpoint}/{uuid}", method='GET')
        if response is None or ('msg' in response and response.get('msg') == 'invalid request'):
            logging.error('No user found with the given UUID.')
            return None
        logging.debug(f'User found: {response}')
        return response
    except Exception as e:
        logging.error(f'API error: {e}')
        return None

def insert(url, name, usage_limit_GB, package_days, last_reset_time=None, added_by_uuid=None, mode="no_reset",
           last_online="1-01-01 00:00:00", telegram_id=None, comment=None, current_usage_GB=0, start_date=None, endpoint="/admin/user"):
    logging.debug(f'insert: url={url}, name={name}, usage_limit_GB={usage_limit_GB}, package_days={package_days}')
    import uuid as uuid_lib
    uuid = str(uuid_lib.uuid4())
    added_by_uuid = urlparse(url).path.split('/')[2]
    last_reset_time = datetime.datetime.now().strftime("%Y-%m-%d")

    data = {
        "uuid": uuid,
        "name": name,
        "usage_limit_GB": usage_limit_GB,
        "package_days": package_days,
        "added_by_uuid": added_by_uuid,
        "last_reset_time": last_reset_time,
        "mode": mode,
        "last_online": last_online,
        "telegram_id": telegram_id,
        "comment": comment,
        "current_usage_GB": current_usage_GB,
        "start_date": start_date
    }
    logging.debug(f'Data to be inserted: {json.dumps(data)}')
    try:
        response = interaction(url, endpoint, method='POST', data=data)
        if response is None:
            logging.error("Failed to insert data.")
            return None
        logging.debug(f'Insert response: {response}')
        return uuid
    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err.response.text}')
    except Exception as e:
        logging.error(f'API error: {e}')
    return None

def update(url, uuid, endpoint="/admin/user", **kwargs):
    logging.debug(f'update: url={url}, uuid={uuid}, endpoint={endpoint}, kwargs={kwargs}')
    try:
        user = find(url, uuid, endpoint)
        if not user:
            logging.error('User not found for update.')
            return None
        for key in kwargs:
            if key in user:
                user[key] = kwargs[key]
        logging.debug(f'Updated user data: {user}')
        response = interaction(url, f"{endpoint}/{uuid}", method='POST', data=user)
        if response is None:
            logging.error("Failed to update data.")
            return None
        logging.debug(f'Update response: {response}')
        return uuid
    except Exception as e:
        logging.error(f'API error: {e}')
        return None
