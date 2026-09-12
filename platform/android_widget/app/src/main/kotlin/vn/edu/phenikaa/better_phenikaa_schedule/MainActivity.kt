package vn.edu.phenikaa.better_phenikaa_schedule

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
            val oldTheme = prefs.getString(THEME_KEY, "classic") ?: "classic"

            val manager = AppWidgetManager.getInstance(this)
            val component = ComponentName(this, ScheduleWidgetProvider::class.java)
            val widgetIds = manager.getAppWidgetIds(component)
            if (widgetIds.isNotEmpty() && oldTheme != theme) {
                // The provider owns the complete transition. It deliberately leaves
                // THEME_KEY unchanged while the old widget is animating, then commits
                // the target theme only after the last transition frame.
                ScheduleWidgetProvider().beginThemeTransition(
                    this,
                    manager,
                    widgetIds,
                    oldTheme,
                    theme,
                )
            } else if (oldTheme != theme) {
                prefs.edit().putString(THEME_KEY, theme).commit()
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
