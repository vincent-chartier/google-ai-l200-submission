import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../theme/cinema_theme.dart';

class MovieCardWidget extends StatelessWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;
  final bool isNested;
  final String? groupTitle;

  const MovieCardWidget({
    super.key,
    required this.component,
    required this.onAction,
    this.isNested = false,
    this.groupTitle,
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

    final displayGroup = groupTitle ?? props['group'] as String? ??
        (props['category'] == 'suggested' ? 'Suggested' : (props['category'] == 'on_show' ? 'On Show' : null));

    final isSuggested = displayGroup == 'Suggested';
    final accentColor = isSuggested ? CinemaTheme.hotPink : CinemaTheme.electricBlue;
    final groupIcon = isSuggested ? Icons.auto_awesome : Icons.movie_outlined;

    final content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (displayGroup != null && !isNested) ...[
          Row(
            children: [
              Icon(groupIcon, size: 16, color: accentColor),
              const SizedBox(width: 6),
              Text(
                displayGroup,
                style: TextStyle(
                  color: accentColor,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
        ],

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
                    color: const Color(0xFF141838),
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
    );

    if (isNested) {
      return content;
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 5, horizontal: 2),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF141838), // Solid standout dark background
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: accentColor.withOpacity(0.55),
          width: 1.3,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.6),
            blurRadius: 14,
            offset: const Offset(0, 4),
          ),
          BoxShadow(
            color: accentColor.withOpacity(0.18),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: content,
    );
  }
}
