import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  const platformRoot = 'platform/android_widget/app/src/main';
  const androidRoot = 'android/app/src/main';
  const packagePath =
      'kotlin/vn/edu/phenikaa/better_phenikaa_schedule';

  test('theme transition starts only after Home can become visible', () {
    final mainActivity = _read('$platformRoot/$packagePath/MainActivity.kt');
    final provider = _read(
      '$platformRoot/$packagePath/ScheduleWidgetProvider.kt',
    );
    final service = _read(
      '$platformRoot/$packagePath/ScheduleWidgetService.kt',
    );

    expect(mainActivity, contains('pendingThemeTransition'));
    expect(mainActivity, contains('override fun onStop()'));
    expect(mainActivity, contains('HOME_REVEAL_GRACE_MS'));
    expect(
      mainActivity.indexOf('override fun onStop()'),
      lessThan(mainActivity.lastIndexOf('beginThemeTransition')),
    );
    expect(provider, contains('runVisibleThemeTransitionFrame'));
    expect(provider, contains('renderWidgetThemeTransitionFrame'));
    expect(provider, contains('setViewVisibility(R.id.widget_list, View.INVISIBLE)'));
    expect(provider, contains('commitTargetThemeAndRefresh'));
    expect(service, contains('renderWidgetThemeTransitionFrame'));
    expect(service, isNot(contains('renderWidgetThemeTransitionOverlay')));
  });

  test('theme transition keeps a smooth cached frame cadence', () {
    final provider = _read(
      '$platformRoot/$packagePath/ScheduleWidgetProvider.kt',
    );
    final service = _read(
      '$platformRoot/$packagePath/ScheduleWidgetService.kt',
    );

    expect(provider, contains('TRANSITION_FRAME_COUNT = 24'));
    expect(provider, contains('TRANSITION_FRAME_DELAY_MS = 42L'));
    expect(service, contains('themeTransitionFrameCache'));
    expect(service, contains('obtainThemeTransitionFrameSource'));
    expect(provider, contains('clearWidgetThemeTransitionFrameCache'));
  });

  test('transition cover prefers a real class over an empty-day placeholder', () {
    final provider = _read(
      '$platformRoot/$packagePath/ScheduleWidgetProvider.kt',
    );
    final service = _read(
      '$platformRoot/$packagePath/ScheduleWidgetService.kt',
    );

    expect(service, contains('widgetTransitionDisplayIndex'));
    expect(service, contains('!it.id.startsWith(EMPTY_DAY_ID_PREFIX)'));
    expect(service, contains('val oldSharp = renderWidgetSlide'));
    expect(service, contains('val targetSharp = renderWidgetSlide'));
    expect(provider, contains('renderWidgetTransitionCover'));
    expect(provider, contains('setDisplayedChild'));
    expect(provider, contains('TARGET_COLLECTION_FALLBACK_MS'));
    expect(provider, contains('scheduleNormalRefreshCoverHide'));
    expect(provider, contains('TRANSITION_STALE_AFTER_MS'));
  });

  test('responsive StackView, peek mask, and Minecraft font guards remain', () {
    final provider = _read(
      '$platformRoot/$packagePath/ScheduleWidgetProvider.kt',
    );
    final service = _read(
      '$platformRoot/$packagePath/ScheduleWidgetService.kt',
    );
    final layout = _read('$platformRoot/res/layout/schedule_widget.xml');
    final itemLayout = _read(
      '$platformRoot/res/layout/schedule_widget_item.xml',
    );
    final info = _read('$platformRoot/res/xml/schedule_widget_info.xml');

    expect(provider, contains('exactWidgetSizes'));
    expect(provider, contains('buildSizeAwareViews'));
    expect(provider, contains('setViewLayoutWidth'));
    expect(provider, contains('setViewLayoutHeight'));
    expect(service, contains('CONTENT_LEFT_FRACTION'));
    expect(service, contains('R.font.minecraft_custom'));
    expect(File('assets/fonts/minecraft.ttf').lengthSync(), greaterThan(0));
    expect(
      File('$platformRoot/res/font/minecraft_custom.ttf').lengthSync(),
      greaterThan(0),
    );
    expect(layout, contains('android:loopViews="true"'));
    expect(layout, contains('android:id="@+id/widget_stack_peek_mask"'));
    final peekMask = layout.substring(
      layout.indexOf('android:id="@+id/widget_stack_peek_mask"'),
      layout.indexOf('android:id="@+id/widget_calendar"'),
    );
    expect(peekMask, contains('android:layout_width="match_parent"'));
    expect(peekMask, contains('android:layout_height="match_parent"'));
    expect(peekMask, isNot(contains('android:visibility="gone"')));
    expect(provider, contains('renderStackPeekMask'));
    expect(provider, contains('PEEK_MASK_HEIGHT_FRACTION'));
    expect(
      layout.indexOf('android:id="@+id/widget_empty"'),
      lessThan(layout.indexOf('android:id="@+id/widget_refresh_cover"')),
      reason: 'The refresh cover must stay above the empty-state view.',
    );
    expect(itemLayout, contains('android:background="@android:color/transparent"'));
    expect(itemLayout, contains('android:outlineProvider="none"'));
    expect(info, contains('android:minResizeWidth="220dp"'));
    expect(info, contains('android:resizeMode="horizontal"'));
  });

  test('generated Android widget sources mirror the canonical platform files', () {
    const mirroredFiles = <String>[
      '$packagePath/MainActivity.kt',
      '$packagePath/ScheduleWidgetProvider.kt',
      '$packagePath/ScheduleWidgetService.kt',
      'res/layout/schedule_widget.xml',
      'res/layout/schedule_widget_item.xml',
      'res/font/minecraft_custom.ttf',
      'res/xml/schedule_widget_info.xml',
    ];

    for (final relativePath in mirroredFiles) {
      expect(
        File('$androidRoot/$relativePath').readAsBytesSync(),
        File('$platformRoot/$relativePath').readAsBytesSync(),
        reason: '$relativePath is out of sync',
      );
    }
  });
}
