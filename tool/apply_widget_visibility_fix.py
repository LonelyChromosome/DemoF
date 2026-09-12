from pathlib import Path

provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
s = provider.read_text(encoding='utf-8')

old = '''            if (cover != null) {
                views.setImageViewBitmap(R.id.widget_refresh_cover, cover)
                views.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)
                views.setDisplayedChild(R.id.widget_list, 0)
            } else {
                views.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
            }
        } else {
            views.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
        }'''
new = '''            if (cover != null) {
                views.setImageViewBitmap(R.id.widget_refresh_cover, cover)
                views.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)
                // Keep StackView laid out and loading, but never let Samsung Launcher
                // expose its intermediate multi-child composition during invalidation.
                views.setViewVisibility(R.id.widget_list, View.INVISIBLE)
            } else {
                views.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
                views.setViewVisibility(R.id.widget_list, View.VISIBLE)
            }
        } else {
            views.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
            views.setViewVisibility(R.id.widget_list, View.VISIBLE)
        }'''
if old not in s:
    raise SystemExit('refresh cover block not found')
s = s.replace(old, new, 1)

old = '''            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)
            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
            appWidgetManager.partiallyUpdateAppWidget(widgetId, reveal)'''
new = '''            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)
            reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)
            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
            appWidgetManager.partiallyUpdateAppWidget(widgetId, reveal)'''
if old not in s:
    raise SystemExit('reveal block not found')
s = s.replace(old, new, 1)

s = s.replace(
    'private const val REFRESH_COVER_HOLD_MS = 1250L',
    'private const val REFRESH_COVER_HOLD_MS = 1600L',
    1,
)
provider.write_text(s, encoding='utf-8')

pubspec = Path('pubspec.yaml')
p = pubspec.read_text(encoding='utf-8')
p = p.replace('version: 2.0.7+12', 'version: 2.0.8+13', 1)
pubspec.write_text(p, encoding='utf-8')

Path(__file__).unlink()
