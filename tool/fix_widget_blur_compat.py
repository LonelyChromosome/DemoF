from pathlib import Path

service = Path('platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt')
s = service.read_text(encoding='utf-8')
s = s.replace('import android.graphics.RenderEffect\n', '')
old = '''    val frostPaint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)\n    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {\n        val blurRadius = (sharp.height * TRANSITION_BLUR_HEIGHT_FRACTION)\n            .coerceAtLeast(2f)\n        frostPaint.setRenderEffect(\n            RenderEffect.createBlurEffect(\n                blurRadius,\n                blurRadius,\n                Shader.TileMode.CLAMP,\n            ),\n        )\n    }\n    canvas.drawBitmap(sharp, 0f, 0f, frostPaint)\n'''
new = '''    // RemoteViews/widget builds cannot rely on Paint RenderEffect across all\n    // launcher/API combinations. Approximate a frosted blur with several\n    // translucent offset taps; the sharp card is revealed over it afterwards.\n    val softOffset = (sharp.height * TRANSITION_BLUR_HEIGHT_FRACTION)\n        .coerceIn(2f, 10f)\n    val frostPaint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG).apply {\n        alpha = 28\n    }\n    val taps = arrayOf(\n        -1f to 0f,\n        1f to 0f,\n        0f to -1f,\n        0f to 1f,\n        -0.7f to -0.7f,\n        0.7f to -0.7f,\n        -0.7f to 0.7f,\n        0.7f to 0.7f,\n    )\n    for ((dx, dy) in taps) {\n        canvas.drawBitmap(sharp, dx * softOffset, dy * softOffset, frostPaint)\n    }\n    val frostCenterPaint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG).apply {\n        alpha = 76\n    }\n    canvas.drawBitmap(sharp, 0f, 0f, frostCenterPaint)\n'''
if old not in s:
    raise SystemExit('RenderEffect frost block not found')
s = s.replace(old, new, 1)
service.write_text(s, encoding='utf-8')
