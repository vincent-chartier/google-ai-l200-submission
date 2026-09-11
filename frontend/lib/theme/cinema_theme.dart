import 'package:flutter/material.dart';

class CinemaTheme {
  // Deep space midnight blue background
  static const Color darkBackground = Color(0xFF090B1A);
  static const Color cardBackground = Color(0xFF12162E);
  static const Color elevatedBackground = Color(0xFF1B2042);

  // Blues & Pinks Palette
  static const Color electricBlue = Color(0xFF3A86FF);
  static const Color neonCyan = Color(0xFF00F0FF);
  static const Color hotPink = Color(0xFFFF2A85);
  static const Color vibrantMagenta = Color(0xFFE01E78);
  static const Color softPink = Color(0xFFFF70A6);
  static const Color violetPurple = Color(0xFF7B2CBF);

  // Backward-compatible aliases for existing widget references
  static const Color goldAccent = Color(0xFFFF2A85); // Maps gold to radiant hot pink
  static const Color neonCoral = Color(0xFFFF70A6); // Maps coral to soft pastel pink

  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFF94A3B8); // Cool blue-slate

  // Seat status
  static const Color seatAvailable = Color(0xFF1E2447);
  static const Color seatSelected = Color(0xFFFF2A85); // Hot Pink
  static const Color seatOccupied = Color(0xFF475569);
  static const Color seatVip = Color(0xFF3A86FF); // Electric Blue

  // Primary Gradients (Blues and Pinks)
  static const LinearGradient bluePinkGradient = LinearGradient(
    colors: [electricBlue, hotPink],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient pinkBlueGradient = LinearGradient(
    colors: [hotPink, electricBlue],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient cyanPinkGradient = LinearGradient(
    colors: [neonCyan, electricBlue, hotPink],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient ambientBackdrop = LinearGradient(
    colors: [
      Color(0xFF080D26), // Deep Navy Blue
      Color(0xFF150A28), // Deep Violet
      Color(0xFF280720), // Glowing Neon Pink / Magenta
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBackground,
      primaryColor: hotPink,
      colorScheme: const ColorScheme.dark(
        primary: hotPink,
        secondary: electricBlue,
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
          backgroundColor: hotPink,
          foregroundColor: Colors.white,
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
