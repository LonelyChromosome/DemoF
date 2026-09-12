from __future__ import annotations

import base64
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEME_DART = r'''import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:home_widget/home_widget.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum AppThemeId {
  classic,
  lol,
  valorant,
  minecraft,
  facebook,
  shopee,
  tiktok,
  ben10,
  youtube,
  steam,
}

enum AppThemeGeometry { rounded, square, valorant, lol, pixel }

extension AppThemeIdUi on AppThemeId {
  String get storageKey => name;

  String get label => switch (this) {
    AppThemeId.classic => 'Better mặc định',
    AppThemeId.lol => 'League of Legends',
    AppThemeId.valorant => 'Valorant',
    AppThemeId.minecraft => 'Minecraft',
    AppThemeId.facebook => 'Facebook',
    AppThemeId.shopee => 'Shopee',
    AppThemeId.tiktok => 'TikTok',
    AppThemeId.ben10 => 'Ben 10',
    AppThemeId.youtube => 'YouTube',
    AppThemeId.steam => 'Steam',
  };

  String get caption => switch (this) {
    AppThemeId.classic => 'Sạch, xanh, quen thuộc',
    AppThemeId.lol => 'Hextech • vàng • lam ngọc',
    AppThemeId.valorant => 'Tactical • đỏ • góc cắt',
    AppThemeId.minecraft => 'Pixel • đất • nút khối',
    AppThemeId.facebook => 'Feed sáng • xanh Facebook',
    AppThemeId.shopee => 'Cam thương mại • card sáng',
    AppThemeId.tiktok => 'Đen • hồng • cyan',
    AppThemeId.ben10 => 'Omnitrix • đen • xanh neon',
    AppThemeId.youtube => 'Dark feed • đỏ video',
    AppThemeId.steam => 'Store dark • xanh Steam',
  };

  IconData get icon => switch (this) {
    AppThemeId.classic => Icons.check_rounded,
    AppThemeId.lol => Icons.auto_awesome_rounded,
    AppThemeId.valorant => Icons.change_history_rounded,
    AppThemeId.minecraft => Icons.view_in_ar_rounded,
    AppThemeId.facebook => Icons.facebook_rounded,
    AppThemeId.shopee => Icons.shopping_bag_rounded,
    AppThemeId.tiktok => Icons.music_note_rounded,
    AppThemeId.ben10 => Icons.watch_rounded,
    AppThemeId.youtube => Icons.play_circle_fill_rounded,
    AppThemeId.steam => Icons.sports_esports_rounded,
  };
}

@immutable
class AppThemePalette {
  const AppThemePalette({
    required this.id,
    required this.pageStart,
    required this.pageEnd,
    required this.surface,
    required this.card,
    required this.cardAlt,
    required this.primary,
    required this.accent,
    required this.textPrimary,
    required this.textSecondary,
    required this.border,
    required this.shadow,
    required this.widgetStart,
    required this.widgetEnd,
    required this.widgetText,
    required this.widgetSubtext,
    required this.radius,
    required this.geometry,
    required this.dark,
    this.fontFamily,
  });

  final AppThemeId id;
  final Color pageStart;
  final Color pageEnd;
  final Color surface;
  final Color card;
  final Color cardAlt;
  final Color primary;
  final Color accent;
  final Color textPrimary;
  final Color textSecondary;
  final Color border;
  final Color shadow;
  final Color widgetStart;
  final Color widgetEnd;
  final Color widgetText;
  final Color widgetSubtext;
  final double radius;
  final AppThemeGeometry geometry;
  final bool dark;
  final String? fontFamily;
}

const Map<AppThemeId, AppThemePalette> appThemePalettes = <AppThemeId, AppThemePalette>{
  AppThemeId.classic: AppThemePalette(
    id: AppThemeId.classic,
    pageStart: Color(0xFFF9FBFF),
    pageEnd: Color(0xFFF2F6FF),
    surface: Color(0xFFFFFFFF),
    card: Color(0xFFFFFFFF),
    cardAlt: Color(0xFFF3F6FC),
    primary: Color(0xFF1747B5),
    accent: Color(0xFF4A89FF),
    textPrimary: Color(0xFF102B73),
    textSecondary: Color(0xFF7180A0),
    border: Color(0xFFE8EDF7),
    shadow: Color(0x18193B80),
    widgetStart: Color(0xFF173A8E),
    widgetEnd: Color(0xFF315AB5),
    widgetText: Color(0xFFFFFFFF),
    widgetSubtext: Color(0xFFDDE8FF),
    radius: 14,
    geometry: AppThemeGeometry.rounded,
    dark: false,
  ),
  AppThemeId.lol: AppThemePalette(
    id: AppThemeId.lol,
    pageStart: Color(0xFF030B10),
    pageEnd: Color(0xFF071821),
    surface: Color(0xFF07161D),
    card: Color(0xFF0B1A21),
    cardAlt: Color(0xFF0F252D),
    primary: Color(0xFF0AC8B9),
    accent: Color(0xFFC89B3C),
    textPrimary: Color(0xFFF0E6D2),
    textSecondary: Color(0xFF9D947F),
    border: Color(0xFF785A28),
    shadow: Color(0x66000000),
    widgetStart: Color(0xFF06131A),
    widgetEnd: Color(0xFF0B343A),
    widgetText: Color(0xFFF0E6D2),
    widgetSubtext: Color(0xFFC8AA6E),
    radius: 2,
    geometry: AppThemeGeometry.lol,
    dark: true,
  ),
  AppThemeId.valorant: AppThemePalette(
    id: AppThemeId.valorant,
    pageStart: Color(0xFF0F1923),
    pageEnd: Color(0xFF111D27),
    surface: Color(0xFF111D27),
    card: Color(0xFF14222D),
    cardAlt: Color(0xFF1D2A34),
    primary: Color(0xFFFF4655),
    accent: Color(0xFFECE8E1),
    textPrimary: Color(0xFFECE8E1),
    textSecondary: Color(0xFF9AA7AD),
    border: Color(0xFF3A4A55),
    shadow: Color(0x66000000),
    widgetStart: Color(0xFF0F1923),
    widgetEnd: Color(0xFF24313B),
    widgetText: Color(0xFFECE8E1),
    widgetSubtext: Color(0xFFFF7B86),
    radius: 2,
    geometry: AppThemeGeometry.valorant,
    dark: true,
  ),
  AppThemeId.minecraft: AppThemePalette(
    id: AppThemeId.minecraft,
    pageStart: Color(0xFF5C3922),
    pageEnd: Color(0xFF352116),
    surface: Color(0xFF261D16),
    card: Color(0xFF30241B),
    cardAlt: Color(0xFF5D5D5D),
    primary: Color(0xFF8BC34A),
    accent: Color(0xFFFFFFFF),
    textPrimary: Color(0xFFFFFFFF),
    textSecondary: Color(0xFFD8D1C9),
    border: Color(0xFF0B0907),
    shadow: Color(0x77000000),
    widgetStart: Color(0xFF3A2B20),
    widgetEnd: Color(0xFF6B4A2F),
    widgetText: Color(0xFFFFFFFF),
    widgetSubtext: Color(0xFFD8D1C9),
    radius: 0,
    geometry: AppThemeGeometry.pixel,
    dark: true,
    fontFamily: 'MinecraftCustom',
  ),
  AppThemeId.facebook: AppThemePalette(
    id: AppThemeId.facebook,
    pageStart: Color(0xFFF0F2F5),
    pageEnd: Color(0xFFF0F2F5),
    surface: Color(0xFFF0F2F5),
    card: Color(0xFFFFFFFF),
    cardAlt: Color(0xFFE7F3FF),
    primary: Color(0xFF0866FF),
    accent: Color(0xFF0866FF),
    textPrimary: Color(0xFF050505),
    textSecondary: Color(0xFF65676B),
    border: Color(0xFFE4E6EB),
    shadow: Color(0x18000000),
    widgetStart: Color(0xFFFFFFFF),
    widgetEnd: Color(0xFFE7F3FF),
    widgetText: Color(0xFF050505),
    widgetSubtext: Color(0xFF65676B),
    radius: 16,
    geometry: AppThemeGeometry.rounded,
    dark: false,
  ),
  AppThemeId.shopee: AppThemePalette(
    id: AppThemeId.shopee,
    pageStart: Color(0xFFFFF5F1),
    pageEnd: Color(0xFFF7F7F7),
    surface: Color(0xFFF6F6F6),
    card: Color(0xFFFFFFFF),
    cardAlt: Color(0xFFFFE9E1),
    primary: Color(0xFFEE4D2D),
    accent: Color(0xFFFF8B5E),
    textPrimary: Color(0xFF222222),
    textSecondary: Color(0xFF777777),
    border: Color(0xFFEAEAEA),
    shadow: Color(0x16000000),
    widgetStart: Color(0xFFEE4D2D),
    widgetEnd: Color(0xFFFF6A3D),
    widgetText: Color(0xFFFFFFFF),
    widgetSubtext: Color(0xFFFFE9E1),
    radius: 15,
    geometry: AppThemeGeometry.rounded,
    dark: false,
  ),
  AppThemeId.tiktok: AppThemePalette(
    id: AppThemeId.tiktok,
    pageStart: Color(0xFF000000),
    pageEnd: Color(0xFF111111),
    surface: Color(0xFF0A0A0A),
    card: Color(0xFF202020),
    cardAlt: Color(0xFF2A2A2A),
    primary: Color(0xFFFE2C55),
    accent: Color(0xFF25F4EE),
    textPrimary: Color(0xFFFFFFFF),
    textSecondary: Color(0xFFB8B8B8),
    border: Color(0xFF343434),
    shadow: Color(0x77000000),
    widgetStart: Color(0xFF111111),
    widgetEnd: Color(0xFF2A1520),
    widgetText: Color(0xFFFFFFFF),
    widgetSubtext: Color(0xFF25F4EE),
    radius: 14,
    geometry: AppThemeGeometry.rounded,
    dark: true,
  ),
  AppThemeId.ben10: AppThemePalette(
    id: AppThemeId.ben10,
    pageStart: Color(0xFF050805),
    pageEnd: Color(0xFF142016),
    surface: Color(0xFF101510),
    card: Color(0xFF182018),
    cardAlt: Color(0xFF243126),
    primary: Color(0xFF39D353),
    accent: Color(0xFF7CFF00),
    textPrimary: Color(0xFFF5FFF5),
    textSecondary: Color(0xFFA8B8A9),
    border: Color(0xFF315637),
    shadow: Color(0x77000000),
    widgetStart: Color(0xFF101510),
    widgetEnd: Color(0xFF1D5F22),
    widgetText: Color(0xFFFFFFFF),
    widgetSubtext: Color(0xFF7CFF00),
    radius: 18,
    geometry: AppThemeGeometry.rounded,
    dark: true,
  ),
  AppThemeId.youtube: AppThemePalette(
    id: AppThemeId.youtube,
    pageStart: Color(0xFF0F0F0F),
    pageEnd: Color(0xFF151515),
    surface: Color(0xFF0F0F0F),
    card: Color(0xFF212121),
    cardAlt: Color(0xFF272727),
    primary: Color(0xFFFF0033),
    accent: Color(0xFFFFFFFF),
    textPrimary: Color(0xFFF1F1F1),
    textSecondary: Color(0xFFAAAAAA),
    border: Color(0xFF303030),
    shadow: Color(0x77000000),
    widgetStart: Color(0xFF181818),
    widgetEnd: Color(0xFF2B0E14),
    widgetText: Color(0xFFFFFFFF),
    widgetSubtext: Color(0xFFFF8A9F),
    radius: 14,
    geometry: AppThemeGeometry.rounded,
    dark: true,
  ),
  AppThemeId.steam: AppThemePalette(
    id: AppThemeId.steam,
    pageStart: Color(0xFF0E141B),
    pageEnd: Color(0xFF162536),
    surface: Color(0xFF171D25),
    card: Color(0xFF1B2838),
    cardAlt: Color(0xFF22384A),
    primary: Color(0xFF66C0F4),
    accent: Color(0xFF1A9FFF),
    textPrimary: Color(0xFFD6E9F8),
    textSecondary: Color(0xFF8F98A0),
    border: Color(0xFF2A475E),
    shadow: Color(0x66000000),
    widgetStart: Color(0xFF171D25),
    widgetEnd: Color(0xFF1B3D55),
    widgetText: Color(0xFFD6E9F8),
    widgetSubtext: Color(0xFF66C0F4),
    radius: 4,
    geometry: AppThemeGeometry.square,
    dark: true,
  ),
};

AppThemePalette get appThemePalette =>
    appThemePalettes[AppThemeController.instance.theme] ?? appThemePalettes[AppThemeId.classic]!;

class AppThemeController extends ChangeNotifier {
  AppThemeController._();

  static final AppThemeController instance = AppThemeController._();
  static const _preferenceKey = 'better_phenikaa_theme_v2';

  AppThemeId _theme = AppThemeId.classic;
  bool _loaded = false;

  AppThemeId get theme => _theme;
  AppThemePalette get palette => appThemePalettes[_theme]!;

  Future<void> load() async {
    if (_loaded) return;
    _loaded = true;
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_preferenceKey);
    if (saved != null) {
      for (final candidate in AppThemeId.values) {
        if (candidate.storageKey == saved) {
          _theme = candidate;
          break;
        }
      }
    }
    notifyListeners();
    await _syncWidgetTheme();
  }

  Future<void> select(AppThemeId value) async {
    if (_theme == value) return;
    _theme = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_preferenceKey, value.storageKey);
    await _syncWidgetTheme();
  }

  Future<void> _syncWidgetTheme() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return;
    await HomeWidget.saveWidgetData<String>('appTheme', _theme.storageKey);
    await HomeWidget.updateWidget(
      name: 'ScheduleWidgetProvider',
      androidName: 'ScheduleWidgetProvider',
    );
  }
}

ThemeData buildBetterTheme(AppThemePalette palette) {
  final brightness = palette.dark ? Brightness.dark : Brightness.light;
  final base = ThemeData(
    useMaterial3: true,
    brightness: brightness,
    fontFamily: palette.fontFamily ?? 'Roboto',
  );
  final shape = themeButtonShape(palette);
  return base.copyWith(
    scaffoldBackgroundColor: palette.surface,
    colorScheme: ColorScheme.fromSeed(
      seedColor: palette.primary,
      brightness: brightness,
    ).copyWith(
      primary: palette.primary,
      secondary: palette.accent,
      surface: palette.surface,
      onSurface: palette.textPrimary,
    ),
    textTheme: base.textTheme.apply(
      fontFamily: palette.fontFamily ?? 'Roboto',
      bodyColor: palette.textPrimary,
      displayColor: palette.textPrimary,
    ),
    iconTheme: IconThemeData(color: palette.textPrimary),
    cardTheme: CardThemeData(
      color: palette.card,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(palette.radius),
        side: BorderSide(color: palette.border),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: palette.primary,
        foregroundColor: palette.dark && palette.id != AppThemeId.lol
            ? Colors.white
            : palette.id == AppThemeId.lol
            ? const Color(0xFF06171D)
            : Colors.white,
        shape: shape,
        textStyle: TextStyle(
          fontWeight: FontWeight.w800,
          letterSpacing: themeLetterSpacing(palette),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: palette.primary,
        side: BorderSide(color: palette.border),
        shape: shape,
      ),
    ),
    dividerColor: palette.border,
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: palette.surface,
      modalBackgroundColor: palette.surface,
    ),
  );
}

OutlinedBorder themeButtonShape(AppThemePalette palette) {
  return switch (palette.geometry) {
    AppThemeGeometry.valorant => const BeveledRectangleBorder(
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(10),
        bottomRight: Radius.circular(10),
      ),
    ),
    AppThemeGeometry.lol => const BeveledRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(12)),
    ),
    AppThemeGeometry.pixel || AppThemeGeometry.square => const RoundedRectangleBorder(),
    AppThemeGeometry.rounded => RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(palette.radius),
    ),
  };
}

double themeLetterSpacing(AppThemePalette palette) => switch (palette.id) {
  AppThemeId.valorant => .85,
  AppThemeId.lol => .65,
  AppThemeId.minecraft => .15,
  _ => 0,
};

String themedHeading(String value, AppThemePalette palette) =>
    palette.id == AppThemeId.valorant ? value.toUpperCase() : value;

class AppThemeBackdrop extends StatelessWidget {
  const AppThemeBackdrop({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _ThemeBackdropPainter(appThemePalette),
      child: SizedBox.expand(child: child),
    );
  }
}

class _ThemeBackdropPainter extends CustomPainter {
  const _ThemeBackdropPainter(this.palette);

  final AppThemePalette palette;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final base = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: <Color>[palette.pageStart, palette.pageEnd],
      ).createShader(rect);
    canvas.drawRect(rect, base);

    switch (palette.id) {
      case AppThemeId.minecraft:
        final block = (size.shortestSide / 11).clamp(26.0, 48.0);
        final paint = Paint();
        for (var y = 0.0; y < size.height; y += block) {
          for (var x = 0.0; x < size.width; x += block) {
            final index = ((x / block).floor() + (y / block).floor()) % 4;
            paint.color = <Color>[
              const Color(0xFF5A3824),
              const Color(0xFF6A4229),
              const Color(0xFF4C2D1C),
              const Color(0xFF765037),
            ][index];
            canvas.drawRect(Rect.fromLTWH(x, y, block + .5, block + .5), paint);
          }
        }
        paint.color = const Color(0xFF5D963E).withValues(alpha: .55);
        canvas.drawRect(Rect.fromLTWH(0, 0, size.width, block * .28), paint);
      case AppThemeId.valorant:
        final paint = Paint()..color = palette.primary.withValues(alpha: .13);
        final path = Path()
          ..moveTo(size.width * .62, 0)
          ..lineTo(size.width, 0)
          ..lineTo(size.width, size.height * .31)
          ..close();
        canvas.drawPath(path, paint);
        final path2 = Path()
          ..moveTo(0, size.height * .78)
          ..lineTo(size.width * .26, size.height)
          ..lineTo(0, size.height)
          ..close();
        canvas.drawPath(path2, paint);
      case AppThemeId.lol:
        final glow = Paint()
          ..shader = RadialGradient(
            colors: <Color>[
              palette.primary.withValues(alpha: .18),
              Colors.transparent,
            ],
          ).createShader(
            Rect.fromCircle(
              center: Offset(size.width * .5, size.height * .08),
              radius: size.width * .55,
            ),
          );
        canvas.drawRect(rect, glow);
        final line = Paint()
          ..color = palette.accent.withValues(alpha: .16)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.2;
        canvas.drawCircle(Offset(size.width * .5, size.height * .12), size.width * .31, line);
      case AppThemeId.tiktok:
        final pink = Paint()..color = palette.primary.withValues(alpha: .08);
        final cyan = Paint()..color = palette.accent.withValues(alpha: .07);
        canvas.drawCircle(Offset(size.width * .9, size.height * .18), size.width * .36, pink);
        canvas.drawCircle(Offset(size.width * .05, size.height * .76), size.width * .3, cyan);
      case AppThemeId.ben10:
        final ring = Paint()
          ..color = palette.accent.withValues(alpha: .10)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 10;
        canvas.drawCircle(Offset(size.width * .86, size.height * .12), size.width * .22, ring);
      case AppThemeId.youtube:
        final glow = Paint()..color = palette.primary.withValues(alpha: .07);
        canvas.drawCircle(Offset(size.width * .52, 0), size.width * .55, glow);
      case AppThemeId.steam:
        final glow = Paint()
          ..shader = LinearGradient(
            colors: <Color>[
              Colors.transparent,
              palette.primary.withValues(alpha: .11),
            ],
          ).createShader(rect);
        canvas.drawRect(rect, glow);
      case AppThemeId.shopee:
        final band = Paint()..color = palette.primary.withValues(alpha: .10);
        canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height * .14), band);
      case AppThemeId.facebook:
      case AppThemeId.classic:
        break;
    }
  }

  @override
  bool shouldRepaint(covariant _ThemeBackdropPainter oldDelegate) =>
      oldDelegate.palette.id != palette.id;
}

class AppThemePanel extends StatelessWidget {
  const AppThemePanel({
    required this.child,
    this.padding,
    this.width,
    this.constraints,
    this.alt = false,
    this.elevated = true,
    super.key,
  });

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double? width;
  final BoxConstraints? constraints;
  final bool alt;
  final bool elevated;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    final decoration = BoxDecoration(
      color: alt ? palette.cardAlt : palette.card,
      border: Border.all(
        color: palette.border,
        width: palette.geometry == AppThemeGeometry.pixel ? 3 : 1,
      ),
      borderRadius: palette.geometry == AppThemeGeometry.rounded
          ? BorderRadius.circular(palette.radius)
          : BorderRadius.zero,
      boxShadow: elevated
          ? <BoxShadow>[
              BoxShadow(
                color: palette.shadow,
                blurRadius: palette.geometry == AppThemeGeometry.pixel ? 0 : 18,
                offset: palette.geometry == AppThemeGeometry.pixel
                    ? const Offset(4, 4)
                    : const Offset(0, 6),
              ),
            ]
          : null,
    );
    final box = Container(
      width: width,
      constraints: constraints,
      padding: padding,
      decoration: decoration,
      child: child,
    );
    return switch (palette.geometry) {
      AppThemeGeometry.valorant => ClipPath(
        clipper: const _ValorantClipper(),
        child: box,
      ),
      AppThemeGeometry.lol => ClipPath(
        clipper: const _LolClipper(),
        child: box,
      ),
      _ => box,
    };
  }
}

class _ValorantClipper extends CustomClipper<Path> {
  const _ValorantClipper();

  @override
  Path getClip(Size size) {
    const cut = 12.0;
    return Path()
      ..moveTo(cut, 0)
      ..lineTo(size.width, 0)
      ..lineTo(size.width, size.height - cut)
      ..lineTo(size.width - cut, size.height)
      ..lineTo(0, size.height)
      ..lineTo(0, cut)
      ..close();
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

class _LolClipper extends CustomClipper<Path> {
  const _LolClipper();

  @override
  Path getClip(Size size) {
    const cut = 11.0;
    return Path()
      ..moveTo(cut, 0)
      ..lineTo(size.width - cut, 0)
      ..lineTo(size.width, cut)
      ..lineTo(size.width, size.height - cut)
      ..lineTo(size.width - cut, size.height)
      ..lineTo(cut, size.height)
      ..lineTo(0, size.height - cut)
      ..lineTo(0, cut)
      ..close();
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

Future<void> showAppThemePicker(BuildContext context) async {
  final controller = AppThemeController.instance;
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    barrierColor: const Color(0x99000000),
    builder: (context) => AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final palette = controller.palette;
        final radius = palette.geometry == AppThemeGeometry.rounded ? 28.0 : 0.0;
        return SafeArea(
          top: false,
          child: Container(
            constraints: BoxConstraints(
              maxHeight: MediaQuery.sizeOf(context).height * .78,
            ),
            padding: const EdgeInsets.fromLTRB(18, 12, 18, 20),
            decoration: BoxDecoration(
              color: palette.surface,
              border: Border(top: BorderSide(color: palette.border)),
              borderRadius: BorderRadius.vertical(top: Radius.circular(radius)),
              boxShadow: <BoxShadow>[
                BoxShadow(color: palette.shadow, blurRadius: 32, offset: const Offset(0, -8)),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Center(
                  child: Container(
                    width: 44,
                    height: 5,
                    margin: const EdgeInsets.only(bottom: 14),
                    decoration: BoxDecoration(
                      color: palette.textSecondary.withValues(alpha: .35),
                      borderRadius: BorderRadius.circular(99),
                    ),
                  ),
                ),
                Text(
                  'Giao diện',
                  style: TextStyle(
                    color: palette.textPrimary,
                    fontSize: 21,
                    fontWeight: FontWeight.w900,
                    letterSpacing: themeLetterSpacing(palette),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Đổi skin cho toàn bộ app và widget. Lịch và dữ liệu không thay đổi.',
                  style: TextStyle(color: palette.textSecondary, fontSize: 12.5, height: 1.35),
                ),
                const SizedBox(height: 16),
                Flexible(
                  child: GridView.builder(
                    shrinkWrap: true,
                    physics: const BouncingScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 1.45,
                    ),
                    itemCount: AppThemeId.values.length,
                    itemBuilder: (context, index) {
                      final id = AppThemeId.values[index];
                      final preview = appThemePalettes[id]!;
                      final selected = controller.theme == id;
                      return InkWell(
                        onTap: () => controller.select(id),
                        borderRadius: BorderRadius.circular(14),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 220),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: palette.card,
                            borderRadius: BorderRadius.circular(
                              palette.geometry == AppThemeGeometry.rounded ? 14 : 2,
                            ),
                            border: Border.all(
                              color: selected ? palette.primary : palette.border,
                              width: selected ? 2 : 1,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Expanded(
                                child: Container(
                                  width: double.infinity,
                                  decoration: BoxDecoration(
                                    gradient: LinearGradient(
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                      colors: <Color>[
                                        preview.pageStart,
                                        preview.primary,
                                        preview.accent,
                                      ],
                                    ),
                                    borderRadius: BorderRadius.circular(
                                      preview.geometry == AppThemeGeometry.rounded ? 9 : 1,
                                    ),
                                  ),
                                  child: Align(
                                    alignment: Alignment.topRight,
                                    child: Padding(
                                      padding: const EdgeInsets.all(7),
                                      child: Icon(
                                        selected ? Icons.check_circle_rounded : id.icon,
                                        color: preview.widgetText,
                                        size: 19,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                id.label,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  color: palette.textPrimary,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 12.5,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                id.caption,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(color: palette.textSecondary, fontSize: 10),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    ),
  );
}

class AppThemeSettingButton extends StatelessWidget {
  const AppThemeSettingButton({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = AppThemeController.instance;
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
              child: Icon(controller.theme.icon, color: palette.widgetText, size: 21),
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
                    style: TextStyle(color: palette.textSecondary, fontSize: 11.5),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: palette.textSecondary),
          ],
        ),
      ),
    );
  }
}
'''


def replace_section(text: str, start: str, end: str, replacement: str) -> str:
    i = text.find(start)
    if i < 0:
        raise RuntimeError(f'missing start marker: {start}')
    j = text.find(end, i)
    if j < 0:
        raise RuntimeError(f'missing end marker: {end}')
    return text[:i] + replacement.rstrip() + '\n\n' + text[j:]


def write_theme_file() -> None:
    path = ROOT / 'lib/theme/app_theme.dart'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(THEME_DART, encoding='utf-8')


def rewrite_app() -> None:
    path = ROOT / 'lib/app/app.dart'
    text = path.read_text(encoding='utf-8')
    import_line = "import 'package:better_phenikaa_schedule/theme/app_theme.dart';\n"
    if import_line not in text:
        text = text.replace(
            "import 'package:better_phenikaa_schedule/features/qldt_intake/qldt_models.dart';\n",
            "import 'package:better_phenikaa_schedule/features/qldt_intake/qldt_models.dart';\n" + import_line,
            1,
        )

    text = replace_section(text, 'class BetterPhenikaaScheduleApp', 'enum _AppPage', r'''class BetterPhenikaaScheduleApp extends StatefulWidget {
  const new({super.key});

  @override
  State<BetterPhenikaaScheduleApp> createState() => _BetterPhenikaaScheduleAppState();
}

class _BetterPhenikaaScheduleAppState extends State<BetterPhenikaaScheduleApp> {
  final AppThemeController _themes = AppThemeController.instance;

  @override
  void initState() {
    super.initState();
    unawaited(_themes.load());
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _themes,
      builder: (context, _) {
        final palette = _themes.palette;
        return MaterialApp(
          title: 'Better Phenikaa App',
          debugShowCheckedModeBanner: false,
          theme: buildBetterTheme(palette),
          home: const _AppRoot(),
        );
      },
    );
  }
}''')

    # Theme the outer phone shell without touching navigation/data logic.
    old_root = r'''  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[Color(0xFFF9FBFF), Color(0xFFF2F6FF)],
          ),
        ),
        child: SafeArea('''
    new_root = r'''  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: AppThemeBackdrop(
        child: SafeArea('''
    if old_root not in text:
        raise RuntimeError('root scaffold marker changed')
    text = text.replace(old_root, new_root, 1)
    text = text.replace(
        '                      color: Colors.white,\n                      borderRadius: BorderRadius.circular(desktop ? 28 : 0),',
        '                      color: palette.surface.withValues(alpha: desktop ? .98 : .94),\n                      borderRadius: BorderRadius.circular(desktop && palette.geometry == AppThemeGeometry.rounded ? 28 : 0),',
        1,
    )
    # DecoratedBox -> backdrop removed one wrapper but closing count is already identical.

    text = replace_section(text, 'class _SplashScreen', 'class _LoginScreen', r'''class _SplashScreen extends StatelessWidget {
  const new();

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return _PhoneSurface(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const _AppMark(size: 76),
          const SizedBox(height: 26),
          Text(
            themedHeading('Better Phenikaa App', palette),
            style: TextStyle(
              color: palette.textPrimary,
              fontSize: 30,
              fontWeight: FontWeight.w900,
              letterSpacing: themeLetterSpacing(palette),
            ),
          ),
          const SizedBox(height: 7),
          Text(
            '2.0 • Lịch học & Lịch thi',
            style: TextStyle(color: palette.textSecondary, fontSize: 15),
          ),
          const SizedBox(height: 120),
          SizedBox(
            width: 88,
            child: LinearProgressIndicator(
              minHeight: palette.geometry == AppThemeGeometry.pixel ? 6 : 4,
              borderRadius: BorderRadius.all(
                Radius.circular(palette.geometry == AppThemeGeometry.rounded ? 10 : 0),
              ),
              backgroundColor: palette.cardAlt,
              color: palette.primary,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Đang khởi động...',
            style: TextStyle(color: palette.textSecondary, fontSize: 12),
          ),
        ],
      ),
    );
  }
}''')

    text = replace_section(text, 'class _LoginScreen', 'class _MainShell', r'''class _LoginScreen extends StatelessWidget {
  const new({required this.onLogin, required this.supportsLive});

  final VoidCallback onLogin;
  final bool supportsLive;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return _PhoneSurface(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(32, 58, 32, 30),
        child: Column(
          children: <Widget>[
            const Spacer(),
            const _AppMark(size: 62),
            const SizedBox(height: 22),
            Text(
              themedHeading('Chào mừng bạn!', palette),
              style: TextStyle(
                color: palette.textPrimary,
                fontSize: 28,
                fontWeight: FontWeight.w900,
                letterSpacing: themeLetterSpacing(palette),
              ),
            ),
            const SizedBox(height: 14),
            Text(
              'Kết nối với QLĐT để xem lịch học và lịch thi của bạn',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: palette.textSecondary,
                height: 1.55,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 38),
            SizedBox(
              width: double.infinity,
              height: 62,
              child: FilledButton(
                onPressed: onLogin,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    const _MicrosoftMark(),
                    const SizedBox(width: 14),
                    Text(
                      supportsLive
                          ? 'Đăng nhập QLĐT\n(Microsoft)'
                          : 'Đăng nhập QLĐT thật\n(Android APK)',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 22),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                Icon(Icons.lock_outline, size: 17, color: palette.textSecondary),
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    'Dữ liệu chỉ lưu cục bộ trên thiết bị của bạn',
                    style: TextStyle(color: palette.textSecondary, fontSize: 12),
                  ),
                ),
              ],
            ),
            const Spacer(flex: 2),
            Text(
              'Better Phenikaa App • ${AppThemeController.instance.theme.label}',
              style: TextStyle(
                color: palette.textSecondary,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}''')

    text = replace_section(text, 'class _MainShell', 'class _TimetableScreen', r'''class _MainShell extends StatelessWidget {
  const new({
    required this.data,
    required this.page,
    required this.selectedDate,
    required this.showPastExams,
    required this.panelOpen,
    required this.syncing,
    required this.errorMessage,
    required this.onTogglePanel,
    required this.onOpenPage,
    required this.onSync,
    required this.onLogout,
    required this.onDateChanged,
    required this.onExamTabChanged,
    required this.onDismissError,
  });

  final ImportedScheduleData data;
  final _AppPage page;
  final DateTime selectedDate;
  final bool showPastExams;
  final bool panelOpen;
  final bool syncing;
  final String? errorMessage;
  final VoidCallback onTogglePanel;
  final ValueChanged<_AppPage> onOpenPage;
  final VoidCallback onSync;
  final VoidCallback onLogout;
  final ValueChanged<DateTime> onDateChanged;
  final ValueChanged<bool> onExamTabChanged;
  final VoidCallback onDismissError;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    final child = switch (page) {
      _AppPage.timetable => _TimetableScreen(
        data: data,
        selectedDate: selectedDate,
        onDateChanged: onDateChanged,
      ),
      _AppPage.exam => _ExamScreen(
        data: data,
        showPast: showPastExams,
        onTabChanged: onExamTabChanged,
      ),
      _AppPage.account => _AccountScreen(
        data: data,
        onLogout: onLogout,
        onSync: onSync,
      ),
    };

    return _PhoneSurface(
      child: Stack(
        children: <Widget>[
          Positioned.fill(child: child),
          if (errorMessage != null)
            Positioned(
              left: 16,
              right: 16,
              top: 14,
              child: _ErrorBanner(
                message: errorMessage!,
                onDismiss: onDismissError,
              ),
            ),
          if (syncing)
            Positioned(
              left: 0,
              right: 0,
              top: 0,
              child: LinearProgressIndicator(minHeight: 3, color: palette.primary),
            ),
          if (panelOpen)
            Positioned.fill(
              child: GestureDetector(
                onTap: onTogglePanel,
                child: Container(color: Colors.black.withValues(alpha: .48)),
              ),
            ),
          if (panelOpen)
            Positioned(
              right: 10,
              bottom: 78,
              child: _ControlPanel(
                page: page,
                onOpenPage: onOpenPage,
                onSync: onSync,
              ),
            ),
          Positioned(
            right: 22,
            bottom: 28,
            child: FloatingActionButton(
              heroTag: 'control-panel',
              onPressed: onTogglePanel,
              backgroundColor: palette.primary,
              foregroundColor: palette.id == AppThemeId.lol
                  ? const Color(0xFF06171D)
                  : Colors.white,
              elevation: palette.geometry == AppThemeGeometry.pixel ? 0 : 8,
              shape: themeButtonShape(palette),
              child: AnimatedRotation(
                turns: panelOpen ? .125 : 0,
                duration: const Duration(milliseconds: 260),
                curve: Curves.easeOutCubic,
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 180),
                  child: Icon(
                    panelOpen ? Icons.close : Icons.grid_view_rounded,
                    key: ValueKey<bool>(panelOpen),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}''')

    text = replace_section(text, 'class _AccountScreen', 'class _TopTitle', r'''class _AccountScreen extends StatelessWidget {
  const new({required this.data, required this.onLogout, required this.onSync});

  final ImportedScheduleData data;
  final VoidCallback onLogout;
  final VoidCallback onSync;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    final next = _nextForAccount(data);
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 26, 22, 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _TopTitle(title: 'Tài khoản', badge: null),
          const SizedBox(height: 26),
          Row(
            children: <Widget>[
              CircleAvatar(
                radius: 38,
                backgroundColor: palette.primary,
                child: Icon(
                  Icons.person_rounded,
                  color: palette.id == AppThemeId.lol ? const Color(0xFF06171D) : Colors.white,
                  size: 48,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                child: Text(
                  data.displayName.isEmpty ? 'Người dùng QLĐT' : data.displayName,
                  style: TextStyle(
                    color: palette.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    letterSpacing: themeLetterSpacing(palette),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _InfoPanel(data: data),
          const SizedBox(height: 12),
          const AppThemeSettingButton(),
          const SizedBox(height: 12),
          if (next != null) _WidgetPreview(item: next),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton.icon(
              onPressed: onSync,
              icon: const Icon(Icons.sync_rounded),
              label: const Text('Đồng bộ lại QLĐT'),
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: OutlinedButton.icon(
              onPressed: onLogout,
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFFE55656),
                side: const BorderSide(color: Color(0xFFFF7777)),
                shape: themeButtonShape(palette),
              ),
              icon: const Icon(Icons.logout_rounded, size: 19),
              label: const Text('Đăng xuất', style: TextStyle(fontWeight: FontWeight.w700)),
            ),
          ),
          const SizedBox(height: 76),
        ],
      ),
    );
  }

  static ScheduleRecord? _nextForAccount(ImportedScheduleData data) {
    if (data.classes.isEmpty) return null;
    final reference = DateTime.now();
    final items = data.classes.where((record) => !record.endAt.isBefore(reference)).toList()
      ..sort((a, b) => a.startAt.compareTo(b.startAt));
    return items.isEmpty ? null : items.first;
  }
}''')

    text = replace_section(text, 'class _TopTitle', 'class _DateNavigator', r'''class _TopTitle extends StatelessWidget {
  const new({required this.title, this.badge, this.onCalendarTap});

  final String title;
  final String? badge;
  final VoidCallback? onCalendarTap;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Row(
      children: <Widget>[
        Text(
          themedHeading(title, palette),
          style: TextStyle(
            color: palette.textPrimary,
            fontSize: 25,
            fontWeight: FontWeight.w900,
            letterSpacing: themeLetterSpacing(palette),
          ),
        ),
        if (badge != null) ...<Widget>[
          const SizedBox(width: 9),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
            decoration: BoxDecoration(
              color: palette.cardAlt,
              borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 999 : 0),
              border: Border.all(color: palette.border),
            ),
            child: Text(
              badge!,
              style: TextStyle(color: palette.primary, fontSize: 10, fontWeight: FontWeight.w800),
            ),
          ),
        ],
        const Spacer(),
        if (onCalendarTap == null)
          Icon(Icons.calendar_month_outlined, color: palette.primary)
        else
          IconButton.filledTonal(
            tooltip: 'Chọn ngày',
            onPressed: onCalendarTap,
            style: IconButton.styleFrom(
              foregroundColor: palette.primary,
              backgroundColor: palette.cardAlt,
              shape: themeButtonShape(palette),
            ),
            icon: const Icon(Icons.calendar_month_outlined),
          ),
      ],
    );
  }
}''')

    text = replace_section(text, 'class _DateNavigator', 'Future<void> _showCalendarPicker', r'''class _DateNavigator extends StatelessWidget {
  const new({
    required this.date,
    required this.onTap,
    required this.onPrevious,
    required this.onNext,
  });

  final DateTime date;
  final VoidCallback onTap;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Row(
      children: <Widget>[
        IconButton(onPressed: onPrevious, icon: Icon(Icons.chevron_left_rounded, color: palette.textSecondary)),
        Expanded(
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 18 : 0),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Flexible(
                    child: Text(
                      _dateLabel(date),
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: palette.textPrimary, fontWeight: FontWeight.w800),
                    ),
                  ),
                  const SizedBox(width: 7),
                  Icon(Icons.expand_more_rounded, size: 18, color: palette.textSecondary),
                ],
              ),
            ),
          ),
        ),
        IconButton(onPressed: onNext, icon: Icon(Icons.chevron_right_rounded, color: palette.textSecondary)),
      ],
    );
  }
}''')

    text = replace_section(text, 'Future<void> _showCalendarPicker', 'class _ScheduleCard', r'''Future<void> _showCalendarPicker(
  BuildContext context,
  DateTime selectedDate,
  ValueChanged<DateTime> onDateChanged,
) async {
  var draft = _dateOnly(selectedDate);
  final palette = appThemePalette;
  final picked = await showModalBottomSheet<DateTime>(
    context: context,
    isScrollControlled: true,
    showDragHandle: false,
    backgroundColor: Colors.transparent,
    barrierColor: Colors.black.withValues(alpha: .48),
    builder: (context) {
      return StatefulBuilder(
        builder: (context, setModalState) {
          return TweenAnimationBuilder<double>(
            tween: Tween<double>(begin: .94, end: 1),
            duration: const Duration(milliseconds: 280),
            curve: Curves.easeOutBack,
            builder: (context, value, child) => Transform.scale(
              alignment: Alignment.bottomCenter,
              scale: value,
              child: child,
            ),
            child: SafeArea(
              top: false,
              child: Container(
                padding: const EdgeInsets.fromLTRB(18, 10, 18, 18),
                decoration: BoxDecoration(
                  color: palette.surface,
                  border: Border(top: BorderSide(color: palette.border)),
                  borderRadius: BorderRadius.vertical(
                    top: Radius.circular(palette.geometry == AppThemeGeometry.rounded ? 30 : 0),
                  ),
                  boxShadow: <BoxShadow>[
                    BoxShadow(color: palette.shadow, blurRadius: 28, offset: const Offset(0, -6)),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Container(
                      width: 42,
                      height: 5,
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: palette.textSecondary.withValues(alpha: .35),
                        borderRadius: BorderRadius.circular(99),
                      ),
                    ),
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            'Chọn ngày xem lịch',
                            style: TextStyle(color: palette.textPrimary, fontSize: 18, fontWeight: FontWeight.w900),
                          ),
                        ),
                        TextButton(
                          onPressed: () => setModalState(() => draft = _dateOnly(DateTime.now())),
                          child: const Text('Hôm nay'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Theme(
                      data: buildBetterTheme(palette),
                      child: CalendarDatePicker(
                        initialDate: draft,
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2035, 12, 31),
                        onDateChanged: (value) => setModalState(() => draft = _dateOnly(value)),
                      ),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: FilledButton.icon(
                        onPressed: () => Navigator.of(context).pop(draft),
                        icon: const Icon(Icons.check_rounded),
                        label: Text('Xem ${_dateLabel(draft)}'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      );
    },
  );
  if (picked != null) onDateChanged(_dateOnly(picked));
}''')

    text = replace_section(text, 'class _ScheduleCard', 'class _ExamCard', r'''class _ScheduleCard extends StatelessWidget {
  const new({required this.item, required this.accent});

  final ScheduleRecord item;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    final barColor = palette.id == AppThemeId.classic ? accent : palette.primary;
    return AppThemePanel(
      constraints: const BoxConstraints(minHeight: 106),
      child: Row(
        children: <Widget>[
          Container(
            width: palette.geometry == AppThemeGeometry.pixel ? 6 : 4,
            color: barColor,
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            child: Text(
              _time(item.startAt),
              style: TextStyle(color: palette.primary, fontWeight: FontWeight.w900, fontSize: 17),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(4, 14, 14, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Text(
                    item.subjectName,
                    style: TextStyle(color: palette.textPrimary, fontWeight: FontWeight.w900, fontSize: 16),
                  ),
                  if (item.room.isNotEmpty) ...<Widget>[
                    const SizedBox(height: 8),
                    _MetaLine(icon: Icons.location_on_outlined, text: item.room),
                  ],
                  const SizedBox(height: 5),
                  _MetaLine(icon: Icons.access_time_rounded, text: '${_time(item.startAt)} - ${_time(item.endAt)}'),
                  if (item.periodStart != null && item.periodEnd != null) ...<Widget>[
                    const SizedBox(height: 5),
                    _MetaLine(icon: Icons.menu_book_outlined, text: 'Tiết ${item.periodStart} - ${item.periodEnd}'),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}''')

    text = replace_section(text, 'class _ExamCard', 'class _SegmentTabs', r'''class _ExamCard extends StatelessWidget {
  const new({required this.item});

  final ScheduleRecord item;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return AppThemePanel(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: <Widget>[
          Container(
            width: 58,
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: palette.cardAlt,
              border: Border.all(color: palette.border),
              borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 10 : 0),
            ),
            child: Column(
              children: <Widget>[
                Text(
                  item.startAt.day.toString().padLeft(2, '0'),
                  style: TextStyle(color: palette.primary, fontSize: 20, fontWeight: FontWeight.w900),
                ),
                Text('THG ${item.startAt.month}', style: TextStyle(color: palette.textSecondary, fontSize: 10)),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(item.subjectName, style: TextStyle(color: palette.textPrimary, fontWeight: FontWeight.w900)),
                if (item.examForm.isNotEmpty) ...<Widget>[
                  const SizedBox(height: 4),
                  Text(item.examForm, style: TextStyle(color: palette.accent, fontSize: 11)),
                ],
                const SizedBox(height: 7),
                _MetaLine(icon: Icons.access_time_rounded, text: '${_time(item.startAt)} - ${_time(item.endAt)}'),
                if (item.room.isNotEmpty) ...<Widget>[
                  const SizedBox(height: 4),
                  _MetaLine(icon: Icons.location_on_outlined, text: item.room),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}''')

    text = replace_section(text, 'class _SegmentTabs', 'class _TabButton', r'''class _SegmentTabs extends StatelessWidget {
  const new({required this.showPast, required this.onChanged});

  final bool showPast;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Container(
      height: 43,
      decoration: BoxDecoration(
        color: palette.cardAlt,
        border: Border.all(color: palette.border),
        borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 11 : 0),
      ),
      child: Row(
        children: <Widget>[
          Expanded(child: _TabButton(label: 'Sắp tới', selected: !showPast, onTap: () => onChanged(false))),
          Expanded(child: _TabButton(label: 'Đã qua', selected: showPast, onTap: () => onChanged(true))),
        ],
      ),
    );
  }
}''')

    text = replace_section(text, 'class _TabButton', 'class _InfoPanel', r'''class _TabButton extends StatelessWidget {
  const new({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 10 : 0),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        alignment: Alignment.center,
        margin: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: selected ? palette.card : Colors.transparent,
          borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 9 : 0),
          border: selected ? Border.all(color: palette.primary.withValues(alpha: .45)) : null,
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? palette.primary : palette.textSecondary,
            fontWeight: selected ? FontWeight.w900 : FontWeight.w600,
          ),
        ),
      ),
    );
  }
}''')

    text = replace_section(text, 'class _InfoPanel', 'class _AccountInfoRow', r'''class _InfoPanel extends StatelessWidget {
  const new({required this.data});

  final ImportedScheduleData data;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return AppThemePanel(
      width: double.infinity,
      elevated: false,
      alt: true,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('Dữ liệu trên thiết bị', style: TextStyle(color: palette.textPrimary, fontWeight: FontWeight.w900)),
          const SizedBox(height: 12),
          _AccountInfoRow(label: 'Lịch học', value: '${data.classes.length} mục'),
          const SizedBox(height: 8),
          _AccountInfoRow(label: 'Lịch thi', value: '${data.exams.length} mục'),
          const SizedBox(height: 8),
          _AccountInfoRow(label: 'Cập nhật lần cuối', value: '${_dateShort(data.syncedAt)} ${_time(data.syncedAt)}'),
          const SizedBox(height: 8),
          const _AccountInfoRow(label: 'Nguồn', value: 'QLĐT Phenikaa'),
        ],
      ),
    );
  }
}''')

    text = replace_section(text, 'class _AccountInfoRow', 'class _WidgetPreview', r'''class _AccountInfoRow extends StatelessWidget {
  const new({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Row(
      children: <Widget>[
        Expanded(child: Text(label, style: TextStyle(color: palette.textSecondary, fontSize: 12))),
        Text(value, style: TextStyle(color: palette.textPrimary, fontSize: 12, fontWeight: FontWeight.w800)),
      ],
    );
  }
}''')

    text = replace_section(text, 'class _WidgetPreview', 'class _ControlPanel', r'''class _WidgetPreview extends StatelessWidget {
  const new({required this.item});

  final ScheduleRecord item;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text('Widget 1×4', style: TextStyle(color: palette.textPrimary, fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        ClipPath(
          clipper: palette.geometry == AppThemeGeometry.valorant
              ? const _WidgetValorantClipper()
              : palette.geometry == AppThemeGeometry.lol
              ? const _WidgetLolClipper()
              : null,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: <Color>[palette.widgetStart, palette.widgetEnd]),
              borderRadius: BorderRadius.circular(palette.geometry == AppThemeGeometry.rounded ? 18 : 0),
              border: Border.all(color: palette.border.withValues(alpha: .8)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(item.subjectName, style: TextStyle(color: palette.widgetText, fontWeight: FontWeight.w900)),
                const SizedBox(height: 7),
                Row(
                  children: <Widget>[
                    Icon(Icons.location_on_outlined, color: palette.widgetSubtext, size: 15),
                    const SizedBox(width: 5),
                    Text(item.room, style: TextStyle(color: palette.widgetSubtext, fontSize: 12)),
                    const Spacer(),
                    Icon(Icons.access_time_rounded, color: palette.widgetSubtext, size: 15),
                    const SizedBox(width: 5),
                    Text('${_time(item.startAt)} - ${_time(item.endAt)}', style: TextStyle(color: palette.widgetSubtext, fontSize: 12)),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _WidgetValorantClipper extends CustomClipper<Path> {
  const _WidgetValorantClipper();
  @override
  Path getClip(Size size) => Path()
    ..moveTo(12, 0)
    ..lineTo(size.width, 0)
    ..lineTo(size.width, size.height - 12)
    ..lineTo(size.width - 12, size.height)
    ..lineTo(0, size.height)
    ..lineTo(0, 12)
    ..close();
  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

class _WidgetLolClipper extends CustomClipper<Path> {
  const _WidgetLolClipper();
  @override
  Path getClip(Size size) => Path()
    ..moveTo(10, 0)
    ..lineTo(size.width - 10, 0)
    ..lineTo(size.width, 10)
    ..lineTo(size.width, size.height - 10)
    ..lineTo(size.width - 10, size.height)
    ..lineTo(10, size.height)
    ..lineTo(0, size.height - 10)
    ..lineTo(0, 10)
    ..close();
  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}''')

    text = replace_section(text, 'class _ControlPanel', 'class _ArcPanelAction', r'''class _ControlPanel extends StatelessWidget {
  const new({required this.page, required this.onOpenPage, required this.onSync});

  final _AppPage page;
  final ValueChanged<_AppPage> onOpenPage;
  final VoidCallback onSync;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: const Duration(milliseconds: 420),
      curve: Curves.easeOutCubic,
      builder: (context, progress, child) {
        return SizedBox(
          width: 300,
          height: 344,
          child: Stack(
            clipBehavior: Clip.none,
            children: <Widget>[
              _ArcPanelAction(
                progress: progress,
                start: 0,
                right: 4,
                bottom: 254,
                originOffset: const Offset(20, 78),
                child: _PanelAction(
                  label: 'Lịch học',
                  icon: Icons.event_available_rounded,
                  color: palette.primary,
                  selected: page == _AppPage.timetable,
                  onTap: () => onOpenPage(_AppPage.timetable),
                ),
              ),
              _ArcPanelAction(
                progress: progress,
                start: .08,
                right: 42,
                bottom: 196,
                originOffset: const Offset(34, 62),
                child: _PanelAction(
                  label: 'Lịch thi',
                  icon: Icons.assignment_rounded,
                  color: palette.accent,
                  selected: page == _AppPage.exam,
                  onTap: () => onOpenPage(_AppPage.exam),
                ),
              ),
              _ArcPanelAction(
                progress: progress,
                start: .16,
                right: 72,
                bottom: 138,
                originOffset: const Offset(46, 46),
                child: _PanelAction(
                  label: 'Đồng bộ',
                  icon: Icons.sync_rounded,
                  color: const Color(0xFFFFA51E),
                  selected: false,
                  onTap: onSync,
                ),
              ),
              _ArcPanelAction(
                progress: progress,
                start: .24,
                right: 92,
                bottom: 80,
                originOffset: const Offset(54, 30),
                child: _PanelAction(
                  label: 'Tài khoản',
                  icon: Icons.person_rounded,
                  color: palette.primary,
                  selected: page == _AppPage.account,
                  onTap: () => onOpenPage(_AppPage.account),
                ),
              ),
              _ArcPanelAction(
                progress: progress,
                start: .32,
                right: 100,
                bottom: 20,
                originOffset: const Offset(58, 20),
                child: _PanelAction(
                  label: 'Giao diện',
                  icon: Icons.palette_outlined,
                  color: palette.accent,
                  selected: false,
                  onTap: () => showAppThemePicker(context),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}''')

    text = replace_section(text, 'class _PanelAction', 'class _MetaLine', r'''class _PanelAction extends StatelessWidget {
  const new({
    required this.label,
    required this.icon,
    required this.color,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: AppThemePanel(
          elevated: true,
          padding: const EdgeInsets.fromLTRB(18, 5, 5, 5),
          child: SizedBox(
            height: 40,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(
                  label,
                  style: TextStyle(
                    color: selected ? palette.primary : palette.textPrimary,
                    fontWeight: FontWeight.w800,
                    letterSpacing: themeLetterSpacing(palette),
                  ),
                ),
                const SizedBox(width: 12),
                CircleAvatar(
                  radius: 20,
                  backgroundColor: color,
                  child: Icon(
                    icon,
                    color: palette.id == AppThemeId.lol && color == palette.primary
                        ? const Color(0xFF06171D)
                        : Colors.white,
                    size: 20,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}''')

    text = replace_section(text, 'class _MetaLine', 'class _EmptyState', r'''class _MetaLine extends StatelessWidget {
  const new({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Row(
      children: <Widget>[
        Icon(icon, size: 15, color: palette.textSecondary),
        const SizedBox(width: 5),
        Expanded(child: Text(text, style: TextStyle(color: palette.textSecondary, fontSize: 12))),
      ],
    );
  }
}''')

    text = replace_section(text, 'class _EmptyState', 'class _ErrorBanner', r'''class _EmptyState extends StatelessWidget {
  const new({required this.icon, required this.title, required this.message});

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 52, color: palette.primary.withValues(alpha: .6)),
            const SizedBox(height: 14),
            Text(title, style: TextStyle(color: palette.textPrimary, fontWeight: FontWeight.w900, fontSize: 16)),
            const SizedBox(height: 7),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(color: palette.textSecondary, height: 1.45, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}''')

    text = replace_section(text, 'class _PhoneSurface', 'class _AppMark', r'''class _PhoneSurface extends StatelessWidget {
  const new({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    return ColoredBox(
      color: palette.surface.withValues(alpha: palette.dark ? .94 : .985),
      child: SizedBox.expand(child: child),
    );
  }
}''')

    text = replace_section(text, 'class _AppMark', 'class _MicrosoftMark', r'''class _AppMark extends StatelessWidget {
  const new({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    final palette = appThemePalette;
    final square = palette.geometry != AppThemeGeometry.rounded;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: palette.card.withValues(alpha: .35),
        borderRadius: BorderRadius.circular(square ? 0 : size * .2),
        border: Border.all(
          color: palette.primary,
          width: palette.geometry == AppThemeGeometry.pixel ? size * .07 : size * .08,
        ),
        boxShadow: palette.geometry == AppThemeGeometry.pixel
            ? <BoxShadow>[BoxShadow(color: palette.shadow, offset: Offset(size * .06, size * .06))]
            : null,
      ),
      child: Icon(
        AppThemeController.instance.theme.icon,
        size: size * .58,
        color: palette.primary,
      ),
    );
  }
}''')

    path.write_text(text, encoding='utf-8')


def rewrite_pubspec() -> None:
    path = ROOT / 'pubspec.yaml'
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^version:.*$', 'version: 2.0.0+5', text, count=1, flags=re.MULTILINE)
    font_block = """\n  fonts:\n    - family: MinecraftCustom\n      fonts:\n        - asset: assets/fonts/minecraft.ttf\n"""
    if 'family: MinecraftCustom' not in text:
        marker = '  uses-material-design: true\n'
        if marker not in text:
            raise RuntimeError('pubspec flutter marker missing')
        text = text.replace(marker, marker + font_block, 1)
    path.write_text(text, encoding='utf-8')


def build_minecraft_font() -> None:
    css_path = Path('/tmp/demoE/minecraft-font.css')
    if not css_path.exists():
        raise RuntimeError('demoE minecraft font source missing')
    css = css_path.read_text(encoding='utf-8')
    match = re.search(r'base64,([^\"]+)', css)
    if not match:
        raise RuntimeError('embedded Minecraft font not found')
    woff = ROOT / 'assets/fonts/minecraft.woff2'
    ttf = ROOT / 'assets/fonts/minecraft.ttf'
    woff.parent.mkdir(parents=True, exist_ok=True)
    woff.write_bytes(base64.b64decode(match.group(1)))
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fonttools[woff]', 'brotli'])
        from fontTools.ttLib import TTFont
    font = TTFont(str(woff))
    font.flavor = None
    font.save(str(ttf))
    woff.unlink(missing_ok=True)


def rewrite_widget_service() -> None:
    path = ROOT / 'platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetService.kt'
    text = path.read_text(encoding='utf-8')
    text = text.replace(
        '        val backgroundPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {\n            shader = LinearGradient(\n                0f,\n                0f,\n                widthPx,\n                0f,\n                0xFF173A8E.toInt(),\n                0xFF315AB5.toInt(),\n                Shader.TileMode.CLAMP,\n            )\n        }',
        '''        val theme = readWidgetTheme(context)\n        val backgroundPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {\n            shader = LinearGradient(\n                0f,\n                0f,\n                widthPx,\n                0f,\n                theme.startColor,\n                theme.endColor,\n                Shader.TileMode.CLAMP,\n            )\n        }''',
        1,
    )
    text = text.replace('            color = 0xFFFFFFFF.toInt()\n            textSize = heightPx * SUBJECT_TEXT_HEIGHT_FRACTION\n            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)', '            color = theme.textColor\n            textSize = heightPx * SUBJECT_TEXT_HEIGHT_FRACTION\n            typeface = themedTypeface(context, theme, Typeface.BOLD)', 1)
    text = text.replace('            color = 0xFFDDE8FF.toInt()\n            textSize = heightPx * DETAIL_TEXT_HEIGHT_FRACTION', '            color = theme.subtextColor\n            textSize = heightPx * DETAIL_TEXT_HEIGHT_FRACTION\n            typeface = themedTypeface(context, theme, Typeface.NORMAL)', 1)
    insert_marker = 'private fun readWidgetClasses(context: Context, widgetId: Int): List<WidgetClass> {'
    helper = r'''private data class WidgetTheme(
    val key: String,
    val startColor: Int,
    val endColor: Int,
    val textColor: Int,
    val subtextColor: Int,
)

private fun readWidgetTheme(context: Context): WidgetTheme {
    val key = context
        .getSharedPreferences(SNAPSHOT_PREFS, Context.MODE_PRIVATE)
        .getString(THEME_KEY, "classic")
        ?: "classic"
    return when (key) {
        "lol" -> WidgetTheme(key, 0xFF06131A.toInt(), 0xFF0B343A.toInt(), 0xFFF0E6D2.toInt(), 0xFFC8AA6E.toInt())
        "valorant" -> WidgetTheme(key, 0xFF0F1923.toInt(), 0xFF24313B.toInt(), 0xFFECE8E1.toInt(), 0xFFFF7B86.toInt())
        "minecraft" -> WidgetTheme(key, 0xFF3A2B20.toInt(), 0xFF6B4A2F.toInt(), 0xFFFFFFFF.toInt(), 0xFFD8D1C9.toInt())
        "facebook" -> WidgetTheme(key, 0xFFFFFFFF.toInt(), 0xFFE7F3FF.toInt(), 0xFF050505.toInt(), 0xFF65676B.toInt())
        "shopee" -> WidgetTheme(key, 0xFFEE4D2D.toInt(), 0xFFFF6A3D.toInt(), 0xFFFFFFFF.toInt(), 0xFFFFE9E1.toInt())
        "tiktok" -> WidgetTheme(key, 0xFF111111.toInt(), 0xFF2A1520.toInt(), 0xFFFFFFFF.toInt(), 0xFF25F4EE.toInt())
        "ben10" -> WidgetTheme(key, 0xFF101510.toInt(), 0xFF1D5F22.toInt(), 0xFFFFFFFF.toInt(), 0xFF7CFF00.toInt())
        "youtube" -> WidgetTheme(key, 0xFF181818.toInt(), 0xFF2B0E14.toInt(), 0xFFFFFFFF.toInt(), 0xFFFF8A9F.toInt())
        "steam" -> WidgetTheme(key, 0xFF171D25.toInt(), 0xFF1B3D55.toInt(), 0xFFD6E9F8.toInt(), 0xFF66C0F4.toInt())
        else -> WidgetTheme("classic", 0xFF173A8E.toInt(), 0xFF315AB5.toInt(), 0xFFFFFFFF.toInt(), 0xFFDDE8FF.toInt())
    }
}

private fun themedTypeface(context: Context, theme: WidgetTheme, style: Int): Typeface {
    if (theme.key != "minecraft") {
        return Typeface.create(Typeface.DEFAULT, style)
    }
    return try {
        val base = context.resources.getFont(R.font.minecraft_custom)
        Typeface.create(base, style)
    } catch (_: Exception) {
        Typeface.create(Typeface.MONOSPACE, style)
    }
}

'''
    if helper not in text:
        text = text.replace(insert_marker, helper + insert_marker, 1)
    text = text.replace('private const val SNAPSHOT_KEY = "flutter.better_phenikaa_snapshot_v1"', 'private const val SNAPSHOT_KEY = "flutter.better_phenikaa_snapshot_v1"\nprivate const val THEME_KEY = "flutter.appTheme"', 1)
    path.write_text(text, encoding='utf-8')


def add_android_font_resource() -> None:
    # Android native widget cannot read Flutter asset paths directly. Copy the exact
    # supplied Minecraft face into res/font too so the home-screen widget matches app.
    src = ROOT / 'assets/fonts/minecraft.ttf'
    dst = ROOT / 'platform/android_widget/app/src/main/res/font/minecraft_custom.ttf'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())


def rewrite_widget_provider() -> None:
    path = ROOT / 'platform/android_widget/app/src/main/kotlin/vn/edu/phenikaa/better_phenikaa_schedule/ScheduleWidgetProvider.kt'
    text = path.read_text(encoding='utf-8')
    marker = '        views.setRemoteAdapter(R.id.widget_list, serviceIntent)\n'
    injection = r'''        val themeKey = context
            .getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .getString("flutter.appTheme", "classic")
            ?: "classic"
        val themeEndColor = when (themeKey) {
            "lol" -> 0xFF0B343A.toInt()
            "valorant" -> 0xFF24313B.toInt()
            "minecraft" -> 0xFF6B4A2F.toInt()
            "facebook" -> 0xFFE7F3FF.toInt()
            "shopee" -> 0xFFFF6A3D.toInt()
            "tiktok" -> 0xFF2A1520.toInt()
            "ben10" -> 0xFF1D5F22.toInt()
            "youtube" -> 0xFF2B0E14.toInt()
            "steam" -> 0xFF1B3D55.toInt()
            else -> 0xFF315AB5.toInt()
        }
        val iconColor = if (themeKey == "facebook") 0xFF0866FF.toInt() else 0xFFFFFFFF.toInt()
        views.setInt(R.id.widget_stack_peek_mask, "setBackgroundColor", themeEndColor)
        views.setInt(R.id.widget_calendar, "setColorFilter", iconColor)
'''
    if injection not in text:
        if marker not in text:
            raise RuntimeError('widget provider adapter marker missing')
        text = text.replace(marker, injection + marker, 1)
    path.write_text(text, encoding='utf-8')


def main() -> None:
    write_theme_file()
    build_minecraft_font()
    add_android_font_resource()
    rewrite_pubspec()
    rewrite_app()
    rewrite_widget_service()
    rewrite_widget_provider()
    # One-shot generator: remove it from the finished 2.0 source tree.
    Path(__file__).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
