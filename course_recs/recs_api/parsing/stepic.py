import json
import time
import requests
from decouple import config


def api_call(url: str):
    """Make an API call with exponential backoff in case of failure."""
    #global TOKEN
    CLIENT_ID = config('CLIENT_ID')
    CLIENT_SECRET = config('CLIENT_SECRET')

    resp = requests.post('https://stepik.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))
    TOKEN = json.loads(resp.text)['access_token']

    retries = 0
    while retries < 3:
        try:
            response = requests.get(url, headers={'Authorization': f'Bearer {TOKEN}'})
            response.raise_for_status()
            return json.loads(response.text)
        except requests.RequestException as e:
            retries += 1
            wait_time = 2 ** retries
            print(f"Error: {e}, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    return {}


def fetch_reviewed_courses(stepik_user_id: int, max_pages: int = None, max_records: int = 10):
    """Fetch user course reviews from Stepik."""
    base_url = f"https://stepik.org:443/api/course-reviews?user={stepik_user_id}"
    url = base_url
    page = 1
    total_records = 0
    result = []
    while url and (max_pages is None or page <= max_pages) and (max_records is None or total_records < max_records):
        data = api_call(url)
        if 'course-reviews' in data:
            result.extend(
                [(review['course'], review['score'], review['create_date']) for review in data['course-reviews']])
            total_records = len(result)
            # Break if we've reached the max_records limit
            if max_records is not None and total_records >= max_records:
                break
        if data.get('meta', {}).get('has_next', False):
            page += 1
            url = f"{base_url}&page={page}"
        else:
            url = None
    return result

# берет айдишник степика и возвращает список теплов
# перед вызовом проверить, добавлен ли этот айдишник у пользователя
# проверить что создаются записи только для тех курсов, которые есть с базе
