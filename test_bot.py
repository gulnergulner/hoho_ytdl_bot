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

    def test_large_file_stays_on_nas(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'abcdefghijk.mp3'
            path.write_bytes(b'123')
            message = {'message': {'chat': {'id': 123, 'type': 'private'}, 'from': {'id': 123}, 'text': 'https://youtu.be/abcdefghijk'}}
            with patch.object(bot, 'USER_ID', '123'), patch.object(bot, 'LIMIT', 2), patch.object(bot, 'convert', return_value=path), patch.object(bot, 'send') as send, patch.object(bot, 'send_file') as upload:
                bot.handle(message)
                upload.assert_not_called()
                self.assertIn(path.name, send.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
