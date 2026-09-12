from pathlib import Path

# 1) Stage native widget theme changes in MainActivity; do not touch the widget
# while the Flutter app is still visible. When the activity pauses, start the
# transition after a short delay so Home can show the intact old widget first.
main = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/MainActivity.kt')
s = main.read_text(encoding='utf-8')
old = '''import android.content.Context
import io.flutter.embedding.android.FlutterActivity
'''
new = '''import android.content.Context
import android.os.Handler
import android.os.Looper
import io.flutter.embedding.android.FlutterActivity
'''
if old not in s:
    raise SystemExit('MainActivity import marker missing')
s = s.replace(old, new, 1)

old = '''class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
'''
new = '''class MainActivity : FlutterActivity() {
    private val widgetThemeHandler = Handler(Looper.getMainLooper())
    private val applyPendingWidgetTheme = Runnable { applyPendingWidgetThemeIfNeeded() }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
'''
if old not in s:
    raise SystemExit('MainActivity class marker missing')
s = s.replace(old, new, 1)

old = '''            val theme = call.argument<String>("theme") ?: "classic"
            val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            // Synchronous write guarantees ScheduleWidgetProvider reads this same
            // theme in the immediately-following update call.
            prefs.edit().putString(THEME_KEY, theme).commit()

            val manager = AppWidgetManager.getInstance(this)
            val component = ComponentName(this, ScheduleWidgetProvider::class.java)
            val widgetIds = manager.getAppWidgetIds(component)
            if (widgetIds.isNotEmpty()) {
                ScheduleWidgetProvider().onUpdate(this, manager, widgetIds, prefs)
            }
            result.success(widgetIds.size)
'''
new = '''            val theme = call.argument<String>("theme") ?: "classic"
            val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            val widgetThemePrefs = getSharedPreferences(WIDGET_THEME_PREFS, Context.MODE_PRIVATE)
            if (!widgetThemePrefs.contains(ACTIVE_THEME_KEY)) {
                val currentTheme = flutterPrefs.getString(THEME_KEY, "classic") ?: "classic"
                widgetThemePrefs.edit().putString(ACTIVE_THEME_KEY, currentTheme).commit()
            }

            // Do not update the Home widget while the Flutter app is on screen.
            // Only stage the requested theme. The old widget remains completely
            // untouched until the app pauses and the deliberate transition begins.
            widgetThemePrefs.edit().putString(PENDING_THEME_KEY, theme).commit()

            val manager = AppWidgetManager.getInstance(this)
            val component = ComponentName(this, ScheduleWidgetProvider::class.java)
            result.success(manager.getAppWidgetIds(component).size)
'''
if old not in s:
    raise SystemExit('MainActivity applyTheme body marker missing')
s = s.replace(old, new, 1)

old = '''    companion object {
        private const val WIDGET_THEME_CHANNEL = "better_phenikaa/widget_theme"
        private const val FLUTTER_PREFS = "FlutterSharedPreferences"
        private const val THEME_KEY = "flutter.appTheme"
    }
}
'''
new = '''    override fun onResume() {
        widgetThemeHandler.removeCallbacks(applyPendingWidgetTheme)
        super.onResume()
    }

    override fun onPause() {
        super.onPause()
        widgetThemeHandler.removeCallbacks(applyPendingWidgetTheme)
        widgetThemeHandler.postDelayed(
            applyPendingWidgetTheme,
            WIDGET_TRANSITION_START_DELAY_MS,
        )
    }

    private fun applyPendingWidgetThemeIfNeeded() {
        val widgetThemePrefs = getSharedPreferences(WIDGET_THEME_PREFS, Context.MODE_PRIVATE)
        val pendingTheme = widgetThemePrefs.getString(PENDING_THEME_KEY, null) ?: return
        val activeTheme = widgetThemePrefs.getString(ACTIVE_THEME_KEY, null)
        if (pendingTheme == activeTheme) {
            widgetThemePrefs.edit().remove(PENDING_THEME_KEY).apply()
            return
        }

        val manager = AppWidgetManager.getInstance(this)
        val component = ComponentName(this, ScheduleWidgetProvider::class.java)
        val widgetIds = manager.getAppWidgetIds(component)
        ScheduleWidgetProvider().beginStagedThemeTransition(
            context = this,
            appWidgetManager = manager,
            appWidgetIds = widgetIds,
            targetThemeKey = pendingTheme,
        )
    }

    companion object {
        private const val WIDGET_THEME_CHANNEL = "better_phenikaa/widget_theme"
        private const val FLUTTER_PREFS = "FlutterSharedPreferences"
        private const val THEME_KEY = "flutter.appTheme"
        private const val WIDGET_THEME_PREFS = "better_phenikaa_widget_theme_state"
        private const val ACTIVE_THEME_KEY = "active_theme"
        private const val PENDING_THEME_KEY = "pending_theme"
        private const val WIDGET_TRANSITION_START_DELAY_MS = 140L
    }
}
'''
if old not in s:
    raise SystemExit('MainActivity companion marker missing')
s = s.replace(old, new, 1)
main.write_text(s, encoding='utf-8')

# 2) Provider: maintain old cover first, switch active theme underneath it,
# refresh StackView while hidden, then wipe only after factory reports ready.
provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
s = provider.read_text(encoding='utf-8')

old = '''    override fun onAppWidgetOptionsChanged(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetId: Int,
        newOptions: Bundle,
    ) {
        super.onAppWidgetOptionsChanged(context, appWidgetManager, appWidgetId, newOptions)
        renderWidget(context, appWidgetManager, appWidgetId)
    }

    private fun renderWidget(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
    ) {
'''
new = '''    override fun onAppWidgetOptionsChanged(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetId: Int,
        newOptions: Bundle,
    ) {
        super.onAppWidgetOptionsChanged(context, appWidgetManager, appWidgetId, newOptions)
        renderWidget(context, appWidgetManager, appWidgetId)
    }

    fun beginStagedThemeTransition(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray,
        targetThemeKey: String,
    ) {
        val widgetThemePrefs = context.getSharedPreferences(
            WIDGET_THEME_STATE_PREFS,
            Context.MODE_PRIVATE,
        )
        val oldThemeKey = readThemeColors(context).key
        if (oldThemeKey == targetThemeKey) {
            widgetThemePrefs.edit().remove(PENDING_THEME_KEY).apply()
            return
        }

        val renderStatePrefs = context.getSharedPreferences(
            WIDGET_RENDER_STATE_PREFS,
            Context.MODE_PRIVATE,
        )

        // Phase A: put one opaque old-theme frost panel above the existing widget.
        // The live StackView is still untouched at this point, so no new-theme crack
        // can ever precede the transition.
        appWidgetIds.forEach { widgetId ->
            renderStatePrefs.edit()
                .putString(transitionFromThemeKey(widgetId), oldThemeKey)
                .apply()
            showOldThemeTransitionHold(
                context,
                appWidgetManager,
                widgetId,
                oldThemeKey,
            )
        }

        // Phase B: only after the old-theme cover is installed, switch the widget's
        // private active theme. Flutter's appTheme preference is deliberately not
        // used as the widget's live renderer state anymore.
        widgetThemePrefs.edit()
            .putString(ACTIVE_THEME_KEY, targetThemeKey)
            .remove(PENDING_THEME_KEY)
            .commit()

        // Phase C: rebuild the collection underneath the existing opaque cover.
        appWidgetIds.forEach { widgetId ->
            renderWidget(
                context = context,
                appWidgetManager = appWidgetManager,
                widgetId = widgetId,
                preserveTransitionCover = true,
            )
        }
    }

    private fun renderWidget(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
        preserveTransitionCover: Boolean = false,
    ) {
'''
if old not in s:
    raise SystemExit('Provider insertion marker missing')
s = s.replace(old, new, 1)

s = s.replace(
'''        val showRefreshCover = collectionChanged || themeChanged
''',
'''        val showRefreshCover = !preserveTransitionCover && (collectionChanged || themeChanged)
''',
1,
)

# Add holdExistingCover argument to all build calls.
s = s.replace(
'''                        bindCollection = collectionChanged,
                        showRefreshCover = showRefreshCover,
                    )
''',
'''                        bindCollection = collectionChanged,
                        showRefreshCover = showRefreshCover,
                        holdExistingCover = preserveTransitionCover,
                    )
''',
1,
)
s = s.replace(
'''                    bindCollection = collectionChanged,
                    showRefreshCover = showRefreshCover,
                )
''',
'''                    bindCollection = collectionChanged,
                    showRefreshCover = showRefreshCover,
                    holdExistingCover = preserveTransitionCover,
                )
''',
1,
)
s = s.replace(
'''                bindCollection = collectionChanged,
                showRefreshCover = showRefreshCover,
            )
''',
'''                bindCollection = collectionChanged,
                showRefreshCover = showRefreshCover,
                holdExistingCover = preserveTransitionCover,
            )
''',
1,
)

old = '''        if (collectionChanged) {
            appWidgetManager.updateAppWidget(widgetId, views)
            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
            renderStatePrefs.edit()
                .putString(contentTokenKey(widgetId), contentToken)
                .putString(themeTokenKey(widgetId), themeKey)
                .apply()
        } else if (themeChanged) {
'''
new = '''        if (preserveTransitionCover) {
            // Never replace the complete root while the staged cover is active;
            // a full update would recreate the XML and momentarily drop the cover.
            appWidgetManager.partiallyUpdateAppWidget(widgetId, views)
            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
            renderStatePrefs.edit()
                .putString(contentTokenKey(widgetId), contentToken)
                .putString(themeTokenKey(widgetId), themeKey)
                .apply()
        } else if (collectionChanged) {
            appWidgetManager.updateAppWidget(widgetId, views)
            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
            renderStatePrefs.edit()
                .putString(contentTokenKey(widgetId), contentToken)
                .putString(themeTokenKey(widgetId), themeKey)
                .apply()
        } else if (themeChanged) {
'''
if old not in s:
    raise SystemExit('Provider render branch marker missing')
s = s.replace(old, new, 1)

old = '''        bindCollection: Boolean,
        showRefreshCover: Boolean,
    ): RemoteViews {
'''
new = '''        bindCollection: Boolean,
        showRefreshCover: Boolean,
        holdExistingCover: Boolean = false,
    ): RemoteViews {
'''
if old not in s:
    raise SystemExit('Provider build args marker missing')
s = s.replace(old, new, 1)

old = '''        if (showRefreshCover) {
            val cover = renderWidgetTransitionFrame(
'''
new = '''        if (holdExistingCover) {
            // Omit all operations on widget_refresh_cover so the old-theme hold
            // bitmap installed in Phase A stays exactly as-is. Only hide the live
            // collection while Samsung Launcher rebuilds it underneath.
            views.setViewVisibility(R.id.widget_list, View.INVISIBLE)
        } else if (showRefreshCover) {
            val cover = renderWidgetTransitionFrame(
'''
if old not in s:
    raise SystemExit('Provider cover branch marker missing')
s = s.replace(old, new, 1)

# Insert old-theme hold helper before playRevealTransition.
marker = '''    private fun playRevealTransition(
'''
helper = '''    private fun showOldThemeTransitionHold(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
        oldThemeKey: String,
    ) {
        val options = appWidgetManager.getAppWidgetOptions(widgetId)
        val views = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val exactSizes = exactWidgetSizes(options)
            if (exactSizes.isNotEmpty()) {
                val sizedViews = LinkedHashMap<SizeF, RemoteViews>()
                exactSizes.take(MAX_EXACT_LAYOUTS).forEach { size ->
                    sizedViews[size] = buildOldThemeHoldViews(
                        context,
                        size.width,
                        size.height,
                        oldThemeKey,
                    )
                }
                RemoteViews(sizedViews)
            } else {
                val size = legacyWidgetSize(options)
                buildOldThemeHoldViews(
                    context,
                    size.width,
                    size.height,
                    oldThemeKey,
                )
            }
        } else {
            val size = legacyWidgetSize(options)
            buildOldThemeHoldViews(
                context,
                size.width,
                size.height,
                oldThemeKey,
            )
        }
        appWidgetManager.partiallyUpdateAppWidget(widgetId, views)
    }

    private fun buildOldThemeHoldViews(
        context: Context,
        widthDp: Float,
        heightDp: Float,
        oldThemeKey: String,
    ): RemoteViews {
        val views = RemoteViews(context.packageName, R.layout.schedule_widget)
        val bitmap = renderWidgetThemeHoldFrame(
            context,
            widthDp.roundToInt().coerceAtLeast(1),
            heightDp.roundToInt().coerceAtLeast(1),
            oldThemeKey,
        )
        views.setImageViewBitmap(R.id.widget_refresh_cover, bitmap)
        views.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)
        return views
    }

    private fun playRevealTransition(
'''
if marker not in s:
    raise SystemExit('Provider transition marker missing')
s = s.replace(marker, helper, 1)

# Update play/run to carry from theme and use data-independent wipe frames.
old = '''        val manager = AppWidgetManager.getInstance(context)
        val options = manager.getAppWidgetOptions(widgetId)
        val size = legacyWidgetSize(options)
        val widthDp = size.width.roundToInt().coerceAtLeast(1)
        val heightDp = size.height.roundToInt().coerceAtLeast(1)

        Handler(Looper.getMainLooper()).postDelayed({
'''
new = '''        val manager = AppWidgetManager.getInstance(context)
        val options = manager.getAppWidgetOptions(widgetId)
        val size = legacyWidgetSize(options)
        val widthDp = size.width.roundToInt().coerceAtLeast(1)
        val heightDp = size.height.roundToInt().coerceAtLeast(1)
        val renderStatePrefs = context.getSharedPreferences(
            WIDGET_RENDER_STATE_PREFS,
            Context.MODE_PRIVATE,
        )
        val fromThemeKey = renderStatePrefs.getString(
            transitionFromThemeKey(widgetId),
            readyThemeKey,
        ) ?: readyThemeKey

        Handler(Looper.getMainLooper()).postDelayed({
'''
if old not in s:
    raise SystemExit('Provider transition setup marker missing')
s = s.replace(old, new, 1)

old = '''                readyThemeKey = readyThemeKey,
                widthDp = widthDp,
                heightDp = heightDp,
                frame = 0,
'''
new = '''                readyThemeKey = readyThemeKey,
                fromThemeKey = fromThemeKey,
                widthDp = widthDp,
                heightDp = heightDp,
                frame = 0,
'''
if old not in s:
    raise SystemExit('Provider initial transition call marker missing')
s = s.replace(old, new, 1)

old = '''        readyThemeKey: String,
        widthDp: Int,
        heightDp: Int,
        frame: Int,
'''
new = '''        readyThemeKey: String,
        fromThemeKey: String,
        widthDp: Int,
        heightDp: Int,
        frame: Int,
'''
if old not in s:
    raise SystemExit('Provider runTransitionFrame args marker missing')
s = s.replace(old, new, 1)

old = '''        val bitmap = renderWidgetTransitionFrame(
            context,
            widgetId,
            widthDp,
            heightDp,
            progress,
        )
'''
new = '''        val bitmap = renderWidgetThemeWipeFrame(
            context = context,
            renderWidthDp = widthDp,
            renderHeightDp = heightDp,
            fromThemeKey = fromThemeKey,
            toThemeKey = readyThemeKey,
            progress = progress,
        )
'''
if old not in s:
    raise SystemExit('Provider transition bitmap marker missing')
s = s.replace(old, new, 1)

# Only staged theme wipe produces a guaranteed bitmap, but keep fallback path.
old = '''        if (bitmap == null) {
            finishRevealTransition(context, widgetId, readyThemeKey)
            return
        }

'''
if old in s:
    s = s.replace(old, '', 1)

old = '''                    readyThemeKey = readyThemeKey,
                    widthDp = widthDp,
                    heightDp = heightDp,
                    frame = frame + 1,
'''
new = '''                    readyThemeKey = readyThemeKey,
                    fromThemeKey = fromThemeKey,
                    widthDp = widthDp,
                    heightDp = heightDp,
                    frame = frame + 1,
'''
if old not in s:
    raise SystemExit('Provider recursive transition call marker missing')
s = s.replace(old, new, 1)

# Clear staged-from marker only after real collection is revealed.
old = '''        AppWidgetManager.getInstance(context)
            .partiallyUpdateAppWidget(widgetId, reveal)
    }

    private data class ThemeColors(
'''
new = '''        AppWidgetManager.getInstance(context)
            .partiallyUpdateAppWidget(widgetId, reveal)
        context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .remove(transitionFromThemeKey(widgetId))
            .apply()
    }

    private data class ThemeColors(
'''
if old not in s:
    raise SystemExit('Provider finish marker missing')
s = s.replace(old, new, 1)

# Widget theme renderer uses a private active theme, not Flutter appTheme.
old = '''    private fun readThemeColors(context: Context): ThemeColors {
        val key = context
            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .getString("flutter.appTheme", "classic")
            ?: "classic"
'''
new = '''    private fun readThemeColors(context: Context): ThemeColors {
        val fallbackTheme = context
            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .getString("flutter.appTheme", "classic")
            ?: "classic"
        val key = context
            .getSharedPreferences(WIDGET_THEME_STATE_PREFS, Context.MODE_PRIVATE)
            .getString(ACTIVE_THEME_KEY, null)
            ?: fallbackTheme
'''
if old not in s:
    raise SystemExit('Provider readThemeColors marker missing')
s = s.replace(old, new, 1)

old = '''    private fun themeTokenKey(widgetId: Int): String = "theme_token_$widgetId"
'''
new = '''    private fun themeTokenKey(widgetId: Int): String = "theme_token_$widgetId"

    private fun transitionFromThemeKey(widgetId: Int): String =
        "transition_from_theme_$widgetId"
'''
if old not in s:
    raise SystemExit('Provider token helper marker missing')
s = s.replace(old, new, 1)

s = s.replace(
'''        private const val WIDGET_RENDER_STATE_PREFS = "better_phenikaa_widget_render_state"
''',
'''        private const val WIDGET_RENDER_STATE_PREFS = "better_phenikaa_widget_render_state"
        private const val WIDGET_THEME_STATE_PREFS = "better_phenikaa_widget_theme_state"
        private const val ACTIVE_THEME_KEY = "active_theme"
        private const val PENDING_THEME_KEY = "pending_theme"
''',
1,
)
s = s.replace('private const val TRANSITION_PREPARE_MS = 520L', 'private const val TRANSITION_PREPARE_MS = 120L', 1)
s = s.replace('private const val TRANSITION_FINAL_HOLD_MS = 180L', 'private const val TRANSITION_FINAL_HOLD_MS = 120L', 1)
provider.write_text(s, encoding='utf-8')

# 3) Service: read native active theme, plus data-independent frost/wipe bitmaps.
service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
t = service.read_text(encoding='utf-8')

old = '''private fun readWidgetTheme(context: Context): WidgetTheme {
    val key = context
        .getSharedPreferences(SNAPSHOT_PREFS, Context.MODE_PRIVATE)
        .getString(THEME_KEY, "classic")
        ?: "classic"
    return when (key) {
'''
new = '''private fun readWidgetTheme(context: Context): WidgetTheme {
    val fallbackTheme = context
        .getSharedPreferences(SNAPSHOT_PREFS, Context.MODE_PRIVATE)
        .getString(THEME_KEY, "classic")
        ?: "classic"
    val key = context
        .getSharedPreferences(WIDGET_THEME_STATE_PREFS, Context.MODE_PRIVATE)
        .getString(ACTIVE_THEME_KEY, null)
        ?: fallbackTheme
    return widgetThemeForKey(key)
}

private fun widgetThemeForKey(key: String): WidgetTheme = when (key) {
'''
if old not in t:
    raise SystemExit('Service readWidgetTheme marker missing')
t = t.replace(old, new, 1)

# close changed when-expression: replace first exact tail after theme map.
old = '''        else -> WidgetTheme("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFDDE8FF.toInt())
    }
}
'''
new = '''        else -> WidgetTheme("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFDDE8FF.toInt())
    }
'''
if old not in t:
    raise SystemExit('Service theme map tail marker missing')
t = t.replace(old, new, 1)

# Insert theme-only hold/wipe before WidgetTheme data class.
marker = '''private data class WidgetTheme(
'''
code = '''internal fun renderWidgetThemeHoldFrame(
    context: Context,
    renderWidthDp: Int,
    renderHeightDp: Int,
    themeKey: String,
): Bitmap = renderThemeTransitionPanel(
    context,
    renderWidthDp,
    renderHeightDp,
    widgetThemeForKey(themeKey),
)

internal fun renderWidgetThemeWipeFrame(
    context: Context,
    renderWidthDp: Int,
    renderHeightDp: Int,
    fromThemeKey: String,
    toThemeKey: String,
    progress: Float,
): Bitmap {
    val from = renderThemeTransitionPanel(
        context,
        renderWidthDp,
        renderHeightDp,
        widgetThemeForKey(fromThemeKey),
    )
    val to = renderThemeTransitionPanel(
        context,
        renderWidthDp,
        renderHeightDp,
        widgetThemeForKey(toThemeKey),
    )
    val output = Bitmap.createBitmap(from.width, from.height, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(output)
    val p = progress.coerceIn(0f, 1f)
    canvas.drawBitmap(from, 0f, 0f, null)

    val revealRight = output.width * p
    if (revealRight > 0f) {
        val save = canvas.save()
        canvas.clipRect(0f, 0f, revealRight, output.height.toFloat())
        canvas.drawBitmap(to, 0f, 0f, null)
        canvas.restoreToCount(save)
    }

    if (p > 0f && p < 1f) {
        val glowWidth = (output.width * TRANSITION_EDGE_WIDTH_FRACTION)
            .coerceIn(12f, 54f)
        val left = (revealRight - glowWidth).coerceAtLeast(0f)
        val right = (revealRight + glowWidth).coerceAtMost(output.width.toFloat())
        if (right > left) {
            val glow = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                shader = LinearGradient(
                    left,
                    0f,
                    right,
                    0f,
                    intArrayOf(0x00FFFFFF, 0x66FFFFFF, 0x00FFFFFF),
                    floatArrayOf(0f, 0.5f, 1f),
                    Shader.TileMode.CLAMP,
                )
            }
            canvas.drawRect(left, 0f, right, output.height.toFloat(), glow)
        }
    }
    return output
}

private fun renderThemeTransitionPanel(
    context: Context,
    renderWidthDp: Int,
    renderHeightDp: Int,
    theme: WidgetTheme,
): Bitmap {
    val density = context.resources.displayMetrics.density
    val width = (renderWidthDp.coerceAtLeast(1) * density).toInt().coerceAtLeast(1)
    val height = (renderHeightDp.coerceAtLeast(1) * density).toInt().coerceAtLeast(1)
    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(bitmap)
    val base = Paint(Paint.ANTI_ALIAS_FLAG).apply {
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
    canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), base)

    // A deliberate frost veil masks the live text while the StackView rebuilds.
    // It contains no schedule data, so stale/empty collection states can never
    // leak into the transition frame.
    val veil = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0x22FFFFFF }
    canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), veil)
    val sheen = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        shader = LinearGradient(
            0f,
            0f,
            width.toFloat(),
            height.toFloat(),
            intArrayOf(0x12FFFFFF, 0x30FFFFFF, 0x08FFFFFF),
            floatArrayOf(0f, 0.48f, 1f),
            Shader.TileMode.CLAMP,
        )
    }
    canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), sheen)
    return bitmap
}

private data class WidgetTheme(
'''
if marker not in t:
    raise SystemExit('Service WidgetTheme marker missing')
t = t.replace(marker, code, 1)

# Add state constants near bottom.
old = '''private const val SNAPSHOT_KEY = "flutter.better_phenikaa_snapshot_v1"
private const val THEME_KEY = "flutter.appTheme"
'''
new = '''private const val SNAPSHOT_KEY = "flutter.better_phenikaa_snapshot_v1"
private const val THEME_KEY = "flutter.appTheme"
private const val WIDGET_THEME_STATE_PREFS = "better_phenikaa_widget_theme_state"
private const val ACTIVE_THEME_KEY = "active_theme"
'''
if old not in t:
    raise SystemExit('Service constants marker missing')
t = t.replace(old, new, 1)
service.write_text(t, encoding='utf-8')

# 4) Move transition cover above the empty TextView in z-order. This prevents
# Android's EmptyView from displaying "Không có lịch học" during animation.
xml = Path('platform/android_widget/app/src/main/res/layout/schedule_widget.xml')
x = xml.read_text(encoding='utf-8')
cover = '''    <!--
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

'''
if cover not in x:
    raise SystemExit('XML cover block missing')
x = x.replace(cover, '', 1)
empty_end = '''        android:textColor="#FFFFFFFF"
        android:textSize="14sp"
        android:textStyle="bold" />

'''
if empty_end not in x:
    raise SystemExit('XML empty view end marker missing')
new_cover = '''        android:textColor="#FFFFFFFF"
        android:textSize="14sp"
        android:textStyle="bold" />

    <!--
      Transition cover intentionally comes AFTER widget_empty in z-order. Android
      may briefly expose the EmptyView while a collection is invalidated; keeping
      this opaque cover above it guarantees "Không có lịch học" cannot leak through
      a theme animation.
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

'''
x = x.replace(empty_end, new_cover, 1)
xml.write_text(x, encoding='utf-8')

# 5) Version bump.
pubspec = Path('pubspec.yaml')
p = pubspec.read_text(encoding='utf-8')
if 'version: 2.0.10+15' not in p:
    raise SystemExit('Expected 2.0.10+15 version missing')
p = p.replace('version: 2.0.10+15', 'version: 2.0.11+16', 1)
pubspec.write_text(p, encoding='utf-8')
