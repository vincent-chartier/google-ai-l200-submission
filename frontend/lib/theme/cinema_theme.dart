import 'package:flutter/material.dart';

class CinemaTheme {
  static const Color darkBackground = Color(0xFF0F0E17);
  static const Color cardBackground = Color(0xFF1E1C2E);
  static const Color elevatedBackground = Color(0xFF2B2842);
  static const Color goldAccent = Color(0xFFFFB703);
  static const Color neonCoral = Color(0xFFFF5964);
  static const Color textPrimary = Color(0xFFFFFFFE);
  static const Color textSecondary = Color(0xFFA7A9BE);
  static const Color seatAvailable = Color(0xFF353350);
  static const Color seatSelected = Color(0xFFFFB703);
  static const Color seatOccupied = Color(0xFF6B6D76);
  static const Color seatVip = Color(0xFF7209B7);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBackground,
      primaryColor: goldAccent,
      colorScheme: const ColorScheme.dark(
        primary: goldAccent,
        secondary: neonCoral,
        surface: cardBackground,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: darkBackground,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: cardBackground,
        elevation: 6,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: goldAccent,
          foregroundColor: Colors.black,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 15,
          ),
        ),
      ),
    );
  }
}
