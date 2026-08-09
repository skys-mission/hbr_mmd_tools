# -*- coding: utf-8 -*-
"""Tests for the pure VSE compatibility helpers (Sequence->Strip rename)."""
import unittest
from types import SimpleNamespace

from src.core.sequencer import (  # pylint: disable=import-error
    find_strip_by_name,
    get_scene_strips,
    get_strip_audio_filepath,
    get_top_level_strips,
)


def _sound_strip(name, channel=1, filepath="/tmp/audio.wav"):
    """构建一个 SOUND strip 桩对象。"""
    return SimpleNamespace(
        name=name,
        channel=channel,
        type='SOUND',
        sound=SimpleNamespace(filepath=filepath),
        frame_final_start=10.0,
    )


class GetTopLevelStripsTests(unittest.TestCase):
    """SequenceEditor.strips(4.4+) / sequences(<4.4) 双命名兼容。"""

    def test_none_sequence_editor(self):
        """无序列编辑器时返回空列表。"""
        self.assertEqual(get_top_level_strips(None), [])

    def test_legacy_sequences_only(self):
        """Blender < 4.4：从 sequences 读取。"""
        strip = _sound_strip("a")
        se = SimpleNamespace(sequences=[strip])
        self.assertEqual(get_top_level_strips(se), [strip])

    def test_strips_only(self):
        """Blender >= 5.0：仅存在 strips。"""
        strip = _sound_strip("a")
        se = SimpleNamespace(strips=[strip])
        self.assertEqual(get_top_level_strips(se), [strip])

    def test_strips_preferred_over_sequences(self):
        """Blender 4.4/4.5：两者并存时优先 strips。"""
        new_strip = _sound_strip("new")
        old_strip = _sound_strip("old")
        se = SimpleNamespace(strips=[new_strip], sequences=[old_strip])
        self.assertEqual(get_top_level_strips(se), [new_strip])

    def test_scene_without_sequence_editor(self):
        """场景从未创建序列编辑器时返回空列表。"""
        self.assertEqual(get_scene_strips(SimpleNamespace()), [])


class GetStripAudioFilepathTests(unittest.TestCase):
    """音频文件路径提取。"""

    def test_sound_strip(self):
        """SOUND strip 返回其 sound 的文件路径。"""
        strip = _sound_strip("a", filepath="/tmp/x.wav")
        self.assertEqual(get_strip_audio_filepath(strip), "/tmp/x.wav")

    def test_movie_strip(self):
        """MOVIE strip 同样从 sound 属性取路径。"""
        strip = SimpleNamespace(
            type='MOVIE', sound=SimpleNamespace(filepath="/tmp/x.mp4"))
        self.assertEqual(get_strip_audio_filepath(strip), "/tmp/x.mp4")

    def test_non_audio_strip(self):
        """非音频 strip 返回 None。"""
        strip = SimpleNamespace(type='IMAGE')
        self.assertIsNone(get_strip_audio_filepath(strip))

    def test_missing_sound_or_filepath(self):
        """sound 缺失或 filepath 为空时返回 None/空值而不抛异常。"""
        self.assertIsNone(
            get_strip_audio_filepath(SimpleNamespace(type='SOUND', sound=None)))
        self.assertIsNone(get_strip_audio_filepath(
            SimpleNamespace(type='SOUND', sound=SimpleNamespace(filepath=None))))


class FindStripByNameTests(unittest.TestCase):
    """按名称查找 strip，含旧版 "channel:name" 回退。"""

    def test_exact_match(self):
        """纯名称精确匹配。"""
        strips = [_sound_strip("a"), _sound_strip("b")]
        self.assertIs(find_strip_by_name(strips, "b"), strips[1])

    def test_empty_name(self):
        """空名称不匹配任何 strip。"""
        self.assertIsNone(find_strip_by_name([_sound_strip("a")], ""))
        self.assertIsNone(find_strip_by_name([_sound_strip("a")], None))

    def test_legacy_channel_name_unique(self):
        """旧版 "channel:name" 在唯一匹配时回退成功。"""
        strip = _sound_strip("a", channel=2)
        self.assertIs(find_strip_by_name([strip], "2:a"), strip)

    def test_legacy_channel_name_ambiguous(self):
        """旧版 "channel:name" 有多个同名 strip 时不回退。"""
        strips = [_sound_strip("a", channel=1), _sound_strip("a", channel=2)]
        self.assertIsNone(find_strip_by_name(strips, "2:a"))

    def test_no_match(self):
        """名称不存在时返回 None。"""
        self.assertIsNone(find_strip_by_name([_sound_strip("a")], "missing"))


if __name__ == '__main__':
    unittest.main()
