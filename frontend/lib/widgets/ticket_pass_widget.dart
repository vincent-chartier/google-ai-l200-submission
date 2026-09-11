import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../theme/cinema_theme.dart';

class TicketPassWidget extends StatelessWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;

  const TicketPassWidget({
    super.key,
    required this.component,
    required this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final props = component.props;
    final bookingId = props['booking_id'] as String? ?? 'BK-89312';
    final movieTitle = props['movie_title'] as String? ?? 'Cinema Outing';
    final cinema = props['cinema'] as String? ?? 'Metropolis Cinema IMAX';
    final hall = props['hall'] as String? ?? 'IMAX Laser Hall';
    final dateTime = props['date_time'] as String? ?? '2026-09-12 19:30';
    final seats = (props['seats'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? ['F7', 'F8'];
    final totalAmount = (props['total_amount'] as num?)?.toDouble() ?? 39.00;
    final paymentMethod = props['payment_method'] as String? ?? 'Google Pay';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: CinemaTheme.goldAccent, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: CinemaTheme.goldAccent.withOpacity(0.2),
            blurRadius: 16,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        children: [
          // Pass Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: CinemaTheme.elevatedBackground,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.movie_creation_outlined, color: CinemaTheme.goldAccent, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      cinema.toUpperCase(),
                      style: const TextStyle(
                        color: CinemaTheme.goldAccent,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.greenAccent),
                  ),
                  child: const Text(
                    'CONFIRMED',
                    style: TextStyle(
                      color: Colors.greenAccent,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Main Pass Body
          Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  movieTitle,
                  style: const TextStyle(
                    color: CinemaTheme.textPrimary,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  hall,
                  style: const TextStyle(
                    color: CinemaTheme.textSecondary,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 18),

                // Details Grid
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildInfoColumn('DATE & TIME', dateTime),
                    _buildInfoColumn('SEATS', seats.join(', ')),
                    _buildInfoColumn('TOTAL', '\$${totalAmount.toStringAsFixed(2)}'),
                  ],
                ),
                const SizedBox(height: 14),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildInfoColumn('BOOKING REF', bookingId),
                    _buildInfoColumn('PAYMENT', paymentMethod),
                    _buildInfoColumn('TICKETS', '${seats.length} Standard'),
                  ],
                ),

                const SizedBox(height: 20),

                // Decorative Dotted Divider
                Row(
                  children: List.generate(
                    30,
                    (index) => Expanded(
                      child: Container(
                        height: 1,
                        color: index.isEven ? Colors.white24 : Colors.transparent,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // Mock QR / Barcode Scan Area
                Center(
                  child: Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.qr_code_2, size: 80, color: Colors.black),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Scan at gate • $bookingId',
                        style: const TextStyle(
                          color: CinemaTheme.textSecondary,
                          fontSize: 11,
                          letterSpacing: 1,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 18),

                // Action Buttons
                if (component.actions.isNotEmpty)
                  ...component.actions.map(
                    (act) => Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        gradient: CinemaTheme.bluePinkGradient,
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [
                          BoxShadow(
                            color: CinemaTheme.hotPink.withOpacity(0.3),
                            blurRadius: 10,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          foregroundColor: Colors.white,
                        ),
                        icon: const Icon(Icons.calendar_today, size: 16),
                        label: Text(act.label),
                        onPressed: () => onAction(act),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoColumn(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: CinemaTheme.textSecondary,
            fontSize: 10,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.8,
          ),
        ),
        const SizedBox(height: 3),
        Text(
          value,
          style: const TextStyle(
            color: CinemaTheme.textPrimary,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
