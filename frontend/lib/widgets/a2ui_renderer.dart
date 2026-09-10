import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import 'movie_card_widget.dart';
import 'seat_map_widget.dart';
import 'ticket_pass_widget.dart';
import 'calendar_invite_widget.dart';
import 'seen_history_widget.dart';

/// The A2UI Dynamic Engine
///
/// Inspects incoming declarative A2UI Component specifications streamed
/// from Python backend agents and instantiates first-class native Flutter widgets.
class A2UIRenderer extends StatelessWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;

  const A2UIRenderer({
    super.key,
    required this.component,
    required this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    switch (component.type) {
      case 'movie_card':
        return MovieCardWidget(component: component, onAction: onAction);
      case 'seat_map_selector':
        return SeatMapWidget(component: component, onAction: onAction);
      case 'ticket_pass':
        return TicketPassWidget(component: component, onAction: onAction);
      case 'calendar_invite_card':
        return CalendarInviteWidget(component: component, onAction: onAction);
      case 'seen_history_list':
        return SeenHistoryWidget(component: component, onAction: onAction);
      default:
        return _buildFallbackCard(context);
    }
  }

  Widget _buildFallbackCard(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Dynamic Widget: ${component.type}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(component.props.toString(), style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
