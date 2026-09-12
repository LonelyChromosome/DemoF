from pathlib import Path

provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
s = provider.read_text(encoding='utf-8')

class_marker = 'class ScheduleWidgetProvider : HomeWidgetProvider() {\n'
on_receive = '''class ScheduleWidgetProvider : HomeWidgetProvider() {\n    override fun onReceive(context: Context, intent: Intent) {\n        if (intent.action == ACTION_COLLECTION_FRAME_READY) {\n            val widgetId = intent.getIntExtra(\n                AppWidgetManager.EXTRA_APPWIDGET_ID,\n                AppWidgetManager.INVALID_APPWIDGET_ID,\n            )\n            val readyThemeKey = intent.getStringExtra(EXTRA_READY_THEME_KEY)\n            if (\n                widgetId != AppWidgetManager.INVALID_APPWIDGET_ID &&\n                readyThemeKey != null\n            ) {\n                revealCollectionWhenReady(context, widgetId, readyThemeKey)\n            }\n            return\n        }\n        super.onReceive(context, intent)\n    }\n\n'''
if 'ACTION_COLLECTION_FRAME_READY' not in s:
    if class_marker not in s:
        raise SystemExit('provider class marker missing')
    s = s.replace(class_marker, on_receive, 1)

s = s.replace('            scheduleRefreshCoverHide(context, appWidgetManager, widgetId)\n', '', 2)

old_hide = '''    private fun scheduleRefreshCoverHide(\n        context: Context,\n        appWidgetManager: AppWidgetManager,\n        widgetId: Int,\n    ) {\n        Handler(Looper.getMainLooper()).postDelayed({\n            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)\n            reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)\n            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n            appWidgetManager.partiallyUpdateAppWidget(widgetId, reveal)\n        }, REFRESH_COVER_HOLD_MS)\n    }\n'''
new_hide = '''    private fun revealCollectionWhenReady(\n        context: Context,\n        widgetId: Int,\n        readyThemeKey: String,\n    ) {\n        // Never reveal a frame that belongs to an older rapid theme change.\n        if (readyThemeKey != readThemeColors(context).key) {\n            return\n        }\n        Handler(Looper.getMainLooper()).postDelayed({\n            if (readyThemeKey != readThemeColors(context).key) {\n                return@postDelayed\n            }\n            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)\n            reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)\n            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n            AppWidgetManager.getInstance(context)\n                .partiallyUpdateAppWidget(widgetId, reveal)\n        }, COLLECTION_READY_SETTLE_MS)\n    }\n'''
if old_hide not in s:
    raise SystemExit('old timed cover hide block missing')
s = s.replace(old_hide, new_hide, 1)

extras_marker = '''        const val EXTRA_RENDER_WIDTH_DP = "renderWidthDp"\n        const val EXTRA_RENDER_HEIGHT_DP = "renderHeightDp"\n        const val WIDGET_SELECTION_PREFS = "better_phenikaa_widget_selection"\n'''
extras_new = '''        const val EXTRA_RENDER_WIDTH_DP = "renderWidthDp"\n        const val EXTRA_RENDER_HEIGHT_DP = "renderHeightDp"\n        const val ACTION_COLLECTION_FRAME_READY =\n            "vn.edu.phenikaa.better_phenikaa_schedule.COLLECTION_FRAME_READY"\n        const val EXTRA_READY_THEME_KEY = "readyThemeKey"\n        const val WIDGET_SELECTION_PREFS = "better_phenikaa_widget_selection"\n'''
if extras_marker not in s:
    raise SystemExit('provider extras marker missing')
s = s.replace(extras_marker, extras_new, 1)
s = s.replace('        private const val REFRESH_COVER_HOLD_MS = 1600L\n', '        private const val COLLECTION_READY_SETTLE_MS = 300L\n', 1)
provider.write_text(s, encoding='utf-8')

service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
t = service.read_text(encoding='utf-8')

field_marker = '''    private var items: List<WidgetClass> = emptyList()\n\n    override fun onCreate() {\n        reload()\n    }\n\n    override fun onDataSetChanged() {\n        reload()\n    }\n'''
field_new = '''    private var items: List<WidgetClass> = emptyList()\n    private var readySignalSent = false\n\n    override fun onCreate() {\n        reload()\n        readySignalSent = false\n    }\n\n    override fun onDataSetChanged() {\n        reload()\n        readySignalSent = false\n    }\n'''
if field_marker not in t:
    raise SystemExit('service factory lifecycle marker missing')
t = t.replace(field_marker, field_new, 1)

bitmap_marker = '''        views.setImageViewBitmap(\n            R.id.widget_slide_image,\n            renderSlide(item),\n        )\n        views.setOnClickFillInIntent(\n'''
bitmap_new = '''        views.setImageViewBitmap(\n            R.id.widget_slide_image,\n            renderSlide(item),\n        )\n        signalReadyOnce()\n        views.setOnClickFillInIntent(\n'''
if bitmap_marker not in t:
    raise SystemExit('service getViewAt bitmap marker missing')
t = t.replace(bitmap_marker, bitmap_new, 1)

render_marker = '''    private fun renderSlide(item: WidgetClass): Bitmap =\n        renderWidgetSlide(context, item, renderWidthDp, renderHeightDp)\n\n}\n'''
render_new = '''    private fun signalReadyOnce() {\n        if (readySignalSent || widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) {\n            return\n        }\n        readySignalSent = true\n        val readyThemeKey = readWidgetTheme(context).key\n        context.sendBroadcast(\n            Intent(context, ScheduleWidgetProvider::class.java).apply {\n                action = ScheduleWidgetProvider.ACTION_COLLECTION_FRAME_READY\n                putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)\n                putExtra(ScheduleWidgetProvider.EXTRA_READY_THEME_KEY, readyThemeKey)\n            },\n        )\n    }\n\n    private fun renderSlide(item: WidgetClass): Bitmap =\n        renderWidgetSlide(context, item, renderWidthDp, renderHeightDp)\n\n}\n'''
if render_marker not in t:
    raise SystemExit('service render marker missing')
t = t.replace(render_marker, render_new, 1)
service.write_text(t, encoding='utf-8')

pubspec = Path('pubspec.yaml')
p = pubspec.read_text(encoding='utf-8')
if 'version: 2.0.8+13' not in p:
    raise SystemExit('expected current version missing')
p = p.replace('version: 2.0.8+13', 'version: 2.0.9+14', 1)
pubspec.write_text(p, encoding='utf-8')
