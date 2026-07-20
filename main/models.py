import uuid

from django.db import models


class Zone(models.Model):
    id = models.AutoField("ID", primary_key=True)
    zone_name = models.CharField("区域名称", max_length=20)
    center_latitude = models.DecimalField(
        "中心纬度", max_digits=10, decimal_places=8, null=True, blank=True
    )
    center_longitude = models.DecimalField(
        "中心经度", max_digits=11, decimal_places=8, null=True, blank=True
    )
    visual_cue = models.CharField("视觉地标提示", max_length=100)
    description = models.CharField("区域氛围描述", max_length=200)

    class Meta:
        db_table = "zones"
        ordering = ("id",)
        verbose_name = "区域"
        verbose_name_plural = "区域管理"

    def __str__(self):
        return self.zone_name


class Attraction(models.Model):
    class Type(models.TextChoices):
        ANCESTRAL_HALL = "祠堂", "祠堂"
        BRIDGE = "桥", "桥"
        WATERFRONT = "水岸", "水岸"
        WHARF = "码头", "码头"
        LANE = "巷", "巷"

    class DepthLevel(models.IntegerChoices):
        BASIC = 1, "基础展示"
        DEEP = 2, "深度闭环"

    class Status(models.IntegerChoices):
        DISABLED = 0, "下架"
        ENABLED = 1, "启用"

    id = models.AutoField("ID", primary_key=True)
    zone = models.ForeignKey(
        Zone, verbose_name="所属区域", on_delete=models.PROTECT, related_name="attractions"
    )
    name = models.CharField("景点名称", max_length=50)
    slug = models.SlugField("URL 标识", max_length=50, unique=True)
    subtitle = models.CharField("副标题", max_length=100)
    type = models.CharField("景点分类", max_length=20, choices=Type.choices)
    depth_level = models.SmallIntegerField(
        "展示深度", choices=DepthLevel.choices, default=DepthLevel.BASIC
    )
    cover_image_url = models.TextField("封面图地址")
    latitude = models.DecimalField(
        "纬度", max_digits=10, decimal_places=8, null=True, blank=True
    )
    longitude = models.DecimalField(
        "经度", max_digits=11, decimal_places=8, null=True, blank=True
    )
    map_x_percent = models.DecimalField(
        "手绘地图横坐标（%）", max_digits=5, decimal_places=2, null=True, blank=True
    )
    map_y_percent = models.DecimalField(
        "手绘地图纵坐标（%）", max_digits=5, decimal_places=2, null=True, blank=True
    )
    display_order = models.SmallIntegerField("后台排序", default=0)
    status = models.SmallIntegerField(
        "状态", choices=Status.choices, default=Status.ENABLED
    )

    class Meta:
        db_table = "attractions"
        ordering = ("display_order", "id")
        verbose_name = "景点"
        verbose_name_plural = "景点管理"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(depth_level__in=[1, 2]),
                name="attractions_depth_level_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=[0, 1]),
                name="attractions_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(map_x_percent__isnull=True)
                    | models.Q(map_x_percent__gte=0, map_x_percent__lte=100)
                ),
                name="attractions_map_x_percent_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(map_y_percent__isnull=True)
                    | models.Q(map_y_percent__gte=0, map_y_percent__lte=100)
                ),
                name="attractions_map_y_percent_valid",
            ),
        ]

    def __str__(self):
        return self.name


class StoryContent(models.Model):
    id = models.AutoField("ID", primary_key=True)
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="所属景点",
        on_delete=models.CASCADE,
        related_name="story_contents",
    )
    full_text = models.TextField("完整历史故事")
    audio_script = models.TextField("语音讲解脚本")
    fun_fact = models.CharField("一句冷知识", max_length=200)
    version = models.SmallIntegerField("内容版本号", default=1)

    class Meta:
        db_table = "story_contents"
        ordering = ("attraction_id", "-version")
        verbose_name = "故事内容"
        verbose_name_plural = "故事内容"
        constraints = [
            models.UniqueConstraint(
                fields=("attraction", "version"),
                name="story_contents_attraction_version_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1),
                name="story_contents_version_positive",
            ),
        ]

    def __str__(self):
        return f"{self.attraction} v{self.version}"


class AudioAsset(models.Model):
    id = models.AutoField("ID", primary_key=True)
    content = models.ForeignKey(
        StoryContent,
        verbose_name="故事内容",
        on_delete=models.CASCADE,
        related_name="audio_assets",
    )
    file_name = models.CharField("原始文件名", max_length=100)
    file_url = models.TextField("音频文件地址")
    duration_seconds = models.IntegerField("音频时长（秒）")
    language = models.CharField("语言", max_length=10, default="zh-CN")

    class Meta:
        db_table = "audio_assets"
        ordering = ("content_id", "id")
        verbose_name = "音频资源"
        verbose_name_plural = "音频资源"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="audio_assets_duration_nonnegative",
            )
        ]

    def __str__(self):
        return self.file_name


class LocalVoice(models.Model):
    id = models.AutoField("ID", primary_key=True)
    title = models.CharField("标题", max_length=100)
    original_file_name = models.CharField("原始文件名", max_length=100, unique=True)
    file_url = models.TextField("音频文件地址")
    duration_seconds = models.PositiveIntegerField("音频时长（秒）")
    language = models.CharField("语言", max_length=20, default="local")
    language_label = models.CharField("语言标签", max_length=20, default="当地讲述")
    display_order = models.PositiveSmallIntegerField("后台排序", default=0)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "local_voices"
        ordering = ("display_order", "id")
        verbose_name = "当地声音"
        verbose_name_plural = "当地声音"

    def __str__(self):
        return self.title


class Theme(models.Model):
    id = models.AutoField("ID", primary_key=True)
    name = models.CharField("主题名称", max_length=20, unique=True)
    icon = models.CharField("图标类名", max_length=50)
    description = models.CharField("主题简介", max_length=100)

    class Meta:
        db_table = "themes"
        ordering = ("id",)
        verbose_name = "叙事主题"
        verbose_name_plural = "叙事主题"

    def __str__(self):
        return self.name


class AttractionTheme(models.Model):
    id = models.AutoField("ID", primary_key=True)
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="景点",
        on_delete=models.CASCADE,
        related_name="theme_links",
    )
    theme = models.ForeignKey(
        Theme,
        verbose_name="叙事主题",
        on_delete=models.CASCADE,
        related_name="attraction_links",
    )

    class Meta:
        db_table = "attraction_themes"
        ordering = ("attraction_id", "theme_id")
        verbose_name = "景点主题标签"
        verbose_name_plural = "景点主题标签"
        constraints = [
            models.UniqueConstraint(
                fields=("attraction", "theme"),
                name="attraction_themes_pair_unique",
            )
        ]

    def __str__(self):
        return f"{self.attraction} - {self.theme}"


class HiddenDetail(models.Model):
    id = models.AutoField("ID", primary_key=True)
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="所属景点",
        on_delete=models.CASCADE,
        related_name="hidden_details",
    )
    detail_text = models.CharField("彩蛋文案", max_length=300)
    poi_latitude = models.DecimalField("彩蛋纬度", max_digits=10, decimal_places=8)
    poi_longitude = models.DecimalField("彩蛋经度", max_digits=11, decimal_places=8)
    trigger_distance_meters = models.SmallIntegerField("触发距离（米）")

    class Meta:
        db_table = "hidden_details"
        ordering = ("attraction_id", "id")
        verbose_name = "隐藏彩蛋"
        verbose_name_plural = "沿途隐藏彩蛋"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(trigger_distance_meters__gt=0),
                name="hidden_details_trigger_distance_positive",
            )
        ]

    def __str__(self):
        return f"{self.attraction}: {self.detail_text[:30]}"


class AttractionPath(models.Model):
    id = models.AutoField("ID", primary_key=True)
    from_attraction = models.ForeignKey(
        Attraction,
        verbose_name="起点景点",
        on_delete=models.CASCADE,
        related_name="outgoing_paths",
    )
    to_attraction = models.ForeignKey(
        Attraction,
        verbose_name="终点景点",
        on_delete=models.CASCADE,
        related_name="incoming_paths",
    )
    distance_meters = models.IntegerField("步行距离（米）")
    estimated_minutes = models.IntegerField("预计步行时间（分钟）")
    is_scenic_route = models.BooleanField("风景推荐路径", default=False)

    class Meta:
        db_table = "attraction_paths"
        ordering = ("from_attraction_id", "to_attraction_id")
        verbose_name = "景点路径"
        verbose_name_plural = "景点路径"
        constraints = [
            models.UniqueConstraint(
                fields=("from_attraction", "to_attraction"),
                name="attraction_paths_pair_unique",
            ),
            models.CheckConstraint(
                condition=~models.Q(from_attraction=models.F("to_attraction")),
                name="attraction_paths_distinct_nodes",
            ),
            models.CheckConstraint(
                condition=models.Q(distance_meters__gte=0),
                name="attraction_paths_distance_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_minutes__gte=0),
                name="attraction_paths_minutes_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.from_attraction} -> {self.to_attraction}"


class Touchpoint(models.Model):
    class TriggerType(models.TextChoices):
        QR = "qr", "二维码"
        NFC = "nfc", "NFC"
        SIMULATE = "simulate", "模拟"

    id = models.AutoField("ID", primary_key=True)
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="关联景点",
        on_delete=models.CASCADE,
        related_name="touchpoints",
    )
    trigger_code = models.CharField("唯一触发码", max_length=20, unique=True)
    trigger_type = models.CharField("触发类型", max_length=10, choices=TriggerType.choices)
    physical_location = models.CharField("实体位置描述", max_length=100)

    class Meta:
        db_table = "touchpoints"
        ordering = ("attraction_id", "trigger_code")
        verbose_name = "触点"
        verbose_name_plural = "触点管理"

    def __str__(self):
        return self.trigger_code


class VisitorSession(models.Model):
    id = models.UUIDField("会话 ID", primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField("首次访问时间", auto_now_add=True)
    last_active_at = models.DateTimeField("最后活跃时间", auto_now=True)
    preference_tags = models.JSONField("兴趣标签", default=list, blank=True)
    last_known_zone = models.ForeignKey(
        Zone,
        verbose_name="上次所在区域",
        on_delete=models.SET_NULL,
        related_name="visitor_sessions",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "visitor_sessions"
        ordering = ("-last_active_at",)
        verbose_name = "匿名游客会话"
        verbose_name_plural = "匿名游客会话"

    def __str__(self):
        return str(self.id)


class Itinerary(models.Model):
    id = models.AutoField("ID", primary_key=True)
    session = models.ForeignKey(
        VisitorSession,
        verbose_name="游客会话",
        on_delete=models.CASCADE,
        related_name="itineraries",
    )
    zone_sequence = models.JSONField("区域顺序", default=list)
    attraction_sequence = models.JSONField("景点顺序", default=list)
    narrative_bridge = models.JSONField("叙事过渡提示", default=dict)
    preference_tags_snapshot = models.JSONField("兴趣标签快照", default=list)
    planning_mode = models.CharField("规划模式", max_length=10, default="relaxed")
    duration_limit_minutes = models.IntegerField("时长上限（分钟）", default=60)
    score = models.IntegerField("路线评分", default=0)
    total_estimated_minutes = models.IntegerField("预计总时长（分钟）")
    generated_at = models.DateTimeField("生成时间", auto_now_add=True)
    is_completed = models.BooleanField("是否完成", default=False)

    class Meta:
        db_table = "itineraries"
        ordering = ("-generated_at",)
        verbose_name = "专属路线"
        verbose_name_plural = "专属路线"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_estimated_minutes__gte=0),
                name="itineraries_minutes_nonnegative",
            )
        ]

    def __str__(self):
        return f"{self.session} - {self.generated_at}"


class Footprint(models.Model):
    id = models.BigAutoField("ID", primary_key=True)
    session = models.ForeignKey(
        VisitorSession,
        verbose_name="游客会话",
        on_delete=models.CASCADE,
        related_name="footprints",
    )
    itinerary = models.ForeignKey(
        Itinerary,
        verbose_name="所属路线",
        on_delete=models.CASCADE,
        related_name="footprints",
    )
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="触发景点",
        on_delete=models.CASCADE,
        related_name="footprints",
    )
    touchpoint = models.ForeignKey(
        Touchpoint,
        verbose_name="触发触点",
        on_delete=models.CASCADE,
        related_name="footprints",
    )
    triggered_at = models.DateTimeField("触发时间", auto_now_add=True)
    audio_played = models.BooleanField("音频是否完整播放", default=False)

    class Meta:
        db_table = "footprints"
        ordering = ("-triggered_at",)
        verbose_name = "足迹触发日志"
        verbose_name_plural = "足迹触发日志"

    def __str__(self):
        return f"{self.session} - {self.attraction}"


class VisitorEvent(models.Model):
    id = models.BigAutoField("ID", primary_key=True)
    session = models.ForeignKey(
        VisitorSession,
        verbose_name="游客会话",
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField("事件类型", max_length=50)
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="关联景点",
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    itinerary = models.ForeignKey(
        Itinerary,
        verbose_name="关联路线",
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    metadata = models.JSONField("补充数据", default=dict, blank=True)
    created_at = models.DateTimeField("记录时间", auto_now_add=True)

    class Meta:
        db_table = "visitor_events"
        ordering = ("-created_at",)
        verbose_name = "游客行为事件"
        verbose_name_plural = "游客行为事件"

    def __str__(self):
        return f"{self.session} - {self.event_type}"


class Favorite(models.Model):
    id = models.AutoField("ID", primary_key=True)
    session = models.ForeignKey(
        VisitorSession,
        verbose_name="游客会话",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    attraction = models.ForeignKey(
        Attraction,
        verbose_name="收藏景点",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        db_table = "favorites"
        ordering = ("-created_at",)
        verbose_name = "故事收藏"
        verbose_name_plural = "故事收藏"
        constraints = [
            models.UniqueConstraint(
                fields=("session", "attraction"),
                name="favorites_session_attraction_unique",
            )
        ]

    def __str__(self):
        return f"{self.session} - {self.attraction}"
