# -*- coding: utf-8 -*-
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

import time
import base64
from tmsg import TelegramMessage
import telegram
from errors import ValidationError
import dynamodb
from captcha import get_choice, check_captcha
import api
from admin import admin_menu
from helpers import (
    save_chat_status,
    make_language_keyboard,
    represents_int,
    change_lang,
    get_pp_link,
    get_tos_link,
    hash_str)
import globalvars

from settings import CONFIG, STATUSES
import urllib.parse
from log import Log


logger = Log("BeePassBot", is_debug=CONFIG['IS_DEBUG'])


def create_new_key(tmsg, token, issue_id=None) -> bool:
    """
    Creates and sends new key for the user and

    :param tmsg: Telegram message
    :param token: Telegram bot token
    :param issue_id: User's issue connecting to server
    """
    telegram.send_message(
        token,
        tmsg.chat_id,
        globalvars.lang.text('MSG_WAIT'))

    try:
        new_keys, online_config_link = api.get_new_key(user_id=tmsg.user_uid, user_issue=issue_id)
    except Exception as exc:
        logger.error(f'Error in creating new key {exc}')
        telegram.send_message(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_ERROR'))
        return False
    if not new_keys:
        telegram.send_message(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_ERROR_NO_KEY'))
        return False
    else:
        telegram.send_message(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_OUTLINE_SSL_CONF'),
            parse='MARKDOWN')

        awsurl = (CONFIG['OUTLINE_AWS_URL'].format(
            tmsg.lang,
            online_config_link))

        telegram.send_message(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_NEW_KEY_A').format(f"{awsurl}#BeePass"),
            parse='MARKDOWN')
        telegram.send_message(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_NEW_KEY_B'),
            parse='MARKDOWN')
        telegram.send_message(
            token,
            tmsg.chat_id,
            f"{online_config_link}#BeePass")

        return True


def unsupported_message(tmsg, token) -> bool:
    logger.error('Not supported message: {}'.format(tmsg.body))
    telegram.send_message(
        token,
        tmsg.chat_id,
        globalvars.lang.text("MSG_UNSUPPORTED_COMMAND"))

    try:
        vpnuser = api.get_user(tmsg.user_uid)
    except Exception as exc:
        logger.error('Could not get user profile: {}'.format(exc))
        return False

    if not vpnuser or not vpnuser['username']:  # start from First step
        keyboard = make_language_keyboard()
        telegram.send_keyboard(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_SELECT_LANGUAGE'),
            keyboard)
        save_chat_status(tmsg.chat_id, STATUSES['SET_LANGUAGE'])
    else:
        telegram.send_keyboard(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_HOME_ELSE'),
            globalvars.HOME_KEYBOARD)
        save_chat_status(tmsg.chat_id, STATUSES['HOME'])
    return True


def bot_handler(event, _):
    """
    Main entry point to handle the bot

    param event: information about the chat
    :param _: information about the telegram message (unused)
    """
    logger.debug(
        "%s:%s Request received:%s",
        __name__,
        str(time.time()),
        str(event))

    try:
        default_language = event["lang"]
        logger.debug("Language is %s", event["lang"])
    except KeyError:
        default_language = "fa"
        logger.debug("Language is not defined!")

    try:
        token = event['token']
    except KeyError:
        logger.error("Token is not defined!")
        return None

    try:
        tmsg = TelegramMessage(event, default_language)
        tmsg.user_uid = hash_str(tmsg.user_uid)
        logger.debug("TMSG object: {}".format(tmsg))
    except Exception as exc:
        logger.error(
            'Error in Telegram Message parsing {} {}'.format(event, str(exc)))
        return None

    if tmsg.type not in CONFIG['SUPPORTED_MESSAGE_TYPES']:
        logger.info('Not supported message type: {}'.format(tmsg.type))
        return None

    if tmsg.chat_id == 0:
        logger.error(
            'This message type has no chat_id: {}'.format(tmsg.type))
        return True

    preferred_lang = None
    try:
        preferred_lang = dynamodb.get_user_lang(
            table=CONFIG["DYNAMO_TABLE"],
            chat_id=tmsg.chat_id)
    except Exception as exc:
        logger.error(
            'Can not find preferred_lang for {}: {}'.format(tmsg, str(exc)))

    if (preferred_lang is None or
            preferred_lang not in CONFIG['SUPPORTED_LANGUAGES']):
        preferred_lang = default_language
    # current_language = CONFIG['SUPPORTED_LANGUAGES'].index(preferred_lang)
    logger.debug('User language is {}'.format(preferred_lang))

    change_lang(preferred_lang)
    tmsg.lang = preferred_lang

    if tmsg.body == globalvars.lang.text('MENU_BACK_HOME'):
        telegram.send_keyboard(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_HOME_ELSE'),
            globalvars.HOME_KEYBOARD)
        save_chat_status(tmsg.chat_id, STATUSES['HOME'])
        return

    if tmsg.command == CONFIG['TELEGRAM_START_COMMAND'] and len(tmsg.command_arg) > 0:
        tmsg.command = ""
        tmsg.body = base64.urlsafe_b64decode(tmsg.command_arg)

    # Check for commands (starts with /)
    if tmsg.command == CONFIG["TELEGRAM_START_COMMAND"]:
        dynamodb.create_chat_status(
            CONFIG['DYNAMO_TABLE'], tmsg.chat_id, STATUSES['START'])
        telegram.send_message(
            token,
            tmsg.chat_id,
            globalvars.lang.text("MSG_INITIAL_SCREEN").format(CONFIG['VERSION']))
        keyboard = make_language_keyboard()
        telegram.send_keyboard(
            token,
            tmsg.chat_id,
            globalvars.lang.text('MSG_SELECT_LANGUAGE'),
            keyboard)
        save_chat_status(tmsg.chat_id, STATUSES['SET_LANGUAGE'])
        return None
    elif tmsg.command == CONFIG['TELEGRAM_ADMIN_COMMAND']:
        chat_status = int(dynamodb.get_chat_status(
            table=CONFIG["DYNAMO_TABLE"],
            chat_id=tmsg.chat_id))
        if not admin_menu(token, tmsg, chat_status):
            telegram.send_keyboard(
                token,
                tmsg.chat_id,
                globalvars.lang.text('MSG_HOME'),
                globalvars.HOME_KEYBOARD
            )
        return None

    # non-command texts, a message not started with /
    elif tmsg.type == 'MESSAGE':
        chat_status = int(dynamodb.get_chat_status(
            table=CONFIG["DYNAMO_TABLE"],
            chat_id=tmsg.chat_id))

        if chat_status >= STATUSES['ADMIN_SECTION_HOME']:
            if not admin_menu(token, tmsg, chat_status):
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME'),
                    globalvars.HOME_KEYBOARD
                )
            return None

        elif chat_status == STATUSES['SET_LANGUAGE']:
            if (tmsg.body is None or
                    tmsg.body not in globalvars.lang.text('SUPPORTED_LANGUAGES')):
                message = globalvars.lang.text('MSG_LANGUAGE_CHANGE_ERROR')
            else:
                new_lang = CONFIG['SUPPORTED_LANGUAGES'][globalvars.lang.text(
                    'SUPPORTED_LANGUAGES').index(tmsg.body)]
                dynamodb.save_user_lang(
                    table=CONFIG["DYNAMO_TABLE"],
                    chat_id=tmsg.chat_id,
                    language=new_lang)
                change_lang(new_lang)
                message = globalvars.lang.text(
                    'MSG_LANGUAGE_CHANGED').format(tmsg.body)
            telegram.send_message(
                token,
                tmsg.chat_id,
                message)

            try:
                vpnuser = api.get_user(tmsg.user_uid)
            except Exception as exc:
                logger.error(f'Error in getting user info: {exc}')
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_ERROR'))
                return None

            if not vpnuser or not vpnuser['username']:
                choices, a, b = get_choice(
                    table=CONFIG["DYNAMO_TABLE"],
                    chat_id=tmsg.chat_id)
                if choices:
                    keyboard = telegram.make_keyboard(choices, 2, '')
                    telegram.send_keyboard(
                        token,
                        tmsg.chat_id,
                        "{}\n{} + {}:".format(
                            globalvars.lang.text("MSG_ASK_CAPTCHA"), a, b),
                        keyboard)
                save_chat_status(tmsg.chat_id, STATUSES['FIRST_CAPTCHA'])
            else:
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME_ELSE'),
                    globalvars.HOME_KEYBOARD)
                save_chat_status(tmsg.chat_id, STATUSES['HOME'])
            return None

        elif chat_status == STATUSES['FIRST_CAPTCHA']:
            try:
                check = check_captcha(
                    table=CONFIG["DYNAMO_TABLE"],
                    chat_id=tmsg.chat_id,
                    sum=int(tmsg.body))
            except Exception as exc:
                check = False
                logger.error(
                    "Wrong First captcha from {} - error: {}".format(
                        hash_str(tmsg.user_uid), str(exc)))

            if check:
                tos = get_tos_link()
                pp = get_pp_link()
                if tos is not None:
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        tos
                    )
                if pp is not None:
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        pp
                    )
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text("MSG_OPT_IN"),
                    globalvars.OPT_IN_KEYBOARD)
                save_chat_status(tmsg.chat_id, STATUSES['OPT_IN'])
            else:
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_WRONG_CAPTCHA'))
                choices, a, b = get_choice(
                    table=CONFIG["DYNAMO_TABLE"],
                    chat_id=tmsg.chat_id)
                if choices:
                    keyboard = telegram.make_keyboard(choices, 2, '')
                    telegram.send_keyboard(
                        token,
                        tmsg.chat_id,
                        "{}\n{} + {}:".format(
                            globalvars.lang.text("MSG_ASK_CAPTCHA"), a, b),
                        keyboard)
                save_chat_status(tmsg.chat_id, STATUSES['FIRST_CAPTCHA'])
            return None

        elif chat_status == STATUSES['OPT_IN']:
            if tmsg.body == globalvars.lang.text('MENU_PRIVACY_POLICY_CONFIRM'):
                try:
                    api.create_user(user_id=tmsg.user_uid, chatid=tmsg.chat_id)
                except Exception as exc:
                    logger.error(f'Error in creating new user: {exc}')
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_ERROR'))
                    return None
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME'),
                    globalvars.HOME_KEYBOARD)
                save_chat_status(tmsg.chat_id, STATUSES['HOME'])
            else:
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_PRIVACY_POLICY_DECLINE'),
                    globalvars.OPT_IN_DECLINED_KEYBOARD)
                save_chat_status(tmsg.chat_id, STATUSES['OPT_IN_DECLINED'])
            return None

        elif chat_status == STATUSES['OPT_IN_DECLINED']:
            if tmsg.body == globalvars.lang.text('MENU_BACK_PRIVACY_POLICY'):
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text("MSG_OPT_IN"),
                    globalvars.OPT_IN_KEYBOARD)
                save_chat_status(tmsg.chat_id, STATUSES['OPT_IN'])
            elif tmsg.body == globalvars.lang.text('MENU_HOME_CHANGE_LANGUAGE'):
                keyboard = make_language_keyboard()
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_SELECT_LANGUAGE'),
                    keyboard)
                save_chat_status(tmsg.chat_id, STATUSES['SET_LANGUAGE'])
            return None

        elif chat_status == STATUSES['HOME']:
            if tmsg.body == globalvars.lang.text('MENU_CHECK_STATUS'):
                blocked = False
                banned = False
                active = True
                try:
                    # user_info = api.get_outline_user(tmsg.user_uid)
                    vpnuser = api.get_user(tmsg.user_uid)
                    if not vpnuser:
                        logger.debug("New user: {}".format(hash_str(tmsg.user_uid)))
                        telegram.send_message(
                            token,
                            tmsg.chat_id,
                            globalvars.lang.text('MSG_NO_ACCOUNT'),
                            parse='MARKDOWN')
                        telegram.send_message(
                            token,
                            tmsg.chat_id,
                            '/start')
                        return None
                except Exception as exc:
                    logger.error(f'Error in getting user info: {exc}')
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_ERROR'))
                    return None
                if 'banned' in vpnuser:
                    banned = vpnuser['banned']
                else:
                    logger.error(
                        "This vpnuser does not have banned value: {}".format(
                            vpnuser))
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_ACCOUNT_INFO_BANNED')
                    if banned else globalvars.lang.text('MSG_ACCOUNT_INFO_OK')
                )
                if not banned:
                    if 'outline_key' in vpnuser and len(vpnuser['outline_key'])>0:
                        for outline_key in vpnuser['outline_key']:
                            try:
                                serverinfo = api.get_outline_server_info(
                                    outline_key['server'])

                            except Exception as exc:
                                logger.error(f'Error in getting server info: {exc}')
                                telegram.send_message(
                                    token,
                                    tmsg.chat_id,
                                    globalvars.lang.text('MSG_ERROR'))
                                return None

                            if serverinfo is not None:
                                blocked = serverinfo['is_blocked']
                                active = serverinfo['active']
                            telegram.send_message(
                                token,
                                tmsg.chat_id,
                                globalvars.lang.text('MSG_SERVER_INFO_BLOCKED')
                                if blocked else globalvars.lang.text('MSG_SERVER_INFO_OK')
                            )
                            telegram.send_message(
                                token,
                                tmsg.chat_id,
                                globalvars.lang.text('MSG_SERVER_INFO_ACTIVE')
                                if active else globalvars.lang.text('MSG_SERVER_INFO_INACTIVE')
                            )
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME_ELSE'),
                    globalvars.HOME_KEYBOARD)
                return None
            elif tmsg.body == globalvars.lang.text('MENU_HOME_NEW_KEY'):
                try:
                    vpnuser = api.get_user(tmsg.user_uid)
                except Exception as exc:
                    logger.error(f'Error in getting user info: {exc}')
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_ERROR'))
                    return None

                if not vpnuser or not vpnuser['username']:
                    logger.debug("New user: {}".format(hash_str(tmsg.user_uid)))
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_NO_ACCOUNT'),
                        parse='MARKDOWN')
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        '/start')
                    return None
                elif 'banned' in vpnuser and vpnuser['banned']:
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_ACCOUNT_INFO_BANNED'))
                    telegram.send_keyboard(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_HOME_ELSE'),
                        globalvars.HOME_KEYBOARD)
                    save_chat_status(tmsg.chat_id, STATUSES['HOME'])
                    return None
                elif not vpnuser['outline_key'] or len(vpnuser['outline_key'])==0:
                    new_key_created = create_new_key(tmsg, token)
                    if not new_key_created:
                        telegram.send_message(
                            token,
                            tmsg.chat_id,
                            globalvars.lang.text('MSG_ERROR_NO_KEY'))
                        return False
                    telegram.send_keyboard(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_HOME_ELSE'),
                        globalvars.HOME_KEYBOARD)
                    save_chat_status(tmsg.chat_id, STATUSES['HOME'])
                    return None
                else:
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_OUTLINE_RETURNING_USER'))

                    online_config_object = api.get_online_config(user_id=tmsg.user_uid)
                    online_config_link = online_config_object['ss_link']

                    awsurl = (CONFIG['OUTLINE_AWS_URL'].format(
                        tmsg.lang,
                        online_config_link))
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text(
                            'MSG_EXISTING_KEY_A').format(f"{awsurl}#BeePass"),
                        parse='MARKDOWN')
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_EXISTING_KEY_B'),
                        parse='MARKDOWN')
                    telegram.send_message(
                        token,
                        tmsg.chat_id,
                        f"{online_config_link}#BeePass")

                    telegram.send_keyboard(
                        token,
                        tmsg.chat_id,
                        globalvars.lang.text('MSG_HOME_ELSE'),
                        globalvars.HOME_KEYBOARD)
                    save_chat_status(tmsg.chat_id, STATUSES['HOME'])
                    return None

            elif tmsg.body == globalvars.lang.text('MENU_HOME_FAQ'):
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_FAQ_URL'))
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME_ELSE'),
                    globalvars.HOME_KEYBOARD)
                return None

            elif tmsg.body == globalvars.lang.text('MENU_HOME_INSTRUCTION'):
                photo_name = "BeepassVPN-guideline-{}.png".format(
                    preferred_lang)
                with open(photo_name, 'rb') as photofile:
                    telegram.send_photo(
                        token,
                        tmsg.chat_id,
                        photofile.read(),
                        "BeePass instructions")
                video_name = f"BePassVPN-How-to-Use-{preferred_lang}.mp4"
                with open(video_name, 'rb') as video_file:
                    telegram.send_video(
                        token,
                        tmsg.chat_id,
                        video_file.read())
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME_ELSE'),
                    globalvars.HOME_KEYBOARD)
                return None

            elif tmsg.body == globalvars.lang.text('MENU_HOME_CHANGE_LANGUAGE'):
                keyboard = make_language_keyboard()
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_SELECT_LANGUAGE'),
                    keyboard)
                save_chat_status(tmsg.chat_id, STATUSES['SET_LANGUAGE'])
                return None

            elif tmsg.body == globalvars.lang.text('MENU_HOME_PRIVACY_POLICY'):
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    get_pp_link())
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME_ELSE'),
                    globalvars.HOME_KEYBOARD)
                return None

            elif tmsg.body == globalvars.lang.text('MENU_HOME_SUPPORT'):
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text("MSG_SUPPORT_BOT"))
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    CONFIG["SUPPORT_BOT"])
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_HOME_ELSE'),
                    globalvars.HOME_KEYBOARD)
                return None

            elif tmsg.body == globalvars.lang.text('MENU_HOME_DELETE_ACCOUNT'):
                reasons_dict = api.get_delete_reasons(tmsg.lang)
                reasons = list(reasons_dict.values())
                keyboard = telegram.make_keyboard(reasons, 2, globalvars.lang.text('MENU_BACK_HOME'))
                telegram.send_keyboard(
                    token, tmsg.chat_id,
                    globalvars.lang.text("MSG_ASK_DELETE_REASONS"),
                    keyboard)
                save_chat_status(
                    tmsg.chat_id, STATUSES['DELETE_ACCOUNT_REASON'])
                return None

            # unsupported message from user
            unsupported_message(tmsg, token)

        elif chat_status == STATUSES['DELETE_ACCOUNT_REASON']:
            reasons_dict = api.get_delete_reasons(tmsg.lang)
            reason_id = [key for (key, value)
                         in reasons_dict.items() if value == tmsg.body]
            if not reason_id:
                telegram.send_message(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text("MSG_UNSUPPORTED_COMMAND"))
                return None

            logger.debug('user {} wants to delete her account because {}'.format(
                hash_str(tmsg.user_uid),
                tmsg.body
            ))
            try:
                deleted = api.delete_user(user_id=tmsg.user_uid, reason_id=reason_id[0])
            except Exception as exc:
                logger.error('Could not delete the profile: {}'.format(exc))
                telegram.send_keyboard(
                    token,
                    tmsg.chat_id,
                    globalvars.lang.text('MSG_ERROR'),
                    globalvars.HOME_KEYBOARD)
                return None
            if deleted:
                telegram.send_keyboard(
                    token, tmsg.chat_id,
                    globalvars.lang.text("MSG_DELETED_ACCOUNT"),
                    globalvars.BACK_TO_HOME_KEYBOARD)
                save_chat_status(
                    tmsg.chat_id, STATUSES['DELETE_ACCOUNT_CONFIRM'])
            return None

        else:  # unsupported message from user
            unsupported_message(tmsg, token)
