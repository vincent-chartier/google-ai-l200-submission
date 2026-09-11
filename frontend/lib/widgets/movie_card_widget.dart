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
    final location = props['location'] as String? ??
        props['theater_location'] as String? ??
        props['theater'] as String? ??
        'Metropolis Cinema IMAX • 450 7th Ave, Downtown';
    final showtimes = (props['showtimes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 5, horizontal: 2),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground.withOpacity(0.90),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: CinemaTheme.electricBlue.withOpacity(0.35),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: CinemaTheme.electricBlue.withOpacity(0.12),
            blurRadius: 10,
            offset: const Offset(-2, 2),
          ),
          BoxShadow(
            color: CinemaTheme.hotPink.withOpacity(0.12),
            blurRadius: 12,
            offset: const Offset(2, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Title
          Text(
            title,
            style: const TextStyle(
              color: CinemaTheme.textPrimary,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),

          // Theater Location
          Text(
            location,
            style: const TextStyle(
              color: CinemaTheme.textSecondary,
              fontSize: 12,
            ),
          ),

          // Showtimes
          if (showtimes.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: showtimes.map((st) {
                return Container(
                  decoration: BoxDecoration(
                    gradient: CinemaTheme.bluePinkGradient,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  padding: const EdgeInsets.all(1.2),
                  child: Container(
                    decoration: BoxDecoration(
                      color: CinemaTheme.cardBackground,
                      borderRadius: BorderRadius.circular(6.8),
                    ),
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: CinemaTheme.hotPink,
                        side: BorderSide.none,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(6.8),
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
                      child: Text(
                        st,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: CinemaTheme.hotPink,
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }
}
