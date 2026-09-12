from pathlib import Path

provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
s = provider.read_text(encoding='utf-8')

s = s.replace(
'''                revealCollectionWhenReady(context, widgetId, readyThemeKey)\n''',
'''                playRevealTransition(context, widgetId, readyThemeKey)\n''',
1,
)

s = s.replace(
'''            val cover = renderWidgetRefreshCover(\n                context,\n                widgetId,\n                renderWidthDp,\n                renderHeightDp,\n            )\n''',
'''            val cover = renderWidgetTransitionFrame(\n                context,\n                widgetId,\n                renderWidthDp,\n                renderHeightDp,\n                0f,\n            ) ?: renderWidgetRefreshCover(\n                context,\n                widgetId,\n                renderWidthDp,\n                renderHeightDp,\n            )\n''',
1,
)

old_reveal = '''    private fun revealCollectionWhenReady(\n        context: Context,\n        widgetId: Int,\n        readyThemeKey: String,\n    ) {\n        // Never reveal a frame that belongs to an older rapid theme change.\n        if (readyThemeKey != readThemeColors(context).key) {\n            return\n        }\n        Handler(Looper.getMainLooper()).postDelayed({\n            if (readyThemeKey != readThemeColors(context).key) {\n                return@postDelayed\n            }\n            val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)\n            reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)\n            reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n            AppWidgetManager.getInstance(context)\n                .partiallyUpdateAppWidget(widgetId, reveal)\n        }, COLLECTION_READY_SETTLE_MS)\n    }\n'''
new_reveal = '''    private fun playRevealTransition(\n        context: Context,\n        widgetId: Int,\n        readyThemeKey: String,\n    ) {\n        // The collection service can finish while the app is still covering Home.\n        // Keep the single bitmap cover in front until the launcher has had time to\n        // settle its hidden StackView, then reveal the new card with a deliberate\n        // left-to-right frosted wipe. Stale theme callbacks are ignored.\n        if (readyThemeKey != readThemeColors(context).key) {\n            return\n        }\n        val manager = AppWidgetManager.getInstance(context)\n        val options = manager.getAppWidgetOptions(widgetId)\n        val size = legacyWidgetSize(options)\n        val widthDp = size.width.roundToInt().coerceAtLeast(1)\n        val heightDp = size.height.roundToInt().coerceAtLeast(1)\n\n        Handler(Looper.getMainLooper()).postDelayed({\n            if (readyThemeKey != readThemeColors(context).key) {\n                return@postDelayed\n            }\n            runTransitionFrame(\n                context = context,\n                widgetId = widgetId,\n                readyThemeKey = readyThemeKey,\n                widthDp = widthDp,\n                heightDp = heightDp,\n                frame = 0,\n            )\n        }, TRANSITION_PREPARE_MS)\n    }\n\n    private fun runTransitionFrame(\n        context: Context,\n        widgetId: Int,\n        readyThemeKey: String,\n        widthDp: Int,\n        heightDp: Int,\n        frame: Int,\n    ) {\n        if (readyThemeKey != readThemeColors(context).key) {\n            return\n        }\n        val denominator = (TRANSITION_FRAME_COUNT - 1).coerceAtLeast(1)\n        val progress = frame.toFloat() / denominator.toFloat()\n        val bitmap = renderWidgetTransitionFrame(\n            context,\n            widgetId,\n            widthDp,\n            heightDp,\n            progress,\n        )\n        if (bitmap == null) {\n            finishRevealTransition(context, widgetId, readyThemeKey)\n            return\n        }\n\n        val frameViews = RemoteViews(context.packageName, R.layout.schedule_widget)\n        frameViews.setImageViewBitmap(R.id.widget_refresh_cover, bitmap)\n        frameViews.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)\n        frameViews.setViewVisibility(R.id.widget_list, View.INVISIBLE)\n        AppWidgetManager.getInstance(context)\n            .partiallyUpdateAppWidget(widgetId, frameViews)\n\n        if (frame + 1 < TRANSITION_FRAME_COUNT) {\n            Handler(Looper.getMainLooper()).postDelayed({\n                runTransitionFrame(\n                    context = context,\n                    widgetId = widgetId,\n                    readyThemeKey = readyThemeKey,\n                    widthDp = widthDp,\n                    heightDp = heightDp,\n                    frame = frame + 1,\n                )\n            }, TRANSITION_FRAME_DELAY_MS)\n        } else {\n            Handler(Looper.getMainLooper()).postDelayed({\n                finishRevealTransition(context, widgetId, readyThemeKey)\n            }, TRANSITION_FINAL_HOLD_MS)\n        }\n    }\n\n    private fun finishRevealTransition(\n        context: Context,\n        widgetId: Int,\n        readyThemeKey: String,\n    ) {\n        if (readyThemeKey != readThemeColors(context).key) {\n            return\n        }\n        val reveal = RemoteViews(context.packageName, R.layout.schedule_widget)\n        reveal.setViewVisibility(R.id.widget_list, View.VISIBLE)\n        reveal.setViewVisibility(R.id.widget_refresh_cover, View.GONE)\n        AppWidgetManager.getInstance(context)\n            .partiallyUpdateAppWidget(widgetId, reveal)\n    }\n'''
if old_reveal not in s:
    raise SystemExit('old reveal function marker missing')
s = s.replace(old_reveal, new_reveal, 1)

s = s.replace(
'''        private const val COLLECTION_READY_SETTLE_MS = 300L\n''',
'''        private const val TRANSITION_PREPARE_MS = 520L\n        private const val TRANSITION_FRAME_COUNT = 8\n        private const val TRANSITION_FRAME_DELAY_MS = 62L\n        private const val TRANSITION_FINAL_HOLD_MS = 180L\n''',
1,
)
provider.write_text(s, encoding='utf-8')

service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
t = service.read_text(encoding='utf-8')
if 'import android.graphics.RenderEffect\n' not in t:
    t = t.replace('import android.graphics.Paint\n', 'import android.graphics.Paint\nimport android.graphics.RenderEffect\n', 1)

cover_marker = '''internal fun renderWidgetRefreshCover(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    return renderWidgetSlide(context, first, renderWidthDp, renderHeightDp)\n}\n'''
transition_code = '''internal fun renderWidgetRefreshCover(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    return renderWidgetSlide(context, first, renderWidthDp, renderHeightDp)\n}\n\ninternal fun renderWidgetTransitionFrame(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n    progress: Float,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    val sharp = renderWidgetSlide(context, first, renderWidthDp, renderHeightDp)\n    val output = Bitmap.createBitmap(sharp.width, sharp.height, Bitmap.Config.ARGB_8888)\n    val canvas = Canvas(output)\n    val p = progress.coerceIn(0f, 1f)\n\n    val frostPaint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)\n    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {\n        val blurRadius = (sharp.height * TRANSITION_BLUR_HEIGHT_FRACTION)\n            .coerceAtLeast(2f)\n        frostPaint.renderEffect = RenderEffect.createBlurEffect(\n            blurRadius,\n            blurRadius,\n            Shader.TileMode.CLAMP,\n        )\n    }\n    canvas.drawBitmap(sharp, 0f, 0f, frostPaint)\n\n    val theme = readWidgetTheme(context)\n    val veilAlpha = ((1f - p) * 92f).toInt().coerceIn(0, 92)\n    if (veilAlpha > 0) {\n        val veilColor = (theme.startColor and 0x00FFFFFF) or (veilAlpha shl 24)\n        canvas.drawColor(veilColor)\n    }\n\n    val revealRight = sharp.width * p\n    if (revealRight > 0f) {\n        val save = canvas.save()\n        canvas.clipRect(0f, 0f, revealRight, sharp.height.toFloat())\n        canvas.drawBitmap(sharp, 0f, 0f, null)\n        canvas.restoreToCount(save)\n    }\n\n    if (p > 0f && p < 1f) {\n        val glowWidth = (sharp.width * TRANSITION_EDGE_WIDTH_FRACTION)\n            .coerceIn(12f, 54f)\n        val left = (revealRight - glowWidth).coerceAtLeast(0f)\n        val right = (revealRight + glowWidth).coerceAtMost(sharp.width.toFloat())\n        if (right > left) {\n            val glow = Paint(Paint.ANTI_ALIAS_FLAG).apply {\n                shader = LinearGradient(\n                    left,\n                    0f,\n                    right,\n                    0f,\n                    intArrayOf(0x00FFFFFF, 0x5AFFFFFF, 0x00FFFFFF),\n                    floatArrayOf(0f, 0.5f, 1f),\n                    Shader.TileMode.CLAMP,\n                )\n            }\n            canvas.drawRect(left, 0f, right, sharp.height.toFloat(), glow)\n        }\n    }\n\n    return output\n}\n'''
if cover_marker not in t:
    raise SystemExit('refresh cover marker missing')
t = t.replace(cover_marker, transition_code, 1)

constants_marker = '''private const val MIN_DETAIL_FIT_SCALE = 0.68f\n'''
if constants_marker not in t:
    # tolerate earlier constant value while still inserting before default dimensions
    constants_marker = '''private const val DEFAULT_WIDGET_WIDTH_DP = 320\n'''
    transition_constants = '''private const val TRANSITION_BLUR_HEIGHT_FRACTION = 0.075f\nprivate const val TRANSITION_EDGE_WIDTH_FRACTION = 0.055f\nprivate const val DEFAULT_WIDGET_WIDTH_DP = 320\n'''
    if constants_marker not in t:
        raise SystemExit('service constants marker missing')
    t = t.replace(constants_marker, transition_constants, 1)
else:
    t = t.replace(
        constants_marker,
        constants_marker + 'private const val TRANSITION_BLUR_HEIGHT_FRACTION = 0.075f\nprivate const val TRANSITION_EDGE_WIDTH_FRACTION = 0.055f\n',
        1,
    )
service.write_text(t, encoding='utf-8')

pubspec = Path('pubspec.yaml')
p = pubspec.read_text(encoding='utf-8')
if 'version: 2.0.9+14' not in p:
    raise SystemExit('expected 2.0.9 version missing')
p = p.replace('version: 2.0.9+14', 'version: 2.0.10+15', 1)
pubspec.write_text(p, encoding='utf-8')
