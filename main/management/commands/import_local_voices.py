from urllib.parse import quote

from django.core.management.base import BaseCommand

from main.models import LocalVoice


LOCAL_VOICES = (
    ("国语版 顺德碧江村介绍.m4a", "顺德碧江村介绍（普通话）", 88, "zh-CN", "普通话"),
    ("顺德碧江村介绍粤语版.m4a", "顺德碧江村介绍（粤语）", 73, "yue", "粤语"),
    ("中原路 4.m4a", "中原路乡音", 118, "local", "当地讲述"),
    ("20260719_223040.m4a", "乡音记录一", 202, "local", "当地讲述"),
    ("20260719_223446.m4a", "乡音记录二", 198, "local", "当地讲述"),
)


class Command(BaseCommand):
    help = "Import the fixed set of local voice recordings."

    def handle(self, *args, **options):
        for file_name, title, duration, language, language_label in LOCAL_VOICES:
            LocalVoice.objects.update_or_create(
                original_file_name=file_name,
                defaults={
                    "title": title,
                    "file_url": f"/static/audio/{quote(file_name)}",
                    "duration_seconds": duration,
                    "language": language,
                    "language_label": language_label,
                },
            )

        self.stdout.write(self.style.SUCCESS("Imported 5 local voices."))
