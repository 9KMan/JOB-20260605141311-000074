import 'package:flutter/material.dart';

class AppConstants {
  static const appName = 'Job Hunt';
  static const defaultApiBase = 'https://api.example.com';
  static const version = '1.0.0';
}

class AppColors {
  static const primary = Color(0xFF4F46E5); // Indigo 600
  static const secondary = Color(0xFF10B981); // Emerald 500
  static const danger = Color(0xFFEF4444); // Red 500
  static const warning = Color(0xFFF59E0B); // Amber 500
}

class AppTheme {
  static ThemeData get lightTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primary,
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      );

  static ThemeData get darkTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primary,
          brightness: Brightness.dark,
        ),
        appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      );
}
