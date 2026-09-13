package vn.edu.phenikaa.better_phenikaa_schedule

import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.content.Context
import android.os.Handler
import android.os.Looper
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val transitionHandler = Handler(Looper.getMainLooper())
    private var pendingThemeTransition: PendingThemeTransition? = null
    private var scheduledThemeTransition: Runnable? = null

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
            val oldTheme = pendingThemeTransition?.oldThemeKey
                ?: prefs.getString(THEME_KEY, "classic")
                ?: "classic"

            val manager = AppWidgetManager.getInstance(this)
            val component = ComponentName(this, ScheduleWidgetProvider::class.java)
            val widgetIds = manager.getAppWidgetIds(component)
            cancelScheduledThemeTransition()
            if (oldTheme == theme) {
                pendingThemeTransition = null
            } else if (widgetIds.isNotEmpty()) {
                // The theme picker covers Home. Starting here makes every animation
                // frame run invisibly behind this Activity. Queue only the final
                // selection and start it after onStop, when Home is visible again.
                pendingThemeTransition = PendingThemeTransition(oldTheme, theme)
            } else {
                pendingThemeTransition = null
                prefs.edit().putString(THEME_KEY, theme).commit()
            }
            result.success(widgetIds.size)
        }
    }

    override fun onStart() {
        super.onStart()
        // onStop also occurs for a brief trip through Recents. If the app becomes
        // visible again before the grace period, keep the transition pending for
        // the next real departure instead of playing it behind another screen.
        cancelScheduledThemeTransition()
    }

    override fun onStop() {
        super.onStop()
        val pending = pendingThemeTransition ?: return
        cancelScheduledThemeTransition()
        val task = Runnable {
            if (pendingThemeTransition != pending) return@Runnable
            scheduledThemeTransition = null
            pendingThemeTransition = null

            val manager = AppWidgetManager.getInstance(applicationContext)
            val component = ComponentName(
                applicationContext,
                ScheduleWidgetProvider::class.java,
            )
            val widgetIds = manager.getAppWidgetIds(component)
            if (widgetIds.isEmpty()) {
                applicationContext
                    .getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
                    .edit()
                    .putString(THEME_KEY, pending.targetThemeKey)
                    .commit()
                return@Runnable
            }
            ScheduleWidgetProvider().beginThemeTransition(
                applicationContext,
                manager,
                widgetIds,
                pending.oldThemeKey,
                pending.targetThemeKey,
            )
        }
        scheduledThemeTransition = task
        transitionHandler.postDelayed(task, HOME_REVEAL_GRACE_MS)
    }

    private fun cancelScheduledThemeTransition() {
        scheduledThemeTransition?.let(transitionHandler::removeCallbacks)
        scheduledThemeTransition = null
    }

    private data class PendingThemeTransition(
        val oldThemeKey: String,
        val targetThemeKey: String,
    )

    companion object {
        private const val WIDGET_THEME_CHANNEL = "better_phenikaa/widget_theme"
        private const val FLUTTER_PREFS = "FlutterSharedPreferences"
        private const val THEME_KEY = "flutter.appTheme"
        private const val HOME_REVEAL_GRACE_MS = 420L
    }
}
