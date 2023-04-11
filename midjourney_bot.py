import json
import requests


class MidjourneyBot:

    def __init__(self, config_file='config.json'):
        self._config = self._parse_json(config_file)
        self._user_token = self._config.get('user_token', None)
        self._server_id = self._config.get('server_id', None)
        self._channel_id = self._config.get('channel_id', None)
        self._proxy = self._config.get('proxy', None)
        self._proxies = None
        if self._proxy:
            self._proxies = {
                'http': self._proxy,
                'https': self._proxy,
            }

        self._header = {'authorization': self._user_token}

    def _parse_json(self, config):
        with open(config, encoding='utf-8') as fp:
            return json.load(fp)

    def content(self, message):
        return message['content']

    def message_id(self, message):
        return message['attachments'][0]['id']

    def message_hash(self, message):
        return self.get_image_url(message).split('_')[-1].split('.')[0]

    def get_image_url(self, message):
        return message['attachments'][0]['url']

    def validate_image_url(self, message):
        if message['attachments']:
            image_url = self.get_image_url(message)
            response = requests.get(
                url=image_url,
                headers=self._header,
                proxies=self._proxies,
                timeout=30,
            )
            return response.status_code == 200
        return False

    def ask(self, prompt):
        payload = {
            "type": 2,
            "application_id": "936929561302675456",
            "guild_id": self._server_id,
            "channel_id": self._channel_id,
            "session_id": "2fb980f65e5c9a77c96ca01f2c242cf6",
            "data": {
                "version": "1077969938624553050",
                "id": "938956540159881230",
                "name": "imagine",
                "type": 1,
                "options": [{
                    "type": 3,
                    "name": "prompt",
                    "value": prompt
                }],
                "application_command": {
                    "id":
                        "938956540159881230",
                    "application_id":
                        "936929561302675456",
                    "version":
                        "1077969938624553050",
                    "default_permission":
                        True,
                    "default_member_permissions":
                        None,
                    "type":
                        1,
                    "nsfw":
                        False,
                    "name":
                        "imagine",
                    "description":
                        "Create images with Midjourney",
                    "dm_permission":
                        True,
                    "options": [{
                        "type": 3,
                        "name": "prompt",
                        "description": "The prompt to imagine",
                        "required": True
                    }]
                },
                "attachments": []
            }
        }

        url = "https://discord.com/api/v9/interactions"
        response = requests.post(
            url=url,
            json=payload,
            headers=self._header,
            proxies=self._proxies,
            timeout=30,
        )
        return response.status_code

    def up_scale(self, index, message):
        payload = {
            "type": 3,
            "guild_id": self._server_id,
            "channel_id": self._channel_id,
            "message_flags": 0,
            "message_id": self.message_id(message),
            "application_id": "936929561302675456",
            "session_id": "45bc04dd4da37141a5f73dfbfaf5bdcf",
            "data": {
                "component_type": 2,
                "custom_id": "MJ::JOB::upsample::{}::{}".format(index, self.message_hash(message))
            }
        }
        url = "https://discord.com/api/v9/interactions"
        response = requests.post(
            url=url,
            json=payload,
            headers=self._header,
            proxies=self._proxies,
            timeout=30,
        )
        return response.status_code

    def max_up_scale(self, message):
        payload = {
            "type": 3,
            "guild_id": self._server_id,
            "channel_id": self._channel_id,
            "message_flags": 0,
            "message_id": self.message_id(message),
            "application_id": "936929561302675456",
            "session_id": "1f3dbdf09efdf93d81a3a6420882c92c",
            "data": {
                "component_type": 2,
                "custom_id": "MJ::JOB::upsample_max::1::{}::SOLO".format(self.message_hash(message))
            }
        }
        url = "https://discord.com/api/v9/interactions"
        response = requests.post(
            url=url,
            json=payload,
            headers=self._header,
            proxies=self._proxies,
            timeout=30,
        )
        return response.status_code

    def messages(self, limit=1):
        url = f'https://discord.com/api/v9/channels/{self._channel_id}/messages?limit={limit}'
        response = requests.get(
            url=url,
            headers=self._header,
            proxies=self._proxies,
            timeout=30,
        )
        return json.loads(response.text)

    def save_image(self, image_url, image_filename):
        response = requests.get(
            url=image_url,
            headers=self._header,
            proxies=self._proxies,
            timeout=30,
        )
        with open(image_filename, 'wb') as fp:
            fp.write(response.content)
