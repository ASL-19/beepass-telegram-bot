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

import logging
logger = logging.getLogger("tmsg")


class ObjectCreationFailed(Exception):
    pass


class TelegramMessage(object):

    def __init__(self, event, lang):

        self.lang = lang
        self.command = ''
        self.command_arg = ''

        if 'message' in event['Input']:
            # New incoming message of any kind - text, photo, sticker, etc.
            self.type = 'MESSAGE'
            message = event['Input']['message']
            if 'title' in message['chat']:
                self.title = message['chat']['title']
            else:
                self.title = u''

            if 'from' in message:
                self.user_uid = str(message['from']['id'])
                if 'username' in message['from']:
                    self.user_id = str(message['from']['username'])
                else:
                    self.user_id = str(message['from']['id'])
                self.user_info = str(message['from'])
            else:
                self.user_id = u''
                self.user_info = u''

            # Type of chat, can be either “private”, “group”, “supergroup” or “channel”
            if message['chat']['type'] == 'supergroup':
                logger.error(f"Message from a Telegram Super Group: {self.title}")
                raise ObjectCreationFailed
            elif message['chat']['type'] == 'channel':
                logger.error(f"Message from a Telegram Channel {self.title}"
                    f"Forwarded by {self.user_uid}")
                raise ObjectCreationFailed
            elif message['chat']['type'] == 'group':
                logger.error(f"Message from a Telegram Group {self.title}"
                    f"Forwarded by {self.user_uid}")
                raise ObjectCreationFailed
            try:
                self.msg_date = message['date']
                self.id = int(message['message_id'])
                self.chat_id = int(message['chat']['id'])

                if 'text' in message:
                    self.body = message['text']
                    self.bodytype = 'TEXT'
                elif 'document' in message:
                    self.body = message['document']['file_id']
                    self.bodytype = 'DOCUMENT'
                    self.bodymime = message['document']['mime_type']
                elif 'location' in message:
                    self.body = ''
                    self.bodytype = 'LOCATION'
                    self.lat = message['location']['latitude']
                    self.lon = message['location']['longitude']
                elif 'photo' in message:
                    self.body = ''
                    self.bodytype = 'PHOTO'
                    self.photo_id = message['photo'][1]['file_id']
                elif 'voice' in message:
                    self.body = ''
                    self.bodytype = 'VOICE'
                    self.voice_id = message['voice']['file_id']
                else:
                    self.body = ''
                    self.bodytype = 'UNKNOWN'

            except Exception as exc:
                logger.error(str(exc))
                raise ObjectCreationFailed

        elif 'inline_query' in event['Input']:
            # New incoming inline query
            self.type = 'INLINE'
            inline_query = event['Input']['inline_query']
            try:
                self.id = inline_query['id']
                self.chat_id = inline_query['from']['id']
                self.user_id = inline_query['from']['username']
                self.body = inline_query['query']
                self.is_bot = inline_query['from']['is_bot']

            except Exception as exc:
                raise ObjectCreationFailed

        elif 'edited_message' in event['Input']:
            # New version of a message that is known to the bot and was edited
            self.type = 'EDITED_MESSAGE'
            message = event['Input']['edited_message']
            try:
                self.msg_date = message['edit_date']
                self.id = int(message['message_id'])
                self.chat_id = int(message['chat']['id'])
                self.user_uid = str(message['from']['id'])
                if 'from' in message:
                    if 'username' in message['from']:
                        self.user_id = str(message['from']['username'])
                    else:
                        self.user_id = str(message['from']['id'])
                    self.user_info = str(message['from'])
                else:
                    self.user_id = u''
                    self.user_info = u''

                if 'text' in message:
                    self.body = message['text']
                    self.bodytype = 'TEXT'
                elif 'document' in message:
                    self.body = message['document']['file_id']
                    self.bodytype = 'DOCUMENT'
                    self.bodymime = message['document']['mime_type']
                elif 'location' in message:
                    self.body = ''
                    self.bodytype = 'LOCATION'
                    self.lat = message['location']['latitude']
                    self.lon = message['location']['longitude']
                elif 'photo' in message:
                    self.body = ''
                    self.bodytype = 'PHOTO'
                    self.photo_id = message['photo'][1]['file_id']
                elif 'voice' in message:
                    self.body = ''
                    self.bodytype = 'VOICE'
                    self.voice_id = message['voice']['file_id']
                else:
                    self.body = ''
                    self.bodytype = 'UNKNOWN'

            except Exception as exc:
                logger.error(str(exc))
                raise ObjectCreationFailed

        elif 'callback_query' in event['Input']:
            # New incoming callback query
            self.type = 'CALLBACK'
            callback_query = event['Input']['callback_query']
            try:
                self.id = callback_query['id']
                if 'message' in callback_query and 'chat' in callback_query['message']:
                    self.chat_id = callback_query['message']['chat']['id']
                else:
                    self.chat_id = callback_query['from']['id']

                if 'message' in callback_query:
                    self.msg_id = callback_query['message']['message_id']
                    self.inline = False
                else:
                    self.msg_id = callback_query['inline_message_id']
                    self.inline = True

                self.user_uid = str(callback_query['from']['id'])
                if 'username' in callback_query['from']:
                    self.user_id = callback_query['from']['username']
                else:
                    self.user_id = callback_query['from']['id']

                self.firstname = callback_query['from']['first_name']
                self.body = callback_query['data']

            except Exception as exc:
                raise ObjectCreationFailed

        elif 'my_chat_member' in event['Input']:
            # The bot's chat member status was updated in a chat.
            # For private chats, this update is received only when the bot is blocked
            # or unblocked by the user.
            self.type = 'MEMBER_UPDATE'
            self.body = ''
            self.chat_id = 0
            my_chat_member = event['Input']['my_chat_member']
            try:
                self.status = my_chat_member['new_chat_member']['status']
                self.user_uid = str(my_chat_member['from']['id'])
                if 'username' in my_chat_member['from']:
                    self.user_id = my_chat_member['from']['username']
                else:
                    self.user_id = my_chat_member['from']['id']
                logger.info(
                    "[Member Update] chat with {} has a new status: {}".format(
                        self.user_id, self.status))

            except Exception as exc:
                raise ObjectCreationFailed

        elif 'channel_post' in event['Input']:
            # New incoming channel post of any kind - text, photo, sticker, etc.
            self.type = 'CHANNEL_POST'
            self.body = ''
            self.chat_id = 0
            channel_post = event['Input']['channel_post']
            try:
                self.user_uid = str(channel_post['sender_chat']['id'])
                if 'username' in channel_post['sender_chat']:
                    self.user_id = channel_post['sender_chat']['username']
                else:
                    self.user_id = channel_post['sender_chat']['id']
                logger.info(
                    "[Channel Post] We've got a channel post from: {}".format(
                        self.user_id))

            except Exception as exc:
                raise ObjectCreationFailed

        elif 'edited_channel_post' in event['Input']:
            # New version of a channel post that is known to the bot and was edited
            self.type = 'EDITED_CHANNEL_POST'
            self.body = ''
            self.chat_id = 0
            channel_post = event['Input']['edited_channel_post']
            try:
                self.user_uid = str(channel_post['sender_chat']['id'])
                if 'username' in channel_post['sender_chat']:
                    self.user_id = channel_post['sender_chat']['username']
                else:
                    self.user_id = channel_post['sender_chat']['id']
                logger.info(
                    f"[Edited Channel Post] We've got a channel post from: {self.user_id}")

            except Exception as exc:
                raise ObjectCreationFailed

        elif 'chosen_inline_result' in event['Input']:
            # Represents a result of an inline query that was chosen by the user and sent to their chat partner.
            self.user_uid = event['Input']['chosen_inline_result']['from']['id']
            self.query = event['Input']['chosen_inline_result']['query']
            logger.error('Not supporting chosen_inline_result yet!'
                f'from: {self.user_id}, query: {self.query}')
            raise ObjectCreationFailed
        elif 'shipping_query' in event['Input']:
            # This object contains information about an incoming shipping query.
            self.user_uid = event['Input']['shipping_query']['from']['id']
            self.invoice_payload = event['Input']['shipping_query']['invoice_payload']
            logger.error('Not supporting shipping_query yet!'
                f'from: {self.user_uid}, Invoice: {self.invoice_payload}')
            raise ObjectCreationFailed
        elif 'pre_checkout_query' in event['Input']:
            # This object contains information about an incoming pre-checkout query.
            self.user_uid = event['Input']['pre_checkout_query']['from']['id']
            self.currency = event['Input']['pre_checkout_query']['currency']
            self.total_amount = event['Input']['pre_checkout_query']['total_amount']
            self.invoice_payload = event['Input']['pre_checkout_query']['invoice_payload']
            logger.error('Not supporting pre_checkout_query yet!'
                f'from: {self.user_uid}, Invoice: {self.invoice_payload}')
            raise ObjectCreationFailed
        elif 'poll' in event['Input']:
            # This object contains information about a poll.
            self.poll_id = event['Input']['poll']['id']
            self.question = event['Input']['poll']['question']
            logger.error('Not supporting poll yet!'
                f'Poll ID: {self.poll_id}, Question: {self.question}')
            raise ObjectCreationFailed
        elif 'poll_answer' in event['Input']:
            # This object represents an answer of a user in a non-anonymous poll.
            self.user_uid = event['Input']['poll_answer']['user']['id']
            self.poll_id = event['Input']['poll_answer']['poll_id']
            logger.error('Not supporting poll_answer yet!'
                f'User: {self.user_uid}, Question: {self.question}')
            raise ObjectCreationFailed
        elif 'chat_member' in event['Input']:
            # A chat member's status was updated in a chat.
            # The bot must be an administrator in the chat
            # and must explicitly specify “chat_member” in
            # the list of allowed_updates to receive these updates.
            self.type = 'MEMBER_UPDATE'
            self.body = ''
            self.chat_id = 0
            chat_member = event['Input']['chat_member']
            try:
                self.status = chat_member['new_chat_member']['status']
                self.user_uid = str(chat_member['from']['id'])
                if 'username' in chat_member['from']:
                    self.user_id = chat_member['from']['username']
                else:
                    self.user_id = chat_member['from']['id']
            except Exception as exc:
                raise ObjectCreationFailed
            logger.error('Not supporting chat_member yet!'
                f'chat with {self.user_id} has a new status: {self.status}')
            raise ObjectCreationFailed
        elif 'chat_join_request' in event['Input']:
            # A request to join the chat has been sent.
            # The bot must have the can_invite_users administrator right in the chat to receive these updates
            self.type = 'CHAT_JOIN_UPDATE'
            self.body = ''
            chat_join_request = event['Input']['chat_join_request']
            self.chat_id = chat_join_request['chat']['id']
            self.user_uid = chat_join_request['from']['id']
            logger.error('Not supporting chat_join_request yet!'
                f'User: {self.user_id}, Chat ID: {self.chat_id}')
            raise ObjectCreationFailed
        else:
            logger.error('Undefined message type! {}'.format(event['Input']))
            raise ObjectCreationFailed

        if self.body.startswith('/'):
            self.command = self.body[1:]
            cmd = self.command.split(' ', 1)
            if len(cmd) > 1:
                self.command = str(cmd[0])
                self.command_arg = str(cmd[1])
            self.command = self.command.lower()
