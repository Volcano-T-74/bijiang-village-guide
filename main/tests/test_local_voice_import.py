from urllib.parse import quote

from django.core.management import call_command
from django.test import TestCase

from main.models import LocalVoice


class LocalVoiceImportTests(TestCase):
    def test_import_is_idempotent(self):
        call_command("import_local_voices", verbosity=0)
        call_command("import_local_voices", verbosity=0)

        self.assertEqual(LocalVoice.objects.count(), 5)
        expected = {
            "国语版 顺德碧江村介绍.m4a": ("顺德碧江村介绍（普通话）", 88, "zh-CN", "普通话"),
            "顺德碧江村介绍粤语版.m4a": ("顺德碧江村介绍（粤语）", 73, "yue", "粤语"),
            "中原路 4.m4a": ("中原路乡音", 118, "local", "当地讲述"),
            "20260719_223040.m4a": ("乡音记录一", 202, "local", "当地讲述"),
            "20260719_223446.m4a": ("乡音记录二", 198, "local", "当地讲述"),
        }
        for file_name, (title, duration, language, language_label) in expected.items():
            with self.subTest(file_name=file_name):
                voice = LocalVoice.objects.get(original_file_name=file_name)
                self.assertEqual(voice.title, title)
                self.assertEqual(voice.duration_seconds, duration)
                self.assertEqual(voice.language, language)
                self.assertEqual(voice.language_label, language_label)
                self.assertEqual(voice.file_url, f"/static/audio/{quote(file_name)}")
