package vn.edu.phenikaa.better_phenikaa_schedule

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.SizeF
import android.util.TypedValue
import android.widget.RemoteViews
import es.antonborri.home_widget.HomeWidgetProvider
import java.util.Locale
import kotlin.math.min
import kotlin.math.roundToInt

class ScheduleWidgetProvider : HomeWidgetProvider() {
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
                )
            }
        } else {
            val fallback = legacyWidgetSize(options)
            buildWidgetViews(
                context = context,
                widgetId = widgetId,
                visualWidthDp = fallback.width,
                visualHeightDp = fallback.height,
            )
        }

        appWidgetManager.updateAppWidget(widgetId, views)
        appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
    }

    private fun buildWidgetViews(
        context: Context,
        widgetId: Int,
        visualWidthDp: Float,
        visualHeightDp: Float,
    ): RemoteViews {
        val widthDp = visualWidthDp.coerceAtLeast(1f)
        val heightDp = visualHeightDp.coerceAtLeast(1f)
        val renderWidthDp = widthDp.roundToInt().coerceAtLeast(1)
        val renderHeightDp = heightDp.roundToInt().coerceAtLeast(1)
        val views = RemoteViews(context.packageName, R.layout.schedule_widget)

        // Use the exact host bounds. Do not enlarge/translate StackView to compensate
        // for a particular launcher grid: that workaround can push the card outside
        // its rounded outline on other launchers and produces clipped corners.
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

            // Keep the calendar action as a small corner control. Its square size and
            // inner padding are proportional to the actual host frame, so it does not
            // consume a fixed-width strip on different launcher grids.
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

        // The selected day (today by default) remains the first item whenever the
        // provider refreshes. Ordinary StackView swipes continue to loop normally.
        views.setDisplayedChild(R.id.widget_list, 0)
        return views
    }

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

        // A one-row widget should use all horizontal space the launcher assigned.
        // Width is therefore taken from the widest host bound, while height stays at
        // the shortest valid row height. No cell-count assumption is involved.
        return SizeF(
            maxOf(minWidth, maxWidth).toFloat(),
            minOf(minHeight, maxHeight).toFloat(),
        )
    }

    companion object {
        const val EXTRA_RENDER_WIDTH_DP = "renderWidthDp"
        const val EXTRA_RENDER_HEIGHT_DP = "renderHeightDp"
        const val WIDGET_SELECTION_PREFS = "better_phenikaa_widget_selection"

        fun selectedDateKey(widgetId: Int): String = "selected_date_$widgetId"

        private const val DATE_PICKER_REQUEST_CODE_BASE = 100_000
        private const val MAX_EXACT_LAYOUTS = 16
        private const val CALENDAR_HEIGHT_FRACTION = 0.42f
        private const val CALENDAR_WIDTH_FRACTION = 0.085f
        private const val CALENDAR_PADDING_FRACTION = 0.19f
        private const val DEFAULT_WIDGET_WIDTH_DP = 320
        private const val DEFAULT_WIDGET_HEIGHT_DP = 64
    }
}
