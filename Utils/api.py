# from config import *
# from Utils.utils import *
import re
import json
import logging
from urllib.parse import urlparse
import datetime
import requests
from config import API_PATH
import Utils

def _fetch_data(url, endpoint, max_retries=3):
    logging.debug(f'fetch url arg: {url}')
    panel_url = re.sub(r'/api/v2$', '', url)
    logging.debug(f'panel_url: {panel_url}')
    api_url = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', url)
    logging.debug(f'api_url: {api_url}')
    url_api = f"{api_url}/{endpoint}"
    logging.debug(f'url_api: {url_api}')
    retries = 0
    while retries < max_retries:
        try:
            logging.debug(f'Trying to fetch panel response from {panel_url}')
            panel_response = requests.get(panel_url)
            panel_response.raise_for_status()
            cookies = panel_response.cookies
            logging.debug(f'Cookies extracted for {endpoint}: {cookies}')
            
            logging.debug(f'Trying to fetch API response from {url_api}')
            response = requests.get(url_api, cookies=cookies)
            response.raise_for_status()
            logging.debug(f'Response received: {response.json()}')
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from {endpoint}. Error: {e}")
            retries += 1
    logging.error(f"Maximum retries exceeded for {endpoint}. Returning None.")
    return None

def select(url, endpoint="admin/user/"):
    logging.debug(f'select: {url}')
    try:
        response = _fetch_data(url, endpoint)
        if response is None:
            logging.error(f'No response received from the API.')
            return None
        logging.debug(f'Response received from API: {response}')
        
        users_dict = Utils.utils.users_to_dict(response)
        if not users_dict:
            logging.error(f'No users found in response.')
            return None
        
        res = Utils.utils.dict_process(users_dict)
        logging.debug(f'Processed result: {res}')
        return res
    except Exception as e:
        logging.error(f'API error: {e}')
        return None

def find(url, uuid, endpoint="/user/"):
    logging.debug(f'find: url={url}, uuid={uuid}, endpoint={endpoint}')
    try:
        response = requests.get(url + endpoint, data={"uuid": uuid})
        jr = response.json()
        logging.debug(f'Response received: {jr}')
        if len(jr) != 1:
            for user in jr:
                if user['uuid'] == uuid:
                    logging.debug(f'User found: {user}')
                    return user
            logging.debug('No user found with the given UUID.')
            return None
        return jr[0]
    except Exception as e:
        logging.error(f'API error: {e}')
        return None

def insert(url, name, usage_limit_GB, package_days, last_reset_time=None, added_by_uuid=None, mode="no_reset",
            last_online="1-01-01 00:00:00", telegram_id=None,
            comment=None, current_usage_GB=0, start_date=None, endpoint="/user/"):
    logging.debug(f'insert: url={url}, name={name}, usage_limit_GB={usage_limit_GB}, package_days={package_days}')
    import uuid
    uuid = str(uuid.uuid4())
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
    jdata = json.dumps(data)
    logging.debug(f'Data to be inserted: {jdata}')
    try:
        response = requests.post(url + endpoint, data=jdata, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        logging.debug(f'Insert response: {response.json()}')
        return uuid
    except Exception as e:
        logging.error(f'API error: {e}')
        return None

def update(url, uuid, endpoint="/user/", **kwargs):
    logging.debug(f'update: url={url}, uuid={uuid}, endpoint={endpoint}, kwargs={kwargs}')
    try:
        user = find(url, uuid)
        if not user:
            logging.error('User not found for update.')
            return None
        for key in kwargs:
            user[key] = kwargs[key]
        logging.debug(f'Updated user data: {user}')
        response = requests.post(url + endpoint, data=json.dumps(user),
                                    headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        logging.debug(f'Update response: {response.json()}')
        return uuid
    except Exception as e:
        logging.error(f'API error: {e}')
        return None
