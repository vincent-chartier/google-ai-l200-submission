import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../theme/cinema_theme.dart';

class MovieCardWidget extends StatelessWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;

  const MovieCardWidget({
    super.key,
    required this.component,
    required this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final props = component.props;
    final title = props['title'] as String? ?? 'Untitled Movie';
    final genres = (props['genres'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    final runtime = props['runtime'] as String? ?? '120 min';
    final rating = props['imdb_rating'] ?? props['rating'] ?? 8.0;
    final synopsis = props['synopsis'] as String? ?? '';
    final matchReason = props['taste_match_reason'] as String? ?? '';
    final showtimes = (props['showtimes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: CinemaTheme.goldAccent.withOpacity(0.3), width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.4),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Banner / Taste Match Header
          if (matchReason.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: CinemaTheme.goldAccent.withOpacity(0.15),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                ),
              ),
              child: Row(
                children: [
                  const Icon(Icons.auto_awesome, color: CinemaTheme.goldAccent, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      matchReason,
                      style: const TextStyle(
                        color: CinemaTheme.goldAccent,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),

          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Title and Rating
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: const TextStyle(
                          color: CinemaTheme.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: CinemaTheme.goldAccent,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.star, color: Colors.black, size: 14),
                          const SizedBox(width: 4),
                          Text(
                            '$rating',
                            style: const TextStyle(
                              color: Colors.black,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 8),

                // Genre and Runtime Tags
                Row(
                  children: [
                    ...genres.map(
                      (g) => Container(
                        margin: const EdgeInsets.only(right: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: CinemaTheme.elevatedBackground,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          g,
                          style: const TextStyle(
                            color: CinemaTheme.textSecondary,
                            fontSize: 11,
                          ),
                        ),
                      ),
                    ),
                    const Spacer(),
                    Text(
                      runtime,
                      style: const TextStyle(
                        color: CinemaTheme.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),

                if (synopsis.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    synopsis,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: CinemaTheme.textSecondary.withOpacity(0.9),
                      fontSize: 13,
                      height: 1.3,
                    ),
                  ),
                ],

                // Showtimes Row
                if (showtimes.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  const Text(
                    'Available Showtimes (Today):',
                    style: TextStyle(
                      color: CinemaTheme.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: showtimes.map((st) {
                      return OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: CinemaTheme.goldAccent,
                          side: const BorderSide(color: CinemaTheme.goldAccent),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        onPressed: () {
                          onAction(A2UIAction(
                            label: 'Select $st',
                            action: 'SELECT_SHOWTIME',
                            payload: {
                              'movie_title': title,
                              'showtime_id': 'SH-DUNE-1930',
                              'time': st,
                            },
                          ));
                        },
                        child: Text(st, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      );
                    }).toList(),
                  ),
                ],

                // Action Buttons from A2UI payload
                if (component.actions.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Row(
                    children: component.actions.map((act) {
                      final isFavorite = act.action == 'ADD_FAVORITE';
                      if (isFavorite) {
                        return Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: IconButton.filledTonal(
                            icon: const Icon(Icons.favorite_border, color: CinemaTheme.neonCoral),
                            tooltip: act.label,
                            onPressed: () => onAction(act),
                          ),
                        );
                      }
                      return Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.confirmation_num, size: 16),
                          label: Text(act.label),
                          onPressed: () => onAction(act),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
