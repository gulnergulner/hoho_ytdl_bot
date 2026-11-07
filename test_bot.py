import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bot', Path(__file__).with_name('bot.py'))
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


class BotTests(unittest.TestCase):
    def test_youtube_links_are_canonicalized(self):
        for url in ['https://youtu.be/abcdefghijk?t=2', 'https://www.youtube.com/watch?v=abcdefghijk&list=anything', 'https://m.youtube.com/shorts/abcdefghijk']:
            self.assertEqual(bot.video_id(url), 'abcdefghijk')
        for url in ['https://youtube.com.evil.test/watch?v=abcdefghijk', 'https://youtube.com/@channel', 'https://youtu.be/../../x', 'https://user@youtube.com/watch?v=abcdefghijk', 'https://youtube.com/watch?v=abcdefghijk&v=12345678901']:
            self.assertIsNone(bot.video_id(url))

    def test_only_authorized_private_chat_is_processed(self):
        with patch.object(bot, 'USER_ID', '123'), patch.object(bot, 'send') as send:
            bot.handle({'message': {'chat': {'id': 123, 'type': 'group'}, 'from': {'id': 123}, 'text': '/start'}})
            bot.handle({'message': {'chat': {'id': 456, 'type': 'private'}, 'from': {'id': 456}, 'text': '/start'}})
            send.assert_not_called()
            bot.handle({'message': {'chat': {'id': 123, 'type': 'private'}, 'from': {'id': 123}, 'text': '/start'}})
            send.assert_called_once()

    def test_title_is_safe_and_length_limited(self):
        self.assertEqual(bot.safe_title(' 찬양/예배: 제목 '), '찬양_예배_ 제목')
        self.assertLessEqual(len(bot.safe_title('한' * 200).encode()), 180)
        self.assertEqual(bot.safe_title('...'), '제목 없음')

    def test_link_is_sent_instead_of_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '제목 [abcdefghijk].mp3'
            path.write_bytes(b'audio')
            message = {'message': {'chat': {'id': 123, 'type': 'private'}, 'from': {'id': 123}, 'text': 'https://youtu.be/abcdefghijk'}}
            with patch.object(bot, 'USER_ID', '123'), patch.object(bot, 'convert', return_value=path), patch.object(bot, 'sharing_link', return_value=('https://gofile.me/example', '2026-11-08')), patch.object(bot, 'send') as send:
                bot.handle(message)
                self.assertIn('https://gofile.me/example', send.call_args.args[1])
                self.assertIn(path.name, send.call_args.args[1])

    def test_sharing_uses_dsm_path_and_expiration(self):
        env = {'DSM_URL': 'https://nas.example.com:5001', 'DSM_ACCOUNT': 'bot', 'DSM_PASSWORD': 'secret', 'DSM_DOWNLOADS_PATH': '/docker/bot/data/telegram'}
        results = [{'sid': 'session'}, {'links': [{'url': 'https://gofile.me/example', 'error': 0}]}, {}]
        with patch.dict(bot.os.environ, env), patch.object(bot, 'dsm_request', side_effect=results) as request:
            link, expiry = bot.sharing_link(Path('찬양 [abcdefghijk].mp3'))
            self.assertEqual(link, 'https://gofile.me/example')
            self.assertIn('찬양', request.call_args_list[1].args[2]['path'])
            self.assertEqual(request.call_args_list[1].args[2]['date_expired'], bot.json.dumps(expiry))


if __name__ == '__main__':
    unittest.main()
