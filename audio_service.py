import base64
import json
import uuid
import requests

from config import Config


def text_to_speech(text):
    appid = Config.audio_appid
    access_token = Config.audio_token
    cluster = Config.tts_cluster

    uid = Config.tts_uid

    voice_type = 'S_xQTkZKmL'
    host = 'openspeech.bytedance.com'
    api_url = f'https://{host}/api/v1/tts'

    header = {'Authorization': f'Bearer;{access_token}'}

    request_json = {
        'app': {
            'appid': appid,
            'token': 'access_token',
            'cluster': cluster
        },
        'user': {
            'uid': uid,
        },
        'audio': {
            'voice_type': voice_type,
            'encoding': 'mp3',
            'speed_ratio': 1.0,
            'volume_ratio': 1.0,
            'pitch_ratio': 1.0,
        },
        'request': {
            'reqid': str(uuid.uuid4()),
            'text': text,
            'text_type': 'plain',
            'operation': 'query',
            'with_frontend': 1,
            'frontend_type': 'unitTson'

        }
    }
    resp = requests.post(api_url, json.dumps(request_json), headers=header)
    
    if 'data' not in resp.json():
        # TODO: add log
        pass

    data = resp.json()['data']
    data = base64.b64decode(data)

    start = 0
    while start < len(data):
        chunk = data[start: start + 1024]
        start += 1024
        yield chunk


def speech_to_text():
    pass
