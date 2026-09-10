import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../theme/cinema_theme.dart';

class SeenHistoryWidget extends StatelessWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;

  const SeenHistoryWidget({
    super.key,
    required this.component,
    required this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final props = component.props;
    final seen = (props['seen_movies'] as List<dynamic>?) ?? [];
    final favorites = (props['favorite_movies'] as List<dynamic>?) ?? [];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: CinemaTheme.goldAccent.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          const Row(
            children: [
              Icon(Icons.history_edu, color: CinemaTheme.goldAccent, size: 20),
              SizedBox(width: 8),
              Text(
                'Cinema Profile & Taste Memory',
                style: TextStyle(
                  color: CinemaTheme.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Favorite Movies Section
          const Text(
            'FAVORITE MOVIES (Passed to Reco Agent):',
            style: TextStyle(
              color: CinemaTheme.goldAccent,
              fontSize: 11,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: favorites.map((f) {
              final title = f['title'] as String? ?? '';
              final genre = f['genre'] as String? ?? '';
              return Chip(
                backgroundColor: CinemaTheme.elevatedBackground,
                avatar: const Icon(Icons.star, color: CinemaTheme.goldAccent, size: 14),
                label: Text(
                  '$title ($genre)',
                  style: const TextStyle(fontSize: 11, color: CinemaTheme.textPrimary),
                ),
              );
            }).toList(),
          ),

          const SizedBox(height: 16),

          // Watched History Section
          const Text(
            'WATCHED MOVIES (Excluded from Recos):',
            style: TextStyle(
              color: CinemaTheme.textSecondary,
              fontSize: 11,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 6),
          ...seen.map((s) {
            final title = s['title'] as String? ?? '';
            final date = s['watched_date'] as String? ?? '';
            final score = s['user_score'] ?? 5;
            return Container(
              margin: const EdgeInsets.only(bottom: 6),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: CinemaTheme.darkBackground,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle_outline, color: Colors.greenAccent, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      title,
                      style: const TextStyle(color: CinemaTheme.textPrimary, fontSize: 13),
                    ),
                  ),
                  Text(
                    '★ $score • $date',
                    style: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 11),
                  ),
                ],
              ),
            );
          }),

          if (component.actions.isNotEmpty) ...[
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.auto_awesome, size: 16),
                label: const Text('Find Movies Matching Favorites'),
                onPressed: () {
                  onAction(component.actions.first);
                },
              ),
            ),
          ],
        ],
      ),
    );
  }
}
