"""Private Telegram-to-MP3 bot; outbound connections only."""
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import parse_qs, urlsplit
import urllib.request
import uuid

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
USER_ID = os.environ.get('TELEGRAM_USER_ID', '')
DATA = Path(os.getenv('BOT_DATA_DIR', '/downloads'))
STATE = Path(os.getenv('BOT_STATE_DIR', '/state'))
LIMIT = 49_000_000
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')


def video_id(text):
    try:
        url = urlsplit(text.strip())
        if url.scheme not in ('http', 'https') or url.username or url.password or url.port:
            return None
        host = (url.hostname or '').lower()
        parts = url.path.strip('/').split('/')
        if host in ('youtu.be', 'www.youtu.be') and len(parts) == 1:
            candidate = parts[0]
        elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
            if url.path == '/watch':
                values = parse_qs(url.query).get('v', [])
                candidate = values[0] if len(values) == 1 else ''
            elif len(parts) == 2 and parts[0] in ('shorts', 'live', 'embed'):
                candidate = parts[1]
            else:
                return None
        else:
            return None
        return candidate if VIDEO_ID.fullmatch(candidate) else None
    except ValueError:
        return None


def api(method, payload):
    req = urllib.request.Request(f'https://api.telegram.org/bot{TOKEN}/{method}', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=45) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError('telegram_api_error')
    return result['result']


def send(chat, text):
    api('sendMessage', {'chat_id': chat, 'text': text})


def send_file(chat, path):
    boundary = uuid.uuid4().hex
    head = (f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{path.name}"\r\n'
            'Content-Type: audio/mpeg\r\n\r\n').encode()
    tail = f'\r\n--{boundary}--\r\n'.encode()
    conn = http.client.HTTPSConnection('api.telegram.org', timeout=180)
    try:
        conn.putrequest('POST', f'/bot{TOKEN}/sendDocument')
        conn.putheader('Content-Type', f'multipart/form-data; boundary={boundary}')
        conn.putheader('Content-Length', str(len(head) + path.stat().st_size + len(tail)))
        conn.endheaders()
        conn.send(head)
        with path.open('rb') as source:
            while chunk := source.read(1024 * 1024):
                conn.send(chunk)
        conn.send(tail)
        response = conn.getresponse()
        result = json.loads(response.read())
        if response.status != 200 or not result.get('ok'):
            raise RuntimeError('telegram_upload_failed')
    finally:
        conn.close()


def convert(vid):
    DATA.mkdir(parents=True, exist_ok=True)
    final = DATA / f'{vid}.mp3'
    if final.is_file() and final.stat().st_size:
        return final
    work = DATA / '.tmp' / vid
    work.mkdir(parents=True, exist_ok=True)
    cmd = ['yt-dlp', '--ignore-config', '--no-playlist', '--js-runtimes', 'deno',
           '--abort-on-unavailable-fragments', '--retries', '3', '--socket-timeout', '30',
           '-f', 'bestaudio', '-x', '--audio-format', 'mp3', '--audio-quality', '192K',
           '--no-progress', '--no-warnings', '-o', str(work / 'source.%(ext)s'),
           f'https://www.youtube.com/watch?v={vid}']
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=7200)
    output = work / 'source.mp3'
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name:format=duration', '-of', 'json', str(output)],
                           capture_output=True, check=True, timeout=60)
    info = json.loads(probe.stdout)
    if (not any(stream.get('codec_name') == 'mp3' for stream in info.get('streams', []))
            or float(info.get('format', {}).get('duration', 0)) <= 0
            or not output.is_file() or not output.stat().st_size):
        raise RuntimeError('empty_audio')
    output.replace(final)
    return final


def handle(update):
    message = update.get('message') or {}
    chat = message.get('chat') or {}
    sender = message.get('from') or {}
    if chat.get('type') != 'private' or str(sender.get('id')) != USER_ID or str(chat.get('id')) != USER_ID:
        return
    text = (message.get('text') or '').strip()
    if text in ('/start', '/help'):
        send(chat['id'], '유튜브 영상 링크를 보내면 MP3로 변환합니다. 결과는 NAS에도 저장됩니다.')
        return
    vid = video_id(text)
    if not vid:
        send(chat['id'], '유튜브 영상 링크 하나를 보내주세요.')
        return
    send(chat['id'], '변환을 시작합니다. 영상 길이에 따라 시간이 걸릴 수 있습니다.')
    try:
        path = convert(vid)
        if path.stat().st_size <= LIMIT:
            send_file(chat['id'], path)
        else:
            send(chat['id'], f'변환 완료. 파일이 텔레그램 전송 한도를 넘어 NAS에 저장했습니다: {path.name}')
    except Exception:
        send(chat['id'], '변환 또는 전송에 실패했습니다. 영상 접근 가능 여부와 NAS 상태를 확인한 후 다시 보내주세요.')


def main():
    if not TOKEN or not USER_ID.isdigit() or int(USER_ID) <= 0:
        raise SystemExit('TELEGRAM_BOT_TOKEN and numeric TELEGRAM_USER_ID are required')
    STATE.mkdir(parents=True, exist_ok=True)
    offset_file = STATE / 'telegram-offset'
    offset = int(offset_file.read_text()) if offset_file.exists() else 0
    while True:
        try:
            for update in api('getUpdates', {'offset': offset, 'timeout': 30, 'allowed_updates': ['message']}):
                handle(update)
                offset = update['update_id'] + 1
                tmp = offset_file.with_suffix('.tmp')
                tmp.write_text(str(offset))
                tmp.replace(offset_file)
        except Exception:
            print('Telegram polling or processing failed; retrying.', flush=True)
            time.sleep(10)


if __name__ == '__main__':
    main()
