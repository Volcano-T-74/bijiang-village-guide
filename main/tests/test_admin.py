from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from main.admin import FavoriteAdmin, FootprintAdmin, VisitorSessionAdmin
from main.models import Favorite, Footprint, Theme, VisitorSession, Zone


class SimpleUIMenuTests(TestCase):
    def test_menu_groups_and_real_admin_urls_are_configured(self):
        from django.conf import settings

        groups = {item["name"]: item for item in settings.SIMPLEUI_CONFIG["menus"]}
        self.assertEqual(
            set(groups),
            {"数据概览", "内容资产库", "空间与路线", "触点管理", "游客行为", "系统管理"},
        )
        content_urls = {item["url"] for item in groups["内容资产库"]["models"]}
        self.assertIn("/admin/main/attraction/", content_urls)
        self.assertIn("/admin/main/storycontent/", content_urls)
        self.assertIn("/admin/main/audioasset/", content_urls)


class DataOverviewTests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin-test", password="test-password"
        )

    def test_anonymous_user_is_redirected_to_admin_login(self):
        response = self.client.get("/admin/data-overview/")

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_dashboard_uses_current_database_counts(self):
        Zone.objects.create(
            zone_name="大宗祠群落",
            center_latitude="22.12345678",
            center_longitude="113.12345678",
            visual_cue="大榕树",
            description="宗祠集中区域",
        )
        Theme.objects.create(
            name="岭南建筑", icon="building", description="岭南建筑线索"
        )
        self.client.force_login(self.superuser)

        response = self.client.get("/admin/data-overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["counts"]["zones"], 1)
        self.assertEqual(response.context["counts"]["themes"], 1)
        self.assertContains(response, "大宗祠群落", count=0)
        self.assertContains(response, "暂无游客会话")


class ReadOnlyBehaviorAdminTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.request.user = get_user_model().objects.create_superuser(
            username="permission-test", password="test-password"
        )

    def test_behavior_evidence_models_are_read_only(self):
        configurations = (
            VisitorSessionAdmin(VisitorSession, admin.site),
            FootprintAdmin(Footprint, admin.site),
            FavoriteAdmin(Favorite, admin.site),
        )

        for model_admin in configurations:
            with self.subTest(model=model_admin.model.__name__):
                self.assertFalse(model_admin.has_add_permission(self.request))
                self.assertFalse(model_admin.has_change_permission(self.request))
                self.assertFalse(model_admin.has_delete_permission(self.request))


class ChineseMetadataTests(TestCase):
    def test_representative_models_and_fields_have_chinese_labels(self):
        self.assertEqual(Zone._meta.verbose_name_plural, "区域管理")
        self.assertEqual(Zone._meta.get_field("zone_name").verbose_name, "区域名称")
        self.assertEqual(
            VisitorSession._meta.verbose_name_plural, "匿名游客会话"
        )
        self.assertEqual(
            Footprint._meta.get_field("triggered_at").verbose_name, "触发时间"
        )
