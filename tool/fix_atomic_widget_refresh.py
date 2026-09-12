from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing marker: {label}")
    return text.replace(old, new, 1)


def find_matching_brace(text: str, open_index: int) -> int:
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    raise RuntimeError('unbalanced braces')


# ---- App action contrast ----------------------------------------------------
app = Path('lib/app/app.dart')
s = app.read_text(encoding='utf-8')
old_helpers = '''Color _panelSecondaryColor(AppThemePalette palette) =>
    Color.lerp(palette.primary, palette.accent, .34) ?? palette.primary;

Color _panelTertiaryColor(AppThemePalette palette) =>
    Color.lerp(palette.primary, palette.accent, .68) ?? palette.primary;

Color _contrastForeground(Color background) =>
    background.computeLuminance() > .52
    ? const Color(0xFF151515)
    : Colors.white;
'''
new_helpers = '''Color _panelSecondaryColor(AppThemePalette palette) => switch (palette.id) {
  AppThemeId.classic => const Color(0xFF6A7CEB),
  AppThemeId.lol => const Color(0xFFC89B3C),
  AppThemeId.valorant => const Color(0xFF56D6C7),
  AppThemeId.minecraft => const Color(0xFF42A5F5),
  AppThemeId.facebook => const Color(0xFF42B72A),
  AppThemeId.shopee => const Color(0xFF0EA5E9),
  AppThemeId.tiktok => const Color(0xFF25F4EE),
  AppThemeId.ben10 => const Color(0xFF00AEEF),
  AppThemeId.youtube => const Color(0xFF3EA6FF),
  AppThemeId.steam => const Color(0xFFA4D007),
};

Color _panelTertiaryColor(AppThemePalette palette) => switch (palette.id) {
  AppThemeId.classic => const Color(0xFF8B5CF6),
  AppThemeId.lol => const Color(0xFF7E72C6),
  AppThemeId.valorant => const Color(0xFFC084FC),
  AppThemeId.minecraft => const Color(0xFFFFCA28),
  AppThemeId.facebook => const Color(0xFFA033FF),
  AppThemeId.shopee => const Color(0xFF8B5CF6),
  AppThemeId.tiktok => const Color(0xFFB06CFF),
  AppThemeId.ben10 => const Color(0xFFC5FF35),
  AppThemeId.youtube => const Color(0xFF8B5CF6),
  AppThemeId.steam => const Color(0xFF66C0F4),
};

Color _contrastForeground(Color background) =>
    background.computeLuminance() > .48
    ? const Color(0xFF101418)
    : Colors.white;
'''
s = replace_once(s, old_helpers, new_helpers, 'panel action palette')
app.write_text(s, encoding='utf-8')


# ---- Widget layout: add full-frame refresh cover ---------------------------
layout = Path('platform/android_widget/app/src/main/res/layout/schedule_widget.xml')
x = layout.read_text(encoding='utf-8')
stack_end = '''        android:clipToPadding="true"
        android:loopViews="true" />

    <TextView
'''
cover_xml = '''        android:clipToPadding="true"
        android:loopViews="true" />

    <!--
      Atomic refresh cover. During collection/theme invalidation Samsung Launcher can
      briefly lay out several StackView children at once. The provider puts a fully
      rendered first card here before invalidating the collection, then hides it only
      after the refreshed stack is stable. This prevents both overlapping text and
      the old peek/edge artifacts without disabling swipe navigation.
    -->
    <ImageView
        android:id="@+id/widget_refresh_cover"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:clickable="false"
        android:contentDescription="@null"
        android:focusable="false"
        android:scaleType="fitXY"
        android:visibility="gone" />

    <TextView
'''
x = replace_once(x, stack_end, cover_xml, 'refresh cover layout')
layout.write_text(x, encoding='utf-8')


# ---- Service: reuse the exact same renderer for the cover ------------------
service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
k = service.read_text(encoding='utf-8')
method_marker = '    private fun renderSlide(item: WidgetClass): Bitmap {'
start = k.index(method_marker)
open_brace = k.index('{', start)
close_brace = find_matching_brace(k, open_brace)
body = k[open_brace + 1:close_brace]
method_replacement = '''    private fun renderSlide(item: WidgetClass): Bitmap =
        renderWidgetSlide(context, item, renderWidthDp, renderHeightDp)
'''
k = k[:start] + method_replacement + k[close_brace + 1:]
insert_marker = '\nprivate data class WidgetTheme('
renderer = '''
private fun renderWidgetSlide(
    context: Context,
    item: WidgetClass,
    renderWidthDp: Int,
    renderHeightDp: Int,
): Bitmap {''' + body + '''
}

internal fun renderWidgetRefreshCover(
    context: Context,
    widgetId: Int,
    renderWidthDp: Int,
    renderHeightDp: Int,
): Bitmap? {
    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null
    return renderWidgetSlide(context, first, renderWidthDp, renderHeightDp)
}
'''
if insert_marker not in k:
    raise RuntimeError('missing widget theme insertion marker')
k = k.replace(insert_marker, '\n' + renderer + insert_marker, 1)
service.write_text(k, encoding='utf-8')


# ---- Provider: atomic cover + delayed reveal -------------------------------
provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
p = provider.read_text(encoding='utf-8')
p = replace_once(p, 'import android.os.Bundle\n', 'import android.os.Bundle\nimport android.os.Handler\nimport android.os.Looper\n', 'handler imports')
p = replace_once(p, 'import android.util.TypedValue\n', 'import android.util.TypedValue\nimport android.view.View\n', 'view import')

p = replace_once(
    p,
    '''        val themeChanged = previousThemeKey != themeKey\n\n        val views = if''',
    '''        val themeChanged = previousThemeKey != themeKey\n        val showRefreshCover = collectionChanged || themeChanged\n\n        val views = if''',
    'cover flag',
)

# Extend every buildWidgetViews call, regardless of indentation/branch.
def inject_cover_arg(match: re.Match[str]) -> str:
    indent = match.group(1)
    return (
        f'{indent}bindCollection = collectionChanged,\n'
        f'{indent}showRefreshCover = showRefreshCover,\n'
    )

p = re.sub(
    r'(?m)^(\s*)bindCollection = collectionChanged,\n',
    inject_cover_arg,
    p,
)

p = replace_once(
    p,
    '''        visualHeightDp: Float,\n        bindCollection: Boolean,\n    ): RemoteViews {''',
    '''        visualHeightDp: Float,\n        bindCollection: Boolean,\n        showRefreshCover: Boolean,\n    ): RemoteViews {''',
    'build views signature',
)

cover_marker = '''        views.setTextColor(R.id.widget_empty, theme.textColor)\n\n        if (bindCollection) {'''
cover_block = '''        views.setTextColor(R.id.widget_empty, theme.textColor)\n\n        if (showRefreshCover) {\n            val cover = renderWidgetRefreshCover(\n                context,\n                widgetId,\n                renderWidthDp,\n                renderHeightDp,\n            )\n            if (cover != null) {\n                views.setImageViewBitmap(R.id.widget_refresh_cover, cover)\n                views.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)\n                views.setDisplayedChild(R.id.widget_list, 0)\n            } else {\n                views.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n            }\n        } else {\n            views.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n        }\n\n        if (bindCollection) {'''
p = replace_once(p, cover_marker, cover_block, 'cover configuration')

p = replace_once(
    p,
    '''            renderStatePrefs.edit()\n                .putString(contentTokenKey(widgetId), contentToken)\n                .putString(themeTokenKey(widgetId), themeKey)\n                .apply()\n        } else if (themeChanged) {''',
    '''            renderStatePrefs.edit()\n                .putString(contentTokenKey(widgetId), contentToken)\n                .putString(themeTokenKey(widgetId), themeKey)\n                .apply()\n            scheduleRefreshCoverHide(context, appWidgetManager, widgetId)\n        } else if (themeChanged) {''',
    'content refresh hide schedule',
)
p = replace_once(
    p,
    '''            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)\n            renderStatePrefs.edit().putString(themeTokenKey(widgetId), themeKey).apply()\n        } else {''',
    '''            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)\n            renderStatePrefs.edit().putString(themeTokenKey(widgetId), themeKey).apply()\n            scheduleRefreshCoverHide(context, appWidgetManager, widgetId)\n        } else {''',
    'theme refresh hide schedule',
)

helper_marker = '''    private data class ThemeColors(\n'''
helper_code = '''    private fun scheduleRefreshCoverHide(\n        context: Context,\n        appWidgetManager: AppWidgetManager,\n        widgetId: Int,\n    ) {\n        Handler(Looper.getMainLooper()).postDelayed({\n            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)\n            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n            appWidgetManager.partiallyUpdateAppWidget(widgetId, reveal)\n        }, REFRESH_COVER_HOLD_MS)\n    }\n\n'''
p = replace_once(p, helper_marker, helper_code + helper_marker, 'cover hide helper')

const_marker = 'private const val CALENDAR_HEIGHT_FRACTION'
if const_marker not in p:
    raise RuntimeError('calendar constant marker missing')
p = p.replace(const_marker, 'private const val REFRESH_COVER_HOLD_MS = 1250L\n        ' + const_marker, 1)
provider.write_text(p, encoding='utf-8')


# ---- Version bump -----------------------------------------------------------
pub = Path('pubspec.yaml')
v = pub.read_text(encoding='utf-8')
v2 = re.sub(r'^version:\s*2\.0\.6\+11\s*$', 'version: 2.0.7+12', v, count=1, flags=re.M)
if v2 == v:
    raise RuntimeError('version marker missing')
pub.write_text(v2, encoding='utf-8')
