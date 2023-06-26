from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
import logging
import json
import requests
import time
import threading


class MidjourneyBot:
    _APPLICATION_ID = '936929561302675456'
    _SESSION_ID = '1aaff965b0542ea8ed94127f3db5668a'
    _DATA_VERSION = '1118961510123847772'
    _DATA_ID = '938956540159881230'
    _APPLICATION_COMMMAND_VERSION = '1118961510123847772'

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
            "application_id": self._APPLICATION_ID,
            "guild_id": self._server_id,
            "channel_id": self._channel_id,
            "session_id": self._SESSION_ID,
            "data": {
                "version": self._DATA_VERSION,
                "id": self._DATA_ID,
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
                        self._APPLICATION_COMMMAND_VERSION,
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
            "application_id": self._APPLICATION_ID,
            "session_id": self._SESSION_ID,
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
            "application_id": self._APPLICATION_ID,
            "session_id": self._SESSION_ID,
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


class BatchBot(MidjourneyBot):

    def __init__(self, config_file='config.json', image_folder='images'):
        super().__init__(config_file)
        self._image_folder = Path(image_folder)
        self._image_folder.mkdir(parents=True, exist_ok=True)

        self._prompts = Queue()

        # collect finished messages with prompt to message info dict
        self._messages_info_lock = threading.Lock()
        self._messages_info = {}

        # collect user requests with message-id to message info dict
        # message info could use for later upscale
        self._results_lock = threading.Lock()
        self._results = {}

        self._stop_event = threading.Event()

        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._thread_pool.submit(self.imagine, self._stop_event)
        self._thread_pool.submit(self.fetch, self._stop_event)

        self._worker_pool = ThreadPoolExecutor(max_workers=10)

    @property
    def results(self):
        with self._results_lock:
            return self._results

    def cancel_tasks(self):
        self._stop_event.set()

    def prompt(self, prompt):
        self._prompts.put(prompt)
        self._worker_pool.submit(self.worker, prompt)

    def imagine(self, event: threading.Event):
        while not event.is_set():
            if not self._prompts.empty():
                prompt = self._prompts.get()
                self.ask(prompt)
                self._prompts.task_done()
            time.sleep(3)

    def _save_image(self, attachments):
        response = requests.get(
            url=attachments['url'],
            headers=self._header,
            proxies=self._proxies,
            timeout=30,
        )
        logging.info(f'Downloading {attachments["filename"]}')
        image_file = self._image_folder / attachments["filename"]
        with open(image_file, 'wb') as fp:
            fp.write(response.content)

    def _parse_messages(self, messages):
        for message in messages[::-1]:
            if not message:
                continue
            try:
                content = message['content'].split("**")[1]
                if '--' in content:
                    content = content.split('--')[0].strip()
                if self._validate_image_url(message):
                    with self._messages_info_lock:
                        self._messages_info[content] = message
            except IndexError as e:
                logging.exception(e)
                continue

    def _validate_image_url(self, message_info):
        if message_info['attachments'] and message_info['attachments'][0][
                'content_type'] == 'image/png':
            return True
        return False

    def fetch(self, event: threading.Event):
        while not event.is_set():
            messages_url = f'https://discord.com/api/v9/channels/{self._channel_id}/messages'
            response = requests.get(
                url=messages_url,
                headers=self._header,
                proxies=self._proxies,
                timeout=30,
            )
            self._parse_messages(json.loads(response.text))
            time.sleep(10)

    def worker(self, prompt):
        while True:
            with self._messages_info_lock:
                message_info = self._messages_info.get(prompt, None)
            if message_info:
                message_id = message_info['id']
                self._save_image(message_info['attachments'][0])
                with self._results_lock:
                    self._results[message_id] = message_info
                return
            time.sleep(5)
