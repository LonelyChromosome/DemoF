from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing marker: {label}")
    return text.replace(old, new, 1)


# 1) Force all palette-reading descendants to rebuild immediately when a theme changes.
app_path = ROOT / "lib/app/app.dart"
app = app_path.read_text(encoding="utf-8")
app = replace_once(
    app,
    "    super.initState();\n    unawaited(_restore());",
    "    super.initState();\n    AppThemeController.instance.addListener(_handleThemeChanged);\n    unawaited(_restore());",
    "AppRoot initState",
)
app = replace_once(
    app,
    "  Future<void> _restore() async {",
    """  void _handleThemeChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    AppThemeController.instance.removeListener(_handleThemeChanged);
    super.dispose();
  }

  Future<void> _restore() async {""",
    "AppRoot restore",
)
app_path.write_text(app, encoding="utf-8")


# 2) Replace the overlaid full-screen mask with a themed background and a tiny corner mask.
layout_path = ROOT / "platform/android_widget/app/src/main/res/layout/schedule_widget.xml"
layout_path.write_text(
    '''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/schedule_widget_background"
    android:clipChildren="true"
    android:clipToOutline="true"
    android:clipToPadding="true"
    android:outlineProvider="background">

    <ImageView
        android:id="@+id/widget_theme_background"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:clickable="false"
        android:contentDescription="@null"
        android:focusable="false"
        android:scaleType="fitXY" />

    <StackView
        android:id="@+id/widget_list"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:layout_gravity="center"
        android:animateFirstView="false"
        android:clickable="true"
        android:clipChildren="true"
        android:clipToPadding="true"
        android:loopViews="true" />

    <TextView
        android:id="@+id/widget_empty"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:gravity="center"
        android:paddingStart="18dp"
        android:paddingEnd="48dp"
        android:text="Không có lịch học"
        android:textColor="#FFFFFFFF"
        android:textSize="14sp"
        android:textStyle="bold" />

    <ImageView
        android:id="@+id/widget_stack_peek_mask"
        android:layout_width="40dp"
        android:layout_height="26dp"
        android:layout_gravity="bottom|end"
        android:clickable="false"
        android:contentDescription="@null"
        android:focusable="false" />

    <ImageView
        android:id="@+id/widget_calendar"
        android:layout_width="36dp"
        android:layout_height="36dp"
        android:layout_gravity="top|end"
        android:layout_marginTop="4dp"
        android:layout_marginEnd="8dp"
        android:background="@android:color/transparent"
        android:clickable="true"
        android:contentDescription="Chọn ngày hiển thị"
        android:focusable="true"
        android:padding="7dp"
        android:src="@drawable/ic_widget_calendar" />
</FrameLayout>
''',
    encoding="utf-8",
)


# 3) Render every themed card fully opaque; improve fit for pixel font and detail time.
service_path = ROOT / "platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt"
service = service_path.read_text(encoding="utf-8")
service = service.replace("import android.graphics.RectF\n", "")
start = service.index("        val radius = heightPx * CORNER_RADIUS_HEIGHT_FRACTION")
end = service.index("\n\n        // Every coordinate", start)
service = service[:start] + "        canvas.drawRect(0f, 0f, widthPx, heightPx, backgroundPaint)" + service[end:]
service = replace_once(
    service,
    "textSize = heightPx * SUBJECT_TEXT_HEIGHT_FRACTION",
    'textSize = heightPx * SUBJECT_TEXT_HEIGHT_FRACTION * if (theme.key == "minecraft") 0.86f else 1f',
    "subject size",
)
service = replace_once(
    service,
    "textSize = heightPx * DETAIL_TEXT_HEIGHT_FRACTION",
    'textSize = heightPx * DETAIL_TEXT_HEIGHT_FRACTION * if (theme.key == "minecraft") 0.84f else 1f',
    "detail size",
)
start = service.index("        val timeWidth = detailPaint.measureText(item.time)")
end = service.index("\n        val room = TextUtils.ellipsize(", start)
service = service[:start] + '''        var timeWidth = detailPaint.measureText(item.time)
        val availableDetailWidth = (detailRight - left).coerceAtLeast(1f)
        val minRoomWidth = widthPx * MIN_DETAIL_WIDTH_FRACTION
        val detailGap = widthPx * DETAIL_GAP_WIDTH_FRACTION
        if (item.time.isNotBlank() && timeWidth + minRoomWidth + detailGap > availableDetailWidth) {
            val fitScale = ((availableDetailWidth - minRoomWidth - detailGap) / timeWidth)
                .coerceIn(MIN_DETAIL_FIT_SCALE, 1f)
            detailPaint.textSize *= fitScale
            timeWidth = detailPaint.measureText(item.time)
        }
        val roomMaxWidth = (
            detailRight - left - timeWidth - detailGap
        ).coerceAtLeast(minRoomWidth)''' + service[end:]
service = replace_once(
    service,
    "private const val MIN_SUBJECT_FIT_SCALE = 0.78f",
    "private const val MIN_SUBJECT_FIT_SCALE = 0.64f\nprivate const val MIN_DETAIL_FIT_SCALE = 0.72f",
    "fit constants",
)
service = service.replace("private const val CORNER_RADIUS_HEIGHT_FRACTION = 0.28f\n", "")
service_path.write_text(service, encoding="utf-8")


# 4) Theme the whole widget host, avoid adapter cache reuse, and stop resetting the card on every refresh.
provider_path = ROOT / "platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt"
provider = provider_path.read_text(encoding="utf-8")
provider = replace_once(
    provider,
    "import android.content.SharedPreferences\n",
    "import android.content.SharedPreferences\nimport android.graphics.Bitmap\nimport android.graphics.Canvas\nimport android.graphics.LinearGradient\nimport android.graphics.Paint\nimport android.graphics.Shader\n",
    "graphics imports",
)

calendar_anchor = provider.index("            val calendarPaddingPx = (")
close_anchor = provider.index("\n        }\n\n        val sizeToken =", calendar_anchor)
mask_sizing = '''
            views.setViewLayoutWidth(
                R.id.widget_stack_peek_mask,
                widthDp * STACK_MASK_WIDTH_FRACTION,
                TypedValue.COMPLEX_UNIT_DIP,
            )
            views.setViewLayoutHeight(
                R.id.widget_stack_peek_mask,
                heightDp * STACK_MASK_HEIGHT_FRACTION,
                TypedValue.COMPLEX_UNIT_DIP,
            )'''
provider = provider[:close_anchor] + mask_sizing + provider[close_anchor:]

start = provider.index("        val sizeToken = String.format(")
end = provider.index("\n        views.setEmptyView(R.id.widget_list, R.id.widget_empty)", start)
provider = provider[:start] + '''        val theme = readThemeColors(context)
        views.setImageViewBitmap(
            R.id.widget_theme_background,
            renderThemeBackground(context, renderWidthDp, renderHeightDp, theme),
        )
        views.setInt(R.id.widget_stack_peek_mask, "setBackgroundColor", theme.endColor)
        views.setInt(R.id.widget_calendar, "setColorFilter", theme.iconColor)
        views.setTextColor(R.id.widget_empty, theme.textColor)

        val sizeToken = String.format(
            Locale.US,
            "%.1fx%.1f",
            widthDp,
            heightDp,
        )
        val serviceIntent = Intent(context, ScheduleWidgetService::class.java).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
            putExtra(EXTRA_RENDER_WIDTH_DP, renderWidthDp)
            putExtra(EXTRA_RENDER_HEIGHT_DP, renderHeightDp)
            data = Uri.parse("better-phenikaa://widget/$widgetId/$sizeToken/${theme.key}")
        }
        views.setRemoteAdapter(R.id.widget_list, serviceIntent)''' + provider[end:]

start = provider.index("        // The selected day (today by default) remains the first item")
end = provider.index("\n        return views", start)
provider = provider[:start] + '''        val selectionPrefs = context.getSharedPreferences(
            WIDGET_SELECTION_PREFS,
            Context.MODE_PRIVATE,
        )
        if (selectionPrefs.getBoolean(resetChildKey(widgetId), false)) {
            views.setDisplayedChild(R.id.widget_list, 0)
            selectionPrefs.edit().remove(resetChildKey(widgetId)).apply()
        }''' + provider[end:]

helper_marker = '    @Suppress("DEPRECATION")\n    private fun exactWidgetSizes'
helpers = '''    private data class ThemeColors(
        val key: String,
        val startColor: Int,
        val endColor: Int,
        val textColor: Int,
        val iconColor: Int,
    )

    private fun readThemeColors(context: Context): ThemeColors {
        val key = context
            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .getString("flutter.appTheme", "classic")
            ?: "classic"
        return when (key) {
            "lol" -> ThemeColors(key, 0xFF06131A.toInt(), 0xFF0B343A.toInt(), 0xFFF0E6D2.toInt(), 0xFFF0E6D2.toInt())
            "valorant" -> ThemeColors(key, 0xFF0F1923.toInt(), 0xFF24313B.toInt(), 0xFFECE8E1.toInt(), 0xFFECE8E1.toInt())
            "minecraft" -> ThemeColors(key, 0xFF3A2B20.toInt(), 0xFF6B4A2F.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "facebook" -> ThemeColors(key, 0xFFFFFFFF.toInt(), 0xFFE7F3FF.toInt(), 0xFF050505.toInt(), 0xFF0866FF.toInt())
            "shopee" -> ThemeColors(key, 0xFFEE4D2D.toInt(), 0xFFFF6A3D.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "tiktok" -> ThemeColors(key, 0xFF111111.toInt(), 0xFF2A1520.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "ben10" -> ThemeColors(key, 0xFF101510.toInt(), 0xFF1D5F22.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "youtube" -> ThemeColors(key, 0xFF181818.toInt(), 0xFF2B0E14.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "steam" -> ThemeColors(key, 0xFF171D25.toInt(), 0xFF1B3D55.toInt(), 0xFFD6E9F8.toInt(), 0xFFD6E9F8.toInt())
            else -> ThemeColors("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
        }
    }

    private fun renderThemeBackground(
        context: Context,
        widthDp: Int,
        heightDp: Int,
        theme: ThemeColors,
    ): Bitmap {
        val density = context.resources.displayMetrics.density
        val width = (widthDp.coerceAtLeast(1) * density).roundToInt().coerceAtLeast(1)
        val height = (heightDp.coerceAtLeast(1) * density).roundToInt().coerceAtLeast(1)
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            shader = LinearGradient(
                0f,
                0f,
                width.toFloat(),
                0f,
                theme.startColor,
                theme.endColor,
                Shader.TileMode.CLAMP,
            )
        }
        Canvas(bitmap).drawRect(0f, 0f, width.toFloat(), height.toFloat(), paint)
        return bitmap
    }

'''
provider = replace_once(provider, helper_marker, helpers + helper_marker, "provider helpers")
provider = replace_once(
    provider,
    '        fun selectedDateKey(widgetId: Int): String = "selected_date_$widgetId"',
    '        fun selectedDateKey(widgetId: Int): String = "selected_date_$widgetId"\n        fun resetChildKey(widgetId: Int): String = "reset_child_$widgetId"',
    "reset key",
)
provider = replace_once(
    provider,
    "        private const val CALENDAR_PADDING_FRACTION = 0.19f",
    "        private const val CALENDAR_PADDING_FRACTION = 0.19f\n        private const val STACK_MASK_WIDTH_FRACTION = 0.11f\n        private const val STACK_MASK_HEIGHT_FRACTION = 0.40f",
    "mask constants",
)
provider_path.write_text(provider, encoding="utf-8")


# 5) Only date changes reset StackView to item zero; ordinary refreshes keep swipe position.
picker_path = ROOT / "platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/WidgetDatePickerActivity.kt"
picker = picker_path.read_text(encoding="utf-8")
picker = replace_once(
    picker,
    '.putString(ScheduleWidgetProvider.selectedDateKey(widgetId), date)\n            .apply()',
    '.putString(ScheduleWidgetProvider.selectedDateKey(widgetId), date)\n            .putBoolean(ScheduleWidgetProvider.resetChildKey(widgetId), true)\n            .apply()',
    "date reset flag",
)
picker_path.write_text(picker, encoding="utf-8")

print("Better Phenikaa 2.0 live theme/widget repair applied")
