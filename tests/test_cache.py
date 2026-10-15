# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from deck_builder import VOICE, audio_for, cleanup_audio_cache


class CacheTests(unittest.TestCase):
    def test_cleanup_age_boundary_and_unrelated_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            now = 2_000_000_000
            cutoff = now - 30 * 86400
            for key, timestamp in [('a', cutoff - 1), ('b', cutoff), ('c', now)]:
                path = root / f'anki_eka_{key * 64}.mp3'
                path.write_bytes(b'audio')
                os.utime(path, (timestamp, timestamp))
            unrelated = root / 'personal.mp3'
            unrelated.write_bytes(b'keep')
            os.utime(unrelated, (0, 0))
            link = root / f'anki_eka_{"d" * 64}.mp3'
            link.symlink_to(unrelated)
            nested = root / f'anki_eka_{"e" * 64}.mp3'
            nested.mkdir()
            self.assertEqual(cleanup_audio_cache(root, now=now), 1)
            self.assertFalse((root / f'anki_eka_{"a" * 64}.mp3').exists())
            self.assertTrue((root / f'anki_eka_{"b" * 64}.mp3').exists())
            self.assertTrue(unrelated.exists())
            self.assertTrue(link.is_symlink())
            self.assertTrue(nested.is_dir())
            self.assertEqual(cleanup_audio_cache(root / 'missing'), 0)

    def test_cache_hit_refreshes_last_use_without_synthesis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            text = 'წყალი'
            key = hashlib.sha256(f'{VOICE}\x00{text}'.encode()).hexdigest()
            path = root / f'anki_eka_{key}.mp3'
            path.write_bytes(b'audio')
            os.utime(path, (1, 1))
            with patch('deck_builder.generate_audio') as generate:
                self.assertEqual(audio_for(text, root), path)
                generate.assert_not_called()
            self.assertGreater(path.stat().st_mtime, 1)
            self.assertEqual(cleanup_audio_cache(root), 0)
