import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../theme/cinema_theme.dart';

class CalendarInviteWidget extends StatefulWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;

  const CalendarInviteWidget({
    super.key,
    required this.component,
    required this.onAction,
  });

  @override
  State<CalendarInviteWidget> createState() => _CalendarInviteWidgetState();
}

class _CalendarInviteWidgetState extends State<CalendarInviteWidget> {
  bool _addedToCalendar = false;

  @override
  Widget build(BuildContext context) {
    final props = widget.component.props;
    final movieTitle = props['movie_title'] as String? ?? 'Cinema Outing';
    final cinema = props['cinema'] as String? ?? 'Metropolis Cinema IMAX';
    final startTime = props['start_time'] as String? ?? '2026-09-12T19:30:00';
    final seats = (props['seats'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.blueAccent.withOpacity(0.4), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.blueAccent.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.blueAccent.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.event_available, color: Colors.blueAccent, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'CALENDAR EVENT READY',
                      style: TextStyle(
                        color: Colors.blueAccent,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Cinema Outing: $movieTitle',
                      style: const TextStyle(
                        color: CinemaTheme.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: CinemaTheme.elevatedBackground,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              children: [
                _buildRow(Icons.location_on_outlined, cinema),
                const SizedBox(height: 8),
                _buildRow(Icons.access_time, startTime.replaceAll('T', ' ')),
                if (seats.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  _buildRow(Icons.event_seat_outlined, 'Seats: ${seats.join(', ')}'),
                ],
              ],
            ),
          ),

          const SizedBox(height: 14),

          if (_addedToCalendar)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.2),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.check_circle, color: Colors.greenAccent, size: 18),
                  SizedBox(width: 8),
                  Text(
                    'Added to your calendar!',
                    style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            )
          else
            Row(
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: CinemaTheme.bluePinkGradient,
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: CinemaTheme.hotPink.withOpacity(0.3),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                      ),
                      icon: const Icon(Icons.add_to_photos, size: 16),
                      label: const Text('Add to Calendar'),
                      onPressed: () {
                        setState(() {
                          _addedToCalendar = true;
                        });
                        final act = widget.component.actions.firstWhere(
                          (a) => a.action == 'OPEN_EXTERNAL_URL',
                          orElse: () => A2UIAction(label: 'Add', action: 'OPEN_EXTERNAL_URL', payload: {}),
                        );
                        widget.onAction(act);
                      },
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white70,
                    side: const BorderSide(color: Colors.white24),
                  ),
                  icon: const Icon(Icons.download, size: 16),
                  label: const Text('.ics'),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('iCalendar .ics invite downloaded!')),
                    );
                  },
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, color: CinemaTheme.textSecondary, size: 16),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(color: CinemaTheme.textPrimary, fontSize: 12),
          ),
        ),
      ],
    );
  }
}
