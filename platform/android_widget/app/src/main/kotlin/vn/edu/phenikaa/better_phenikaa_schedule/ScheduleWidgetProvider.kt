package vn.edu.phenikaa.better_phenikaa_schedule

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Shader
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.SizeF
import android.util.TypedValue
import android.view.View
import android.widget.RemoteViews
import es.antonborri.home_widget.HomeWidgetProvider
import java.util.Locale
import kotlin.math.min
import kotlin.math.roundToInt

class ScheduleWidgetProvider : HomeWidgetProvider() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == ACTION_COLLECTION_FRAME_READY) {
            val widgetId = intent.getIntExtra(
                AppWidgetManager.EXTRA_APPWIDGET_ID,
                AppWidgetManager.INVALID_APPWIDGET_ID,
            )
            val readyThemeKey = intent.getStringExtra(EXTRA_READY_THEME_KEY)
            if (
                widgetId != AppWidgetManager.INVALID_APPWIDGET_ID &&
                readyThemeKey != null
            ) {
                onTargetCollectionReady(context, widgetId, readyThemeKey)
            }
            return
        }
        super.onReceive(context, intent)
    }

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray,
        widgetData: SharedPreferences,
    ) {
        appWidgetIds.forEach { widgetId ->
            renderWidget(context, appWidgetManager, widgetId)
        }
    }

    fun beginThemeTransition(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetIds: IntArray,
        oldThemeKey: String,
        targetThemeKey: String,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        widgetIds.forEach { widgetId ->
            clearWidgetThemeTransitionFrameCache(widgetId)
            // A widget can still be finishing an earlier switch when the user taps
            // another theme. Its own rendered theme is more accurate than the single
            // global preference in that case.
            val displayedThemeKey = state
                .getString(themeTokenKey(widgetId), null)
                ?: oldThemeKey
            state.edit()
                .putString(transitionFromKey(widgetId), displayedThemeKey)
                .putString(transitionTargetKey(widgetId), targetThemeKey)
                .putLong(transitionStartedAtKey(widgetId), System.currentTimeMillis())
                .remove(transitionReadyKey(widgetId))
                .apply()
            runVisibleThemeTransitionFrame(
                context = context,
                appWidgetManager = appWidgetManager,
                widgetId = widgetId,
                fromThemeKey = displayedThemeKey,
                targetThemeKey = targetThemeKey,
                frame = 0,
                startedAtUptimeMs = 0L,
            )
        }
    }

    override fun onAppWidgetOptionsChanged(
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
        val options = appWidgetManager.getAppWidgetOptions(widgetId)
        val renderStatePrefs = context.getSharedPreferences(
            WIDGET_RENDER_STATE_PREFS,
            Context.MODE_PRIVATE,
        )
        // Data/theme broadcasts can arrive while a theme animation is active. The
        // transition consumes the newest snapshot when it refreshes the target
        // collection, so a normal render here would only expose an intermediate
        // frame and reintroduce the old overlap/peek defects.
        if (renderStatePrefs.contains(transitionTargetKey(widgetId))) {
            val startedAt = renderStatePrefs.getLong(transitionStartedAtKey(widgetId), 0L)
            val ageMs = System.currentTimeMillis() - startedAt
            if (startedAt > 0L && ageMs in 0L..TRANSITION_STALE_AFTER_MS) {
                return
            }
            // A process death can cancel Handler callbacks halfway through a switch.
            // Clear only that abandoned transition and let this update restore the
            // theme already committed in SharedPreferences.
            renderStatePrefs.edit()
                .remove(transitionFromKey(widgetId))
                .remove(transitionTargetKey(widgetId))
                .remove(transitionStartedAtKey(widgetId))
                .remove(transitionReadyKey(widgetId))
                .remove(transitionDisplayIndexKey(widgetId))
                .apply()
            clearWidgetThemeTransitionFrameCache(widgetId)
        }
        val contentToken = collectionContentToken(context, widgetId, options)
        val previousToken = renderStatePrefs.getString(contentTokenKey(widgetId), null)
        val collectionChanged = previousToken != contentToken
        val themeKey = readThemeColors(context).key
        val previousThemeKey = renderStatePrefs.getString(themeTokenKey(widgetId), null)
        val themeChanged = previousThemeKey != themeKey
        val showRefreshCover = collectionChanged || themeChanged

        val views = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val exactSizes = exactWidgetSizes(options)
            if (exactSizes.isNotEmpty()) {
                val sizedViews = LinkedHashMap<SizeF, RemoteViews>()
                exactSizes.take(MAX_EXACT_LAYOUTS).forEach { size ->
                    sizedViews[size] = buildWidgetViews(
                        context = context,
                        widgetId = widgetId,
                        visualWidthDp = size.width,
                        visualHeightDp = size.height,
                        bindCollection = collectionChanged,
                        showRefreshCover = showRefreshCover,
                        preferRealClassCover = themeChanged,
                    )
                }
                RemoteViews(sizedViews)
            } else {
                val fallback = legacyWidgetSize(options)
                buildWidgetViews(
                    context = context,
                    widgetId = widgetId,
                    visualWidthDp = fallback.width,
                    visualHeightDp = fallback.height,
                    bindCollection = collectionChanged,
                    showRefreshCover = showRefreshCover,
                    preferRealClassCover = themeChanged,
                )
            }
        } else {
            val fallback = legacyWidgetSize(options)
            buildWidgetViews(
                context = context,
                widgetId = widgetId,
                visualWidthDp = fallback.width,
                visualHeightDp = fallback.height,
                bindCollection = collectionChanged,
                showRefreshCover = showRefreshCover,
                preferRealClassCover = themeChanged,
            )
        }

        if (collectionChanged) {
            appWidgetManager.updateAppWidget(widgetId, views)
            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
            renderStatePrefs.edit()
                .putString(contentTokenKey(widgetId), contentToken)
                .putString(themeTokenKey(widgetId), themeKey)
                .apply()
            scheduleNormalRefreshCoverHide(context, appWidgetManager, widgetId)
        } else if (themeChanged) {
            // Keep the adapter identity stable. Repaint its existing children in place;
            // their opaque backgrounds prevent any neighbouring item from showing
            // through during the refresh.
            appWidgetManager.partiallyUpdateAppWidget(widgetId, views)
            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
            renderStatePrefs.edit().putString(themeTokenKey(widgetId), themeKey).apply()
            scheduleNormalRefreshCoverHide(context, appWidgetManager, widgetId)
        } else {
            appWidgetManager.partiallyUpdateAppWidget(widgetId, views)
        }
    }

    private fun buildWidgetViews(
        context: Context,
        widgetId: Int,
        visualWidthDp: Float,
        visualHeightDp: Float,
        bindCollection: Boolean,
        showRefreshCover: Boolean,
        preferRealClassCover: Boolean,
    ): RemoteViews {
        val widthDp = visualWidthDp.coerceAtLeast(1f)
        val heightDp = visualHeightDp.coerceAtLeast(1f)
        val renderWidthDp = widthDp.roundToInt().coerceAtLeast(1)
        val renderHeightDp = heightDp.roundToInt().coerceAtLeast(1)
        val views = RemoteViews(context.packageName, R.layout.schedule_widget)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            views.setViewLayoutWidth(
                R.id.widget_list,
                widthDp,
                TypedValue.COMPLEX_UNIT_DIP,
            )
            views.setViewLayoutHeight(
                R.id.widget_list,
                heightDp,
                TypedValue.COMPLEX_UNIT_DIP,
            )

            val calendarSizeDp = min(
                heightDp * CALENDAR_HEIGHT_FRACTION,
                widthDp * CALENDAR_WIDTH_FRACTION,
            ).coerceAtLeast(1f)
            views.setViewLayoutWidth(
                R.id.widget_calendar,
                calendarSizeDp,
                TypedValue.COMPLEX_UNIT_DIP,
            )
            views.setViewLayoutHeight(
                R.id.widget_calendar,
                calendarSizeDp,
                TypedValue.COMPLEX_UNIT_DIP,
            )
            val calendarPaddingPx = (
                calendarSizeDp *
                    context.resources.displayMetrics.density *
                    CALENDAR_PADDING_FRACTION
            ).roundToInt()
            views.setViewPadding(
                R.id.widget_calendar,
                calendarPaddingPx,
                calendarPaddingPx,
                calendarPaddingPx,
                calendarPaddingPx,
            )
        }

        val theme = readThemeColors(context)
        views.setImageViewBitmap(
            R.id.widget_theme_background,
            renderThemeBackground(context, renderWidthDp, renderHeightDp, theme),
        )
        views.setInt(R.id.widget_calendar, "setColorFilter", theme.iconColor)
        views.setTextColor(R.id.widget_empty, theme.textColor)
        views.setImageViewBitmap(
            R.id.widget_stack_peek_mask,
            renderStackPeekMask(context, renderWidthDp, renderHeightDp, theme),
        )
        views.setViewVisibility(R.id.widget_stack_peek_mask, View.VISIBLE)

        if (showRefreshCover) {
            val cover = if (preferRealClassCover) {
                renderWidgetTransitionCover(
                    context,
                    widgetId,
                    renderWidthDp,
                    renderHeightDp,
                    theme.key,
                )
            } else {
                renderWidgetRefreshCover(
                    context,
                    widgetId,
                    renderWidthDp,
                    renderHeightDp,
                )
            }
            if (cover != null) {
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
        }

        if (bindCollection) {
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
                data = Uri.parse("better-phenikaa://widget/$widgetId/$sizeToken")
            }
            views.setRemoteAdapter(R.id.widget_list, serviceIntent)
            views.setEmptyView(R.id.widget_list, R.id.widget_empty)

            context.packageManager.getLaunchIntentForPackage(context.packageName)?.let { launchIntent ->
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                val openApp = PendingIntent.getActivity(
                    context,
                    widgetId,
                    launchIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE,
                )
                views.setPendingIntentTemplate(R.id.widget_list, openApp)
                views.setOnClickPendingIntent(R.id.widget_empty, openApp)
            }
        }

        val chooseDateIntent = Intent(context, WidgetDatePickerActivity::class.java).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
            data = Uri.parse("better-phenikaa://widget/$widgetId/date-picker")
        }
        val chooseDate = PendingIntent.getActivity(
            context,
            DATE_PICKER_REQUEST_CODE_BASE + widgetId,
            chooseDateIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        views.setOnClickPendingIntent(R.id.widget_calendar, chooseDate)

        if (bindCollection) {
            val selectionPrefs = context.getSharedPreferences(
                WIDGET_SELECTION_PREFS,
                Context.MODE_PRIVATE,
            )
            if (selectionPrefs.getBoolean(resetChildKey(widgetId), false)) {
                views.setDisplayedChild(R.id.widget_list, 0)
                selectionPrefs.edit().remove(resetChildKey(widgetId)).apply()
            }
        }
        return views
    }

    private fun scheduleNormalRefreshCoverHide(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
    ) {
        Handler(Looper.getMainLooper()).postDelayed({
            val state = context.getSharedPreferences(
                WIDGET_RENDER_STATE_PREFS,
                Context.MODE_PRIVATE,
            )
            if (state.contains(transitionTargetKey(widgetId))) {
                return@postDelayed
            }
            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)
            reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)
            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
            appWidgetManager.partiallyUpdateAppWidget(widgetId, reveal)
        }, NORMAL_REFRESH_COVER_HOLD_MS)
    }

    private fun runVisibleThemeTransitionFrame(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
        fromThemeKey: String,
        targetThemeKey: String,
        frame: Int,
        startedAtUptimeMs: Long,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        if (state.getString(transitionTargetKey(widgetId), null) != targetThemeKey) {
            return
        }

        val lastFrame = (TRANSITION_FRAME_COUNT - 1).coerceAtLeast(0)
        val elapsedFrame = if (startedAtUptimeMs > 0L) {
            (
                (SystemClock.uptimeMillis() - startedAtUptimeMs).coerceAtLeast(0L) /
                    TRANSITION_FRAME_DELAY_MS
            ).toInt()
        } else {
            frame
        }
        // Stay on a fixed 33 ms clock. If rendering or the launcher stalls, skip
        // an overdue intermediate frame instead of extending the 0.5 s animation.
        val visibleFrame = maxOf(frame, elapsedFrame).coerceAtMost(lastFrame)
        val denominator = lastFrame.coerceAtLeast(1)
        val progress = visibleFrame.toFloat() / denominator.toFloat()
        val frameViews = buildSizeAwareViews(
            context,
            appWidgetManager,
            widgetId,
        ) { widthDp, heightDp ->
            val transitionCard = renderWidgetThemeTransitionFrame(
                context = context,
                widgetId = widgetId,
                renderWidthDp = widthDp,
                renderHeightDp = heightDp,
                progress = progress,
                fromThemeKey = fromThemeKey,
                toThemeKey = targetThemeKey,
            )
            RemoteViews(context.packageName, R.layout.schedule_widget).apply {
                if (transitionCard == null) {
                    setViewVisibility(R.id.widget_refresh_cover, View.GONE)
                    setViewVisibility(R.id.widget_list, View.VISIBLE)
                } else {
                    // The opaque frame contains the same real class in both themes.
                    // It makes the wipe visible without exposing StackView's cached
                    // empty row or its neighbouring-card peek during invalidation.
                    setImageViewBitmap(R.id.widget_refresh_cover, transitionCard)
                    setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)
                    setViewVisibility(R.id.widget_list, View.INVISIBLE)
                }
            }
        }
        appWidgetManager.partiallyUpdateAppWidget(widgetId, frameViews)

        // Frame zero creates and caches the two complete theme cards. Start the
        // animation clock only after that one-time preparation has finished.
        val clockOrigin = if (startedAtUptimeMs > 0L) {
            startedAtUptimeMs
        } else {
            SystemClock.uptimeMillis()
        }
        if (visibleFrame < lastFrame) {
            val nextFrame = visibleFrame + 1
            val nextFrameAtUptimeMs =
                clockOrigin + nextFrame.toLong() * TRANSITION_FRAME_DELAY_MS
            Handler(Looper.getMainLooper()).postAtTime({
                runVisibleThemeTransitionFrame(
                    context = context,
                    appWidgetManager = appWidgetManager,
                    widgetId = widgetId,
                    fromThemeKey = fromThemeKey,
                    targetThemeKey = targetThemeKey,
                    frame = nextFrame,
                    startedAtUptimeMs = clockOrigin,
                )
            }, nextFrameAtUptimeMs)
        } else {
            Handler(Looper.getMainLooper()).postDelayed({
                commitTargetThemeAndRefresh(
                    context,
                    appWidgetManager,
                    widgetId,
                    targetThemeKey,
                )
            }, TRANSITION_FINAL_HOLD_MS)
        }
    }

    private fun commitTargetThemeAndRefresh(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
        targetThemeKey: String,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        if (state.getString(transitionTargetKey(widgetId), null) != targetThemeKey) {
            return
        }
        clearWidgetThemeTransitionFrameCache(widgetId)

        // This is intentionally the first persisted write of the target theme.
        // Before this point an opaque transition card kept the same real subject
        // visible while the wipe moved from the old palette to the new palette.
        context.getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(THEME_KEY, targetThemeKey)
            .commit()

        val targetIndex = widgetTransitionDisplayIndex(context, widgetId)
        state.edit()
            .putString(themeTokenKey(widgetId), targetThemeKey)
            .putInt(transitionDisplayIndexKey(widgetId), targetIndex)
            .apply()

        val targetViews = buildSizeAwareViews(
            context,
            appWidgetManager,
            widgetId,
        ) { widthDp, heightDp ->
            val targetTheme = themeColorsForKey(targetThemeKey)
            val cover = renderWidgetTransitionCover(
                context,
                widgetId,
                widthDp,
                heightDp,
                targetThemeKey,
            )
            RemoteViews(context.packageName, R.layout.schedule_widget).apply {
                setImageViewBitmap(
                    R.id.widget_theme_background,
                    renderThemeBackground(context, widthDp, heightDp, targetTheme),
                )
                setInt(R.id.widget_calendar, "setColorFilter", targetTheme.iconColor)
                setTextColor(R.id.widget_empty, targetTheme.textColor)
                setImageViewBitmap(
                    R.id.widget_stack_peek_mask,
                    renderStackPeekMask(context, widthDp, heightDp, targetTheme),
                )
                setViewVisibility(R.id.widget_stack_peek_mask, View.VISIBLE)
                if (cover == null) {
                    setViewVisibility(R.id.widget_refresh_cover, View.GONE)
                    setViewVisibility(R.id.widget_list, View.VISIBLE)
                } else {
                    // A real class is preferred over the synthetic empty-day row.
                    // Keep the collection laid out behind this opaque card so every
                    // launcher is able to request and prepare its target-theme row.
                    setImageViewBitmap(R.id.widget_refresh_cover, cover)
                    setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)
                    setViewVisibility(R.id.widget_list, View.VISIBLE)
                }
            }
        }
        appWidgetManager.partiallyUpdateAppWidget(widgetId, targetViews)
        appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)

        // Some launchers do not request a collection row while the widget is off
        // screen. Never leave the opaque cover stuck indefinitely in that case.
        Handler(Looper.getMainLooper()).postDelayed({
            finishThemeTransition(context, widgetId, targetThemeKey)
        }, TARGET_COLLECTION_FALLBACK_MS)
    }

    private fun onTargetCollectionReady(
        context: Context,
        widgetId: Int,
        readyThemeKey: String,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        if (
            state.getString(transitionTargetKey(widgetId), null) != readyThemeKey ||
            readThemeColors(context).key != readyThemeKey ||
            state.getString(transitionReadyKey(widgetId), null) == readyThemeKey
        ) {
            return
        }
        state.edit().putString(transitionReadyKey(widgetId), readyThemeKey).apply()
        Handler(Looper.getMainLooper()).postDelayed({
            finishThemeTransition(context, widgetId, readyThemeKey)
        }, TARGET_COLLECTION_SETTLE_MS)
    }

    private fun finishThemeTransition(
        context: Context,
        widgetId: Int,
        targetThemeKey: String,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        if (
            state.getString(transitionTargetKey(widgetId), null) != targetThemeKey ||
            readThemeColors(context).key != targetThemeKey
        ) {
            return
        }
        val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)
        reveal.setDisplayedChild(
            R.id.widget_list,
            state.getInt(transitionDisplayIndexKey(widgetId), 0).coerceAtLeast(0),
        )
        reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)
        reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)
        AppWidgetManager.getInstance(context)
            .partiallyUpdateAppWidget(widgetId, reveal)
        state.edit()
            .remove(transitionFromKey(widgetId))
            .remove(transitionTargetKey(widgetId))
            .remove(transitionStartedAtKey(widgetId))
            .remove(transitionReadyKey(widgetId))
            .remove(transitionDisplayIndexKey(widgetId))
            .apply()
        clearWidgetThemeTransitionFrameCache(widgetId)
    }

    private fun buildSizeAwareViews(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetId: Int,
        build: (widthDp: Int, heightDp: Int) -> RemoteViews,
    ): RemoteViews {
        val options = appWidgetManager.getAppWidgetOptions(widgetId)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val exactSizes = exactWidgetSizes(options)
            if (exactSizes.isNotEmpty()) {
                val sizedViews = LinkedHashMap<SizeF, RemoteViews>()
                exactSizes.take(MAX_EXACT_LAYOUTS).forEach { size ->
                    sizedViews[size] = build(
                        size.width.roundToInt().coerceAtLeast(1),
                        size.height.roundToInt().coerceAtLeast(1),
                    )
                }
                return RemoteViews(sizedViews)
            }
        }
        val fallback = legacyWidgetSize(options)
        return build(
            fallback.width.roundToInt().coerceAtLeast(1),
            fallback.height.roundToInt().coerceAtLeast(1),
        )
    }

    private data class ThemeColors(
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
        return themeColorsForKey(key)
    }

    private fun themeColorsForKey(key: String): ThemeColors = when (key) {
            "lol" -> ThemeColors(key, 0xFF06131A.toInt(), 0xFF0B343A.toInt(), 0xFFF0E6D2.toInt(), 0xFFF0E6D2.toInt())
            "valorant" -> ThemeColors(key, 0xFF0F1923.toInt(), 0xFF24313B.toInt(), 0xFFECE8E1.toInt(), 0xFFECE8E1.toInt())
            "minecraft" -> ThemeColors(key, 0xFF3A2B20.toInt(), 0xFF6B4A2F.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "facebook" -> ThemeColors(key, 0xFF1877F2.toInt(), 0xFF0866FF.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "shopee" -> ThemeColors(key, 0xFFEE4D2D.toInt(), 0xFFFF6A3D.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "tiktok" -> ThemeColors(key, 0xFF111111.toInt(), 0xFF2A1520.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "ben10" -> ThemeColors(key, 0xFF101510.toInt(), 0xFF1D5F22.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "youtube" -> ThemeColors(key, 0xFF181818.toInt(), 0xFF2B0E14.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
            "steam" -> ThemeColors(key, 0xFF171D25.toInt(), 0xFF1B3D55.toInt(), 0xFFD6E9F8.toInt(), 0xFFD6E9F8.toInt())
            else -> ThemeColors("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())
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

    private fun renderStackPeekMask(
        context: Context,
        widthDp: Int,
        heightDp: Int,
        theme: ThemeColors,
    ): Bitmap {
        val density = context.resources.displayMetrics.density
        val width = (widthDp.coerceAtLeast(1) * density).roundToInt().coerceAtLeast(1)
        val height = (heightDp.coerceAtLeast(1) * density).roundToInt().coerceAtLeast(1)
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val edge = (height * PEEK_MASK_HEIGHT_FRACTION)
            .roundToInt()
            .coerceIn(1, maxOf(1, height / 4))
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
        val canvas = Canvas(bitmap)
        canvas.drawRect(0f, 0f, width.toFloat(), edge.toFloat(), paint)
        canvas.drawRect(0f, (height - edge).toFloat(), width.toFloat(), height.toFloat(), paint)
        canvas.drawRect(0f, edge.toFloat(), edge.toFloat(), (height - edge).toFloat(), paint)
        canvas.drawRect(
            (width - edge).toFloat(),
            edge.toFloat(),
            width.toFloat(),
            (height - edge).toFloat(),
            paint,
        )
        return bitmap
    }

    private fun collectionContentToken(
        context: Context,
        widgetId: Int,
        options: Bundle,
    ): String {
        val snapshot = context
            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .getString("flutter.better_phenikaa_snapshot_v1", "")
            .orEmpty()
        val selectedDate = context
            .getSharedPreferences(WIDGET_SELECTION_PREFS, Context.MODE_PRIVATE)
            .getString(selectedDateKey(widgetId), "")
            .orEmpty()
        val sizeSignature = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            exactWidgetSizes(options).joinToString(";") { size ->
                String.format(Locale.US, "%.1fx%.1f", size.width, size.height)
            }
        } else {
            val size = legacyWidgetSize(options)
            String.format(Locale.US, "%.1fx%.1f", size.width, size.height)
        }
        return "${snapshot.hashCode()}|$selectedDate|$sizeSignature"
    }

    private fun contentTokenKey(widgetId: Int): String = "content_token_$widgetId"

    private fun themeTokenKey(widgetId: Int): String = "theme_token_$widgetId"

    @Suppress("DEPRECATION")
    private fun exactWidgetSizes(options: Bundle): List<SizeF> {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return emptyList()
        }
        return options
            .getParcelableArrayList<SizeF>(AppWidgetManager.OPTION_APPWIDGET_SIZES)
            .orEmpty()
            .filter { it.width > 0f && it.height > 0f }
            .distinctBy { size ->
                "${(size.width * 10f).roundToInt()}x${(size.height * 10f).roundToInt()}"
            }
    }

    private fun legacyWidgetSize(options: Bundle): SizeF {
        val minWidth = options
            .getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, DEFAULT_WIDGET_WIDTH_DP)
            .takeIf { it > 0 }
            ?: DEFAULT_WIDGET_WIDTH_DP
        val maxWidth = options
            .getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH, minWidth)
            .takeIf { it > 0 }
            ?: minWidth
        val minHeight = options
            .getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT, DEFAULT_WIDGET_HEIGHT_DP)
            .takeIf { it > 0 }
            ?: DEFAULT_WIDGET_HEIGHT_DP
        val maxHeight = options
            .getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT, minHeight)
            .takeIf { it > 0 }
            ?: minHeight

        return SizeF(
            maxOf(minWidth, maxWidth).toFloat(),
            minOf(minHeight, maxHeight).toFloat(),
        )
    }

    companion object {
        const val EXTRA_RENDER_WIDTH_DP = "renderWidthDp"
        const val EXTRA_RENDER_HEIGHT_DP = "renderHeightDp"
        const val ACTION_COLLECTION_FRAME_READY =
            "vn.edu.phenikaa.better_phenikaa_schedule.COLLECTION_FRAME_READY"
        const val EXTRA_READY_THEME_KEY = "readyThemeKey"
        const val WIDGET_SELECTION_PREFS = "better_phenikaa_widget_selection"
        private const val WIDGET_RENDER_STATE_PREFS = "better_phenikaa_widget_render_state"
        private const val FLUTTER_PREFS = "FlutterSharedPreferences"
        private const val THEME_KEY = "flutter.appTheme"

        fun selectedDateKey(widgetId: Int): String = "selected_date_$widgetId"
        fun resetChildKey(widgetId: Int): String = "reset_child_$widgetId"

        private fun transitionFromKey(widgetId: Int) = "transition_from_$widgetId"
        private fun transitionTargetKey(widgetId: Int) = "transition_target_$widgetId"
        private fun transitionStartedAtKey(widgetId: Int) = "transition_started_$widgetId"
        private fun transitionReadyKey(widgetId: Int) = "transition_ready_$widgetId"
        private fun transitionDisplayIndexKey(widgetId: Int) = "transition_index_$widgetId"

        private const val DATE_PICKER_REQUEST_CODE_BASE = 100_000
        private const val MAX_EXACT_LAYOUTS = 16
        private const val TRANSITION_FRAME_COUNT = 16
        private const val TRANSITION_FRAME_DELAY_MS = 33L
        private const val TRANSITION_FINAL_HOLD_MS = 0L
        private const val TARGET_COLLECTION_SETTLE_MS = 220L
        private const val TARGET_COLLECTION_FALLBACK_MS = 1_800L
        private const val NORMAL_REFRESH_COVER_HOLD_MS = 1_600L
        private const val TRANSITION_STALE_AFTER_MS = 8_000L
        private const val CALENDAR_HEIGHT_FRACTION = 0.42f
        private const val CALENDAR_WIDTH_FRACTION = 0.085f
        private const val CALENDAR_PADDING_FRACTION = 0.19f
        private const val PEEK_MASK_HEIGHT_FRACTION = 0.09f
        private const val DEFAULT_WIDGET_WIDTH_DP = 320
        private const val DEFAULT_WIDGET_HEIGHT_DP = 64
    }
}
