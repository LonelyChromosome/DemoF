from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing marker: {label}")
    return text.replace(old, new, 1)


# 1) Account -> Theme tile must listen directly to the controller because it can
# live inside a route/sheet that is not rebuilt with the app root.
theme_file = Path("lib/theme/app_theme.dart")
t = theme_file.read_text(encoding="utf-8")
start = t.index("class AppThemeSettingButton extends StatelessWidget")
new_button = r'''class AppThemeSettingButton extends StatelessWidget {
  const new({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = AppThemeController.instance;
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final palette = controller.palette;
        return AppThemePanel(
          elevated: false,
          alt: true,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: InkWell(
            onTap: () => showAppThemePicker(context),
            child: Row(
              children: <Widget>[
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: <Color>[palette.primary, palette.accent],
                    ),
                    borderRadius: BorderRadius.circular(
                      palette.geometry == AppThemeGeometry.rounded ? 10 : 1,
                    ),
                  ),
                  child: Icon(
                    controller.theme.icon,
                    color: palette.widgetText,
                    size: 21,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        'Giao diện',
                        style: TextStyle(
                          color: palette.textPrimary,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        controller.theme.label,
                        style: TextStyle(
                          color: palette.textSecondary,
                          fontSize: 11.5,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded, color: palette.textSecondary),
              ],
            ),
          ),
        );
      },
    );
  }
}
'''
t = t[:start] + new_button
theme_file.write_text(t, encoding="utf-8")

# 2) Remove every classic-blue native underlay. The actual themed bitmap fills
# the widget; the transparent rounded drawable is used only to keep the root
# outline for launcher clipping.
drawable = Path("platform/android_widget/app/src/main/res/drawable/schedule_widget_outline.xml")
drawable.write_text(
    '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@android:color/transparent" />
    <corners android:radius="18dp" />
</shape>
''',
    encoding="utf-8",
)

layout = Path("platform/android_widget/app/src/main/res/layout/schedule_widget.xml")
x = layout.read_text(encoding="utf-8")
x = replace_once(
    x,
    '    android:background="@drawable/schedule_widget_background"\n',
    '    android:background="@drawable/schedule_widget_outline"\n',
    "widget root blue background",
)
layout.write_text(x, encoding="utf-8")

item = Path("platform/android_widget/app/src/main/res/layout/schedule_widget_item.xml")
i = item.read_text(encoding="utf-8")
i = replace_once(
    i,
    '    android:background="@drawable/schedule_widget_background"\n',
    '    android:background="@android:color/transparent"\n',
    "widget item blue background",
)
i = replace_once(i, '    android:clipToOutline="true"\n', '    android:clipToOutline="false"\n', "item clip")
i = replace_once(i, '    android:outlineProvider="background">\n', '    android:outlineProvider="none">\n', "item outline")
item.write_text(i, encoding="utf-8")

# 3) Keep the RemoteViews adapter identity stable across theme changes. Theme in
# the URI forced Android to destroy/recreate the factory, which caused the visible
# ~1s mixed old/new card. Size remains in the URI so resizing still recreates the
# factory with correct dimensions.
provider = Path(
    "platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt"
)
p = provider.read_text(encoding="utf-8")
p = replace_once(
    p,
    '            data = Uri.parse("better-phenikaa://widget/$widgetId/$sizeToken/${theme.key}")\n',
    '            data = Uri.parse("better-phenikaa://widget/$widgetId/$sizeToken")\n',
    "stable adapter uri",
)
p = replace_once(
    p,
    '''        appWidgetManager.updateAppWidget(widgetId, views)
        appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
''',
    '''        // Refresh the existing collection factory before applying the small
        // native chrome update. With a stable adapter URI this updates the visible
        // card in-place instead of showing a torn old/new theme frame.
        appWidgetManager.notifyAppWidgetViewDataChanged(widgetId, R.id.widget_list)
        appWidgetManager.updateAppWidget(widgetId, views)
''',
    "widget refresh order",
)
provider.write_text(p, encoding="utf-8")

# 4) If Android still asks for a loading view while refreshing the collection,
# render the real first card in the current theme so there is never an empty or
# differently-coloured placeholder frame.
service = Path(
    "platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt"
)
s = service.read_text(encoding="utf-8")
s = replace_once(
    s,
    "    override fun getLoadingView(): RemoteViews? = null\n",
    '''    override fun getLoadingView(): RemoteViews? {
        val item = items.firstOrNull() ?: return null
        val views = RemoteViews(context.packageName, R.layout.schedule_widget_item)
        val widthDp = renderWidthDp.coerceAtLeast(1)
        val heightDp = renderHeightDp.coerceAtLeast(1)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            views.setViewLayoutWidth(
                R.id.widget_slide_item,
                widthDp.toFloat(),
                TypedValue.COMPLEX_UNIT_DIP,
            )
            views.setViewLayoutHeight(
                R.id.widget_slide_item,
                heightDp.toFloat(),
                TypedValue.COMPLEX_UNIT_DIP,
            )
        }
        views.setImageViewBitmap(R.id.widget_slide_image, renderSlide(item))
        return views
    }
''',
    "real loading view",
)
service.write_text(s, encoding="utf-8")

# Release revision.
pubspec = Path("pubspec.yaml")
v = pubspec.read_text(encoding="utf-8")
v2 = re.sub(r"^version:\s*2\.0\.1\+6\s*$", "version: 2.0.2+7", v, count=1, flags=re.M)
if v2 == v:
    raise RuntimeError("version 2.0.1+6 marker missing")
pubspec.write_text(v2, encoding="utf-8")

print("Applied Better Phenikaa 2.0.2 UI/widget polish fixes.")
