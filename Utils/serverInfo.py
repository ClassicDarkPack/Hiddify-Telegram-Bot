import requests
from urllib.parse import urlparse
from Database.dbManager import USERS_DB

def scrape_data_from_json_url(url, api_key):
    try:
        headers = {
            'Hiddify-API-Key': api_key,
            'Accept': 'application/json'
        }
        response = requests.get(f"{url}/admin/get_data", headers=headers)
        response.raise_for_status()
        
        # Parse JSON data
        json_data = response.json()

        # Extract relevant information using the shared function
        extracted_data = json_template(json_data)

        return extracted_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def json_template(data):
    system_stats = data.get('stats', {}).get('system', {})
    usage_history = data.get('usage_history', {})
    
    # Example of extracting relevant fields for system and usage statistics
    return {
        'cpu_percent': system_stats.get('cpu_percent'),
        'disk_total': system_stats.get('disk_total'),
        'ram_used': system_stats.get('ram_used'),
        'total_connections': system_stats.get('total_connections'),
        'online_last_5min': usage_history.get('m5', {}).get('online'),
        'usage_today': usage_history.get('today', {}).get('usage'),
    }


def server_status_template(result, server_name):
    lline = (32 * "-")
    
    cpu_percent = result.get('cpu_percent', 'N/A')
    disk_total = result.get('disk_total', 'N/A')
    ram_used = result.get('ram_used', 'N/A')
    online_last_5min = result.get('online_last_5min', 'N/A')
    usage_today = result.get('usage_today', 'N/A')
    usage_today = f"{usage_today / (1024 ** 3):.2f} GB" if usage_today != 'N/A' else 'N/A'

    return f"<b>Server: {server_name}</b>\n{lline}\n" \
           f"CPU: {cpu_percent}%\n" \
           f"RAM Used: {ram_used:.2f} GB\n" \
           f"Disk Total: {disk_total:.2f} GB\n" \
           f"Online (Now): {online_last_5min} Users\n" \
           f"Usage (Today): {usage_today}\n"


def get_server_status(server_row, api_key):
    server_name = server_row['title']
    server_url = server_row['url']
    
    # Fetch data from the server
    data = scrape_data_from_json_url(server_url, api_key)
    
    if not data:
        return False
    
    # Generate and return server status text
    txt = server_status_template(data, server_name)
    return txt
