from pathlib import Path
import re

# Flutter: notify native widget immediately at the exact theme tap.
p = Path('lib/theme/app_theme.dart')
s = p.read_text(encoding='utf-8')
if "package:flutter/services.dart" not in s:
    s = s.replace(
        "import 'package:flutter/material.dart';\n",
        "import 'package:flutter/material.dart';\nimport 'package:flutter/services.dart';\n",
        1,
    )
old = """  static const _preferenceKey = 'better_phenikaa_theme_v2';
  static const _widgetPreferenceKey = 'appTheme';
"""
new = """  static const _preferenceKey = 'better_phenikaa_theme_v2';
  static const _widgetPreferenceKey = 'appTheme';
  static const MethodChannel _widgetThemeChannel = MethodChannel(
    'better_phenikaa/widget_theme',
  );
"""
if old not in s and '_widgetThemeChannel' not in s:
    raise SystemExit('theme controller constants marker missing')
if '_widgetThemeChannel' not in s:
    s = s.replace(old, new, 1)

old_select = """  Future<void> select(AppThemeId value) async {
    if (_theme == value) return;
    _theme = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await Future.wait<bool>(<Future<bool>>[
      prefs.setString(_preferenceKey, value.storageKey),
      prefs.setString(_widgetPreferenceKey, value.storageKey),
    ]);
    await _syncWidgetTheme();
  }

  Future<void> _syncWidgetTheme() async {
"""
new_select = """  Future<void> select(AppThemeId value) async {
    if (_theme == value) return;
    _theme = value;
    notifyListeners();

    // Start native rendering at the exact tap. The launcher gets the update while
    // the user is still inside the picker instead of waiting for a plugin round-trip.
    final nativeUpdate = _applyWidgetThemeImmediately(value.storageKey);
    final prefs = await SharedPreferences.getInstance();
    await Future.wait<bool>(<Future<bool>>[
      prefs.setString(_preferenceKey, value.storageKey),
      prefs.setString(_widgetPreferenceKey, value.storageKey),
    ]);
    final nativeApplied = await nativeUpdate;
    if (!nativeApplied) {
      await _syncWidgetTheme();
    }
  }

  Future<bool> _applyWidgetThemeImmediately(String themeKey) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return false;
    try {
      await _widgetThemeChannel.invokeMethod<int>(
        'applyTheme',
        <String, Object>{'theme': themeKey},
      );
      return true;
    } on MissingPluginException {
      return false;
    } on PlatformException {
      return false;
    }
  }

  Future<void> _syncWidgetTheme() async {
"""
if old_select not in s:
    raise SystemExit('select method marker missing')
s = s.replace(old_select, new_select, 1)
p.write_text(s, encoding='utf-8')

# Native bridge: synchronously write the widget preference and dispatch the widget
# update before returning to Flutter.
main = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/MainActivity.kt')
main.parent.mkdir(parents=True, exist_ok=True)
main.write_text('''package vn.edu.phenikaa.better_phenikaa_schedule

import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.content.Context
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            WIDGET_THEME_CHANNEL,
        ).setMethodCallHandler { call, result ->
            if (call.method != "applyTheme") {
                result.notImplemented()
                return@setMethodCallHandler
            }

            val theme = call.argument<String>("theme") ?: "classic"
            val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            prefs.edit().putString(THEME_KEY, theme).commit()

            val manager = AppWidgetManager.getInstance(this)
            val component = ComponentName(this, ScheduleWidgetProvider::class.java)
            val widgetIds = manager.getAppWidgetIds(component)
            if (widgetIds.isNotEmpty()) {
                ScheduleWidgetProvider().onUpdate(this, manager, widgetIds, prefs)
            }
            result.success(widgetIds.size)
        }
    }

    companion object {
        private const val WIDGET_THEME_CHANNEL = "better_phenikaa/widget_theme"
        private const val FLUTTER_PREFS = "FlutterSharedPreferences"
        private const val THEME_KEY = "flutter.appTheme"
    }
}
''', encoding='utf-8')

# StackView items become transparent: there is now exactly one owner of the large
# theme color surface (widget_theme_background in the provider).
service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
t = service.read_text(encoding='utf-8')
t = t.replace('import android.graphics.LinearGradient\n', '')
t = t.replace('import android.graphics.Shader\n', '')
background = """        val theme = readWidgetTheme(context)
        val backgroundPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            shader = LinearGradient(
                0f,
                0f,
                widthPx,
                0f,
                theme.startColor,
                theme.endColor,
                Shader.TileMode.CLAMP,
            )
        }
        canvas.drawRect(0f, 0f, widthPx, heightPx, backgroundPaint)

"""
if background not in t:
    raise SystemExit('widget item background marker missing')
t = t.replace(background, '        val theme = readWidgetTheme(context)\n\n', 1)
service.write_text(t, encoding='utf-8')

# Hide the legacy colored peek mask; it can otherwise preserve one stale theme
# rectangle while Samsung Launcher is updating collection children.
layout = Path('platform/android_widget/app/src/main/res/layout/schedule_widget.xml')
x = layout.read_text(encoding='utf-8')
marker = '        android:id="@+id/widget_stack_peek_mask"\n'
if marker not in x:
    raise SystemExit('peek mask marker missing')
segment = x[x.index(marker):x.index(marker) + 400]
if 'android:visibility="gone"' not in segment:
    x = x.replace(marker, marker + '        android:visibility="gone"\n', 1)
layout.write_text(x, encoding='utf-8')

# Stop manipulating the hidden mask in RemoteViews.
provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
q = provider.read_text(encoding='utf-8')
q = re.sub(
    r'''\n            views\.setViewLayoutWidth\(\n                R\.id\.widget_stack_peek_mask,\n                widthDp \* STACK_MASK_WIDTH_FRACTION,\n                TypedValue\.COMPLEX_UNIT_DIP,\n            \)\n            views\.setViewLayoutHeight\(\n                R\.id\.widget_stack_peek_mask,\n                heightDp \* STACK_MASK_HEIGHT_FRACTION,\n                TypedValue\.COMPLEX_UNIT_DIP,\n            \)''',
    '',
    q,
    count=1,
)
q = q.replace('        views.setInt(R.id.widget_stack_peek_mask, "setBackgroundColor", theme.endColor)\n', '')
q = q.replace('        private const val STACK_MASK_WIDTH_FRACTION = 0.11f\n', '')
q = q.replace('        private const val STACK_MASK_HEIGHT_FRACTION = 0.40f\n', '')
provider.write_text(q, encoding='utf-8')

pub = Path('pubspec.yaml')
u = pub.read_text(encoding='utf-8')
u = re.sub(r'^version:.*$', 'version: 2.0.5+10', u, count=1, flags=re.M)
pub.write_text(u, encoding='utf-8')

# Remove this one-shot patch from the final source tree.
Path(__file__).unlink(missing_ok=True)
