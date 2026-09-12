from pathlib import Path

# 1) Flutter: app theme is persisted immediately, but native widget owns the
# active widget theme key so it can keep the old theme frozen until the transition.
app_theme = Path('lib/theme/app_theme.dart')
s = app_theme.read_text(encoding='utf-8')
old = '''    await prefs.setString(_widgetPreferenceKey, _theme.storageKey);\n    notifyListeners();\n    await _syncWidgetTheme();\n'''
new = '''    if (!prefs.containsKey(_widgetPreferenceKey)) {\n      await prefs.setString(_widgetPreferenceKey, _theme.storageKey);\n    }\n    notifyListeners();\n    final widgetTheme = prefs.getString(_widgetPreferenceKey);\n    if (widgetTheme != _theme.storageKey) {\n      final nativeApplied = await _applyWidgetThemeImmediately(_theme.storageKey);\n      if (!nativeApplied) {\n        await prefs.setString(_widgetPreferenceKey, _theme.storageKey);\n        await _syncWidgetTheme();\n      }\n    }\n'''
if old not in s:
    raise SystemExit('load widget theme marker not found')
s = s.replace(old, new, 1)
old = '''    final nativeUpdate = _applyWidgetThemeImmediately(value.storageKey);\n    final prefs = await SharedPreferences.getInstance();\n    await Future.wait<bool>(<Future<bool>>[\n      prefs.setString(_preferenceKey, value.storageKey),\n      prefs.setString(_widgetPreferenceKey, value.storageKey),\n    ]);\n    final nativeApplied = await nativeUpdate;\n    if (!nativeApplied) {\n      await _syncWidgetTheme();\n    }\n'''
new = '''    final nativeUpdate = _applyWidgetThemeImmediately(value.storageKey);\n    final prefs = await SharedPreferences.getInstance();\n    await prefs.setString(_preferenceKey, value.storageKey);\n    final nativeApplied = await nativeUpdate;\n    if (!nativeApplied) {\n      await prefs.setString(_widgetPreferenceKey, value.storageKey);\n      await _syncWidgetTheme();\n    }\n'''
if old not in s:
    raise SystemExit('select widget theme marker not found')
s = s.replace(old, new, 1)
app_theme.write_text(s, encoding='utf-8')

# 2) Native MainActivity: do not switch the shared widget theme immediately.
# Freeze old visual first, then commit target theme and refresh the hidden stack.
for main_path in [
    Path('android/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/MainActivity.kt'),
    Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/MainActivity.kt'),
]:
    t = main_path.read_text(encoding='utf-8')
    if 'import android.os.Handler' not in t:
        t = t.replace('import android.content.Context\n', 'import android.content.Context\nimport android.os.Handler\nimport android.os.Looper\n', 1)
    old_block = '''            val theme = call.argument<String>("theme") ?: "classic"\n            val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)\n            // Synchronous write guarantees ScheduleWidgetProvider reads this same\n            // theme in the immediately-following update call.\n            prefs.edit().putString(THEME_KEY, theme).commit()\n\n            val manager = AppWidgetManager.getInstance(this)\n            val component = ComponentName(this, ScheduleWidgetProvider::class.java)\n            val widgetIds = manager.getAppWidgetIds(component)\n            if (widgetIds.isNotEmpty()) {\n                ScheduleWidgetProvider().onUpdate(this, manager, widgetIds, prefs)\n            }\n            result.success(widgetIds.size)\n'''
    new_block = '''            val theme = call.argument<String>("theme") ?: "classic"\n            val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)\n            val oldTheme = prefs.getString(THEME_KEY, "classic") ?: "classic"\n\n            val manager = AppWidgetManager.getInstance(this)\n            val component = ComponentName(this, ScheduleWidgetProvider::class.java)\n            val widgetIds = manager.getAppWidgetIds(component)\n            if (widgetIds.isNotEmpty() && oldTheme != theme) {\n                val provider = ScheduleWidgetProvider()\n                // Phase 1: freeze a fully rendered OLD-theme card above StackView.\n                // Nothing underneath is invalidated until the launcher has applied\n                // this cover, so returning Home can only show the previous theme.\n                provider.stageThemeTransition(this, manager, widgetIds, oldTheme, theme)\n                Handler(Looper.getMainLooper()).postDelayed({\n                    // Phase 2: only now switch the widget theme source and rebuild the\n                    // hidden collection. The ready callback starts the wipe later.\n                    prefs.edit().putString(THEME_KEY, theme).commit()\n                    provider.refreshHiddenCollection(this, manager, widgetIds, oldTheme, theme)\n                }, THEME_FREEZE_SETTLE_MS)\n            } else if (oldTheme != theme) {\n                prefs.edit().putString(THEME_KEY, theme).commit()\n            }\n            result.success(widgetIds.size)\n'''
    if old_block not in t:
        raise SystemExit(f'MainActivity marker not found: {main_path}')
    t = t.replace(old_block, new_block, 1)
    t = t.replace(
        '        private const val THEME_KEY = "flutter.appTheme"\n',
        '        private const val THEME_KEY = "flutter.appTheme"\n        private const val THEME_FREEZE_SETTLE_MS = 140L\n',
        1,
    )
    main_path.write_text(t, encoding='utf-8')

# 3) Layout: cover must be above the empty view. This removes the temporary
# "Không có lịch học" text from the transition even if StackView toggles empty.
layout = Path('platform/android_widget/app/src/main/res/layout/schedule_widget.xml')
x = layout.read_text(encoding='utf-8')
cover = '''    <!--\n      Atomic refresh cover. During collection/theme invalidation Samsung Launcher can\n      briefly lay out several StackView children at once. The provider puts a fully\n      rendered first card here before invalidating the collection, then hides it only\n      after the refreshed stack is stable. This prevents both overlapping text and\n      the old peek/edge artifacts without disabling swipe navigation.\n    -->\n    <ImageView\n        android:id="@+id/widget_refresh_cover"\n        android:layout_width="match_parent"\n        android:layout_height="match_parent"\n        android:clickable="false"\n        android:contentDescription="@null"\n        android:focusable="false"\n        android:scaleType="fitXY"\n        android:visibility="gone" />\n\n'''
if cover not in x:
    raise SystemExit('cover block not found')
x = x.replace(cover, '', 1)
empty_end = '''    <TextView\n        android:id="@+id/widget_empty"\n        android:layout_width="match_parent"\n        android:layout_height="match_parent"\n        android:gravity="center"\n        android:paddingStart="18dp"\n        android:paddingEnd="48dp"\n        android:text="Không có lịch học"\n        android:textColor="#FFFFFFFF"\n        android:textSize="14sp"\n        android:textStyle="bold" />\n\n'''
if empty_end not in x:
    raise SystemExit('empty view block not found')
x = x.replace(empty_end, empty_end + cover, 1)
layout.write_text(x, encoding='utf-8')

# 4) Provider: explicit two-phase native transition.
provider = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt')
p = provider.read_text(encoding='utf-8')
insert_before = '''    override fun onAppWidgetOptionsChanged(\n'''
methods = r'''    fun stageThemeTransition(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetIds: IntArray,
        oldThemeKey: String,
        targetThemeKey: String,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        widgetIds.forEach { widgetId ->
            val options = appWidgetManager.getAppWidgetOptions(widgetId)
            val size = legacyWidgetSize(options)
            val widthDp = size.width.roundToInt().coerceAtLeast(1)
            val heightDp = size.height.roundToInt().coerceAtLeast(1)
            val cover = renderWidgetTransitionFrame(
                context = context,
                widgetId = widgetId,
                renderWidthDp = widthDp,
                renderHeightDp = heightDp,
                progress = 0f,
                fromThemeKey = oldThemeKey,
                toThemeKey = targetThemeKey,
            ) ?: renderWidgetRefreshCover(
                context,
                widgetId,
                widthDp,
                heightDp,
                oldThemeKey,
            )
            val oldTheme = themeColorsForKey(oldThemeKey)
            val freeze = RemoteViews(context.packageName, R.layout.schedule_widget)
            freeze.setImageViewBitmap(
                R.id.widget_theme_background,
                renderThemeBackground(context, widthDp, heightDp, oldTheme),
            )
            freeze.setInt(R.id.widget_calendar, "setColorFilter", oldTheme.iconColor)
            if (cover != null) {
                freeze.setImageViewBitmap(R.id.widget_refresh_cover, cover)
                freeze.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)
                freeze.setViewVisibility(R.id.widget_list, View.INVISIBLE)
            }
            appWidgetManager.partiallyUpdateAppWidget(widgetId, freeze)
            state.edit()
                .putString(transitionFromKey(widgetId), oldThemeKey)
                .putString(transitionTargetKey(widgetId), targetThemeKey)
                .apply()
        }
    }

    fun refreshHiddenCollection(
        context: Context,
        appWidgetManager: AppWidgetManager,
        widgetIds: IntArray,
        oldThemeKey: String,
        targetThemeKey: String,
    ) {
        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)
        widgetIds.forEach { widgetId ->
            val expected = state.getString(transitionTargetKey(widgetId), null)
            if (expected != targetThemeKey) return@forEach
            state.edit()
                .putString(themeTokenKey(widgetId), targetThemeKey)
                .putString(transitionFromKey(widgetId), oldThemeKey)
                .apply()
            // StackView remains INVISIBLE behind the frozen old-theme bitmap.
            appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
        }
    }

'''
if insert_before not in p:
    raise SystemExit('provider insertion marker missing')
p = p.replace(insert_before, methods + insert_before, 1)

# Make transition read its frozen source theme.
old_sig = '''        val manager = AppWidgetManager.getInstance(context)\n        val options = manager.getAppWidgetOptions(widgetId)\n'''
new_sig = '''        val manager = AppWidgetManager.getInstance(context)\n        val state = context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)\n        val targetThemeKey = state.getString(transitionTargetKey(widgetId), null) ?: readyThemeKey\n        if (targetThemeKey != readyThemeKey) {\n            return\n        }\n        val fromThemeKey = state.getString(transitionFromKey(widgetId), null) ?: readyThemeKey\n        val options = manager.getAppWidgetOptions(widgetId)\n'''
# Replace only in playRevealTransition region: first occurrence after function name.
pos = p.find('    private fun playRevealTransition(')
if pos < 0:
    raise SystemExit('playRevealTransition missing')
sub = p[pos:]
if old_sig not in sub:
    raise SystemExit('transition manager marker missing')
sub = sub.replace(old_sig, new_sig, 1)
p = p[:pos] + sub

# Thread fromThemeKey through frame calls.
p = p.replace(
'''                readyThemeKey = readyThemeKey,\n                widthDp = widthDp,\n''',
'''                readyThemeKey = readyThemeKey,\n                fromThemeKey = fromThemeKey,\n                widthDp = widthDp,\n''',
1,
)
p = p.replace(
'''        readyThemeKey: String,\n        widthDp: Int,\n''',
'''        readyThemeKey: String,\n        fromThemeKey: String,\n        widthDp: Int,\n''',
1,
)
p = p.replace(
'''            heightDp,\n            progress,\n        )\n''',
'''            heightDp,\n            progress,\n            fromThemeKey,\n            readyThemeKey,\n        )\n''',
1,
)
p = p.replace(
'''                    readyThemeKey = readyThemeKey,\n                    widthDp = widthDp,\n''',
'''                    readyThemeKey = readyThemeKey,\n                    fromThemeKey = fromThemeKey,\n                    widthDp = widthDp,\n''',
1,
)
# At transition start, switch background/calendar behind the still-visible cover.
needle = '''        val denominator = (TRANSITION_FRAME_COUNT - 1).coerceAtLeast(1)\n        val progress = frame.toFloat() / denominator.toFloat()\n'''
repl = '''        val denominator = (TRANSITION_FRAME_COUNT - 1).coerceAtLeast(1)\n        val progress = frame.toFloat() / denominator.toFloat()\n        if (frame == 0) {\n            val targetTheme = themeColorsForKey(readyThemeKey)\n            val prep = RemoteViews(context.packageName, R.layout.schedule_widget)\n            prep.setImageViewBitmap(\n                R.id.widget_theme_background,\n                renderThemeBackground(context, widthDp, heightDp, targetTheme),\n            )\n            prep.setInt(R.id.widget_calendar, "setColorFilter", targetTheme.iconColor)\n            prep.setViewVisibility(R.id.widget_list, View.INVISIBLE)\n            prep.setViewVisibility(R.id.widget_refresh_cover, View.VISIBLE)\n            AppWidgetManager.getInstance(context).partiallyUpdateAppWidget(widgetId, prep)\n        }\n'''
if needle not in p:
    raise SystemExit('frame progress marker missing')
p = p.replace(needle, repl, 1)
# Clean transition state on finish.
needle = '''        AppWidgetManager.getInstance(context)\n            .partiallyUpdateAppWidget(widgetId, reveal)\n    }\n\n    private data class ThemeColors(\n'''
repl = '''        AppWidgetManager.getInstance(context)\n            .partiallyUpdateAppWidget(widgetId, reveal)\n        context.getSharedPreferences(WIDGET_RENDER_STATE_PREFS, Context.MODE_PRIVATE)\n            .edit()\n            .remove(transitionFromKey(widgetId))\n            .remove(transitionTargetKey(widgetId))\n            .apply()\n    }\n\n    private data class ThemeColors(\n'''
if needle not in p:
    raise SystemExit('finish transition marker missing')
p = p.replace(needle, repl, 1)
# Refactor theme lookup to allow explicit old/new theme rendering.
old_fun = '''    private fun readThemeColors(context: Context): ThemeColors {\n        val key = context\n            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)\n            .getString("flutter.appTheme", "classic")\n            ?: "classic"\n        return when (key) {\n'''
new_fun = '''    private fun readThemeColors(context: Context): ThemeColors {\n        val key = context\n            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)\n            .getString("flutter.appTheme", "classic")\n            ?: "classic"\n        return themeColorsForKey(key)\n    }\n\n    private fun themeColorsForKey(key: String): ThemeColors = when (key) {\n'''
if old_fun not in p:
    raise SystemExit('readThemeColors marker missing')
p = p.replace(old_fun, new_fun, 1)
# The refactor leaves one extra closing brace after when; normalize exact tail.
p = p.replace(
'''            else -> ThemeColors("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())\n        }\n    }\n\n    private fun renderThemeBackground(\n''',
'''            else -> ThemeColors("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFFFFF.toInt())\n        }\n\n    private fun renderThemeBackground(\n''',
1,
)
# Add state-key helpers near existing token helpers/companion constants.
marker = '''        private const val DATE_PICKER_REQUEST_CODE_BASE = 100_000\n'''
helpers = '''        private fun transitionFromKey(widgetId: Int) = "transition_from_$widgetId"\n        private fun transitionTargetKey(widgetId: Int) = "transition_target_$widgetId"\n\n'''
if marker not in p:
    raise SystemExit('companion marker missing')
p = p.replace(marker, helpers + marker, 1)
provider.write_text(p, encoding='utf-8')

# 5) Service: render explicit old/new theme bitmaps for a real cross-theme wipe.
service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
t = service.read_text(encoding='utf-8')
t = t.replace(
'''private fun renderWidgetSlide(\n    context: Context,\n    item: WidgetClass,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n): Bitmap {\n''',
'''private fun renderWidgetSlide(\n    context: Context,\n    item: WidgetClass,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n    themeOverrideKey: String? = null,\n): Bitmap {\n''',
1,
)
t = t.replace(
'''        val theme = readWidgetTheme(context)\n''',
'''        val theme = themeOverrideKey?.let(::widgetThemeForKey) ?: readWidgetTheme(context)\n''',
1,
)
t = t.replace(
'''internal fun renderWidgetRefreshCover(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    return renderWidgetSlide(context, first, renderWidthDp, renderHeightDp)\n}\n''',
'''internal fun renderWidgetRefreshCover(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n    themeOverrideKey: String? = null,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    return renderWidgetSlide(\n        context,\n        first,\n        renderWidthDp,\n        renderHeightDp,\n        themeOverrideKey,\n    )\n}\n''',
1,
)
old_transition_sig = '''internal fun renderWidgetTransitionFrame(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n    progress: Float,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    val sharp = renderWidgetSlide(context, first, renderWidthDp, renderHeightDp)\n'''
new_transition_sig = '''internal fun renderWidgetTransitionFrame(\n    context: Context,\n    widgetId: Int,\n    renderWidthDp: Int,\n    renderHeightDp: Int,\n    progress: Float,\n    fromThemeKey: String? = null,\n    toThemeKey: String? = null,\n): Bitmap? {\n    val first = readWidgetClasses(context, widgetId).firstOrNull() ?: return null\n    val fromKey = fromThemeKey ?: readWidgetTheme(context).key\n    val toKey = toThemeKey ?: readWidgetTheme(context).key\n    val oldSharp = renderWidgetSlide(context, first, renderWidthDp, renderHeightDp, fromKey)\n    val sharp = renderWidgetSlide(context, first, renderWidthDp, renderHeightDp, toKey)\n'''
if old_transition_sig not in t:
    raise SystemExit('transition service signature missing')
t = t.replace(old_transition_sig, new_transition_sig, 1)
# Base should be OLD theme, lightly frosted; reveal new sharp from left.
t = t.replace(
'''        canvas.drawBitmap(sharp, dx * softOffset, dy * softOffset, frostPaint)\n''',
'''        canvas.drawBitmap(oldSharp, dx * softOffset, dy * softOffset, frostPaint)\n'''
)
t = t.replace(
'''    canvas.drawBitmap(sharp, 0f, 0f, frostCenterPaint)\n\n    val theme = readWidgetTheme(context)\n''',
'''    canvas.drawBitmap(oldSharp, 0f, 0f, frostCenterPaint)\n\n    val theme = widgetThemeForKey(toKey)\n''',
1,
)
# Refactor theme lookup for explicit keys.
old_read = '''private fun readWidgetTheme(context: Context): WidgetTheme {\n    val key = context\n        .getSharedPreferences(SNAPSHOT_PREFS, Context.MODE_PRIVATE)\n        .getString(THEME_KEY, "classic")\n        ?: "classic"\n    return when (key) {\n'''
new_read = '''private fun readWidgetTheme(context: Context): WidgetTheme {\n    val key = context\n        .getSharedPreferences(SNAPSHOT_PREFS, Context.MODE_PRIVATE)\n        .getString(THEME_KEY, "classic")\n        ?: "classic"\n    return widgetThemeForKey(key)\n}\n\nprivate fun widgetThemeForKey(key: String): WidgetTheme = when (key) {\n'''
if old_read not in t:
    raise SystemExit('readWidgetTheme marker missing')
t = t.replace(old_read, new_read, 1)
t = t.replace(
'''        else -> WidgetTheme("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFDDE8FF.toInt())\n    }\n}\n''',
'''        else -> WidgetTheme("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFDDE8FF.toInt())\n    }\n''',
1,
)
service.write_text(t, encoding='utf-8')

# 6) Version bump.
pubspec = Path('pubspec.yaml')
v = pubspec.read_text(encoding='utf-8')
if 'version: 2.0.10+15' not in v:
    raise SystemExit('expected version 2.0.10+15 missing')
v = v.replace('version: 2.0.10+15', 'version: 2.0.11+16', 1)
pubspec.write_text(v, encoding='utf-8')
