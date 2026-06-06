import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeProvider extends ChangeNotifier {
  final SharedPreferences prefs;
  late ThemeMode _mode;
  ThemeProvider(this.prefs) {
    final raw = prefs.getString('theme_mode') ?? 'system';
    _mode = ThemeMode.values.firstWhere(
      (m) => m.name == raw,
      orElse: () => ThemeMode.system,
    );
  }
  ThemeMode get mode => _mode;
  Future<void> setMode(ThemeMode m) async {
    _mode = m;
    await prefs.setString('theme_mode', m.name);
    notifyListeners();
  }
}
