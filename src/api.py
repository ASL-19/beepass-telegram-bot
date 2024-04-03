# Copyright 2024 ASL19 Organization
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from helpers import hash_str
import requests
from settings import CONFIG, API_ENDPOINTS
from log import get_logger


logger = get_logger('BeePassBot', __name__)
USER_AGENT = 'BeePass Telegram Bot'
AUTHORIZATION_HEADER = 'Token {}'


def get_enrolled_users(blocked=False):
    """
    Get a list of enrolled users from server

    :param blocked: boolean to indicate list of blocked users or all users
    :return: List of enrolled users as CSV
    """
    logger.debug("getting enrolled users list from api server")
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['LIST_USERS']}?format=csv"
    if blocked:
        url += '&blocked=True'

    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}

    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_enrolled_users error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        return req.text
    else:
        logger.error(
            'API call error during get_enrolled_users. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_banned_users():
    """
    Get a list of enrolled users from server

    :return: List of enrolled users as CSV
    """
    logger.debug("getting enrolled users list from api server")
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USERS']}?format=csv"
    url += '&banned=True'

    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}

    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_enrolled_users error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        return req.text
    else:
        logger.error(
            'API call error during get_enrolled_users. status: %s',
            str(req.status_code))
        req.raise_for_status()


def store_chatid(username, chatid):
    """
    Store the chat id on the server so we can send messages to the user
    or just clear it if user doesn't like to be notified.

    :param username: Telegram username
    :param chatid: Telegram chat id with user
    :return: User's json object or None in case of success and raise error otherwise
    """
    logger.info("storing chatid for the user on api server: {}".format(username))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USER']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    data = {
        'username': str(username),
        'userchat': str(chatid)
    }
    try:
        req = requests.patch(url, json=data, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('store_chatid error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['not_found']:
        logger.error('Store chat id - User not found')
        return {}
    else:
        logger.error(
            'API call error during store_chatid. status: %s',
            str(req.status_code))
        req.raise_for_status()


def ban_user(username, ban=True):
    """
    Ban user on the server

    :param username: Telegram username
    :return: User's json object or None in case of success and raise error otherwise
    """
    logger.debug("{}banning user from api server: {}".format(
        'un' if ban==True else '', hash_str(username)))

    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USER']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    data = {
        'username': str(username),
        'banned': (ban==True)
    }
    try:
        req = requests.patch(url, json=data, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('ban_user error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['not_found']:
        logger.error('ban_user - User not found')
        return {}
    else:
        logger.error(
            'API call error during ban_user. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_user(user_id):
    """
    Getting user information from server

    :param user_id: Telegram User ID
    :return: User's json object or None in case of success and raise error otherwise
    """
    logger.debug("getting user info from api server: {}".format(
        hash_str(user_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USER']}/{str(user_id)}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}

    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_user error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['not_found']:
        logger.error('Get user - User not found')
        return {}
    else:
        logger.error(
            'API call error during get_user. status: %s',
            str(req.status_code))
        req.raise_for_status()


def create_user(user_id, chatid, channel='TG'):
    """
    Check whether the telegram user has a beepass account

    :param user_id: Telegram User ID
    :param chatid: Telegram chat id with user
    :param channel: What platform user is using to get a key, default Telegram
    :return: User's json object in case of success and None otherwise
    """
    logger.debug("Creating new user: {}".format(hash_str(user_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USER']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    data = {
        'username': str(user_id),
        'channel': channel,
        'region': CONFIG['REGION']
    }

    try:
        req = requests.put(url, json=data, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('create_user error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['bad_request']:
        logger.error('Bad request, check the submitted data')
        return None
    elif req.status_code == requests.codes['conflict']:
        logger.error(
            'Bad request, Username already exists: {}'.format(user_id))
        return None
    else:
        logger.error(
            'API call error during create_user. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_outline_server_info(server_id):
    """
    Retrieve outline server info from the api server

    :param user_id: VPN Server ID
    :return: User's json object in case of success and None otherwise
    """
    logger.debug("Get outline server info {}".format(str(server_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['SERVERS']}/{server_id}"
    print(url)
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_outline_server_info error: {}'.format(error))
        raise error

    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['bad_request']:
        logger.error('Bad request, check the submitted data')
        return None
    else:
        logger.error(
            'API call error during get_outline_server_info. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_outline_user(user_id):
    """
    Check whether the telegram user has a beepass account

    :param user_id: Telegram User ID
    :return: User's json object in case of success and None otherwise
    """
    logger.debug("Get/update outline user info {}".format(
        hash_str(user_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['OUTLINE_KEY']}/{user_id}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_outline_user error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['bad_request']:
        logger.error('Bad request, check the submitted data')
        return None
    else:
        logger.error(
            'API call error during get_outline_user. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_new_key(user_id, user_issue=None):
    """
    Get a new key for the user

    :param user_id: Telegram User ID
    :param user_issue: Issue ID
    :return: User's json object in case of success and None otherwise
    """
    logger.debug("Get a new key for {}".format(hash_str(user_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['OUTLINE_KEY']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    data = {
        'user': str(user_id)
    }
    if user_issue:
        data['user_issue'] = int(user_issue)

    try:
        req = requests.put(url, json=data, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_new_key error: {}'.format(error))
        raise error

    keys = []
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        for created_key in json_data['created_keys']:
            keys.append(created_key['outline_key'])
        return keys, json_data['ss_link']
    elif req.status_code == requests.codes['bad_request']:
        logger.error('Bad request, check the submitted data')
        req.raise_for_status()
    elif req.status_code == requests.codes['not_acceptable']:
        json_data = json.loads(req.text)
        logger.error(json_data.get('detail', 'Not Acceptable request (406)'))
        return None, None
    else:
        logger.error(
            'API call error during get_new_key. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_online_config(user_id):
    """
    Getting Online Config link for a user

    :param user_id: Telegram User ID
    :return: Online Config's json object or None in case of success and raise error otherwise
    """
    logger.debug("getting Online Config link from api server: {}".format(
        hash_str(user_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['OUTLINE_CONFIG']}/{user_id}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}

    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_online_config error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        return json_data
    elif req.status_code == requests.codes['not_found']:
        logger.error('Get user - User not found')
        return {}
    else:
        logger.error(
            f"API call error during get_online_config. \n status: {req.status_code}, message: {req.text}")
        req.raise_for_status()


def get_outline_sever_id(user_id):
    """
    Check whether the telegram user has a beepass account

    :param user_id: Telegram User ID
    :return: User's json object in case of success and None otherwise
    """
    logger.debug("Get outline server id for user: {}".format(
        hash_str(user_id)))
    user = get_outline_user(user_id)
    if user is not None:
        return user['server']


def get_key(user_id, user_issue=None):
    """
    Check whether the telegram user has a beepass account

    :param user_id: Telegram User ID
    :param user_issue: Issue ID
    :return: User's json object in case of success and None otherwise
    """
    logger.debug("Get new Outline key for user: {}".format(
        hash_str(user_id)))
    user = get_outline_user(user_id)
    if user is not None:
        return user['outline_key']


def delete_user(user_id, reason_id):
    """
    Delete the user's beepass account

    :param user_id: Telegram User ID
    :param reason_id: Delete Reason ID
    :return: True if successful and False in case of any error
    """
    logger.debug("Deleting user's profile: {}".format(
        hash_str(user_id)))
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USER']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])
    }
    data = {
        'username': str(user_id),
        'reason_id': str(reason_id)
    }

    try:
        req = requests.delete(url, json=data, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('delete_user error: {}'.format(error))
        raise error
    if req.status_code == requests.codes['no_content']:
        return True
    elif req.status_code == requests.codes['not_found']:
        logger.error('Delete user - User not found')
        return False
    else:
        logger.error(
            'API call error during delete_user. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_issues(lang):
    """
    Get the list of issues from landing page server

    :param lang: user's current language to filter the issues
    :return: Dictionary of issues' id and description
    """
    logger.debug("getting the list of issues from the api server.")
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['ISSUES']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_issues error: {}'.format(error))
        raise error

    lang_pattern = '_{}'.format(lang)
    issues = {}
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        if 'results' in json_data:
            for result in json_data['results']:
                for key, value in result.items():
                    if str(key).endswith(lang_pattern):
                        issues[result['id']] = str(value)
                if result['id'] not in issues:
                    issues[result['id']] = result['description_en']
        return issues
    elif req.status_code == requests.codes['not_found']:
        logger.error('List of Issues not found')
        return {}
    else:
        logger.error(
            'API call error during get_issues. status: %s',
            str(req.status_code))
        req.raise_for_status()


def get_delete_reasons(lang):
    """
    Get the list of delete reasons from landing page server

    :param lang: user's current language to filter the reasons
    :return: Dictionary of reasons' id and description
    """
    logger.debug("getting the list of reasons from the api server.")
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['REASONS']}"
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('get_delete_reasons error: {}'.format(error))
        raise error

    lang_pattern = '_{}'.format(lang)
    reasons = {}
    if req.status_code == requests.codes['ok']:
        json_data = json.loads(req.text)
        if 'results' in json_data:
            for result in json_data['results']:
                for key, value in result.items():
                    if str(key).endswith(lang_pattern):
                        reasons[result['id']] = str(value)
                if result['id'] not in reasons:
                    reasons[result['id']] = result['description_en']
        return reasons
    elif req.status_code == requests.codes['not_found']:
        logger.error('List of reasons not found')
        return {}
    else:
        logger.error(
            'API call error during get_delete_reasons. status: %s',
            str(req.status_code))
        req.raise_for_status()


def users(banned=False):
    """
    Return the list of all users or banned users

    :param banned: True to get banned users, False for all users=
    :retrun: A csv file including users' data
    """
    logger.debug("getting all users from api server")
    url = f"{CONFIG['API_URL']}{API_ENDPOINTS['USERS']}?format=csv"
    if banned:
        url += '&banned=True'

    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': AUTHORIZATION_HEADER.format(CONFIG['API_KEY'])}
    try:
        req = requests.get(url, headers=headers, timeout=CONFIG['API_TIMEOUT'])
    except Exception as error:
        logger.error('all_users error: {}'.format(error))
        raise

    if req.status_code == requests.codes['ok']:
        return req.text
    elif req.status_code == requests.codes['not_found']:
        logger.error('Users not found')
        return {}
    else:
        logger.error(
            'API call error during all_users. status: %s',
            str(req.status_code))
        req.raise_for_status()
