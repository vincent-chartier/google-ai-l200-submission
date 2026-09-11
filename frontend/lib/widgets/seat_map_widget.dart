import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../theme/cinema_theme.dart';

class SeatMapWidget extends StatefulWidget {
  final A2UIComponent component;
  final Function(A2UIAction) onAction;

  const SeatMapWidget({
    super.key,
    required this.component,
    required this.onAction,
  });

  @override
  State<SeatMapWidget> createState() => _SeatMapWidgetState();
}

class _SeatMapWidgetState extends State<SeatMapWidget> {
  final Set<String> _selectedSeats = {};
  double _totalPrice = 0.0;

  @override
  void initState() {
    super.initState();
    // Default pre-selection for pleasant UX
    _selectedSeats.addAll(['F4', 'F5']);
    _recalculatePrice();
  }

  void _recalculatePrice() {
    final props = widget.component.props;
    final basePrice = (props['base_price'] as num?)?.toDouble() ?? 19.50;
    _totalPrice = _selectedSeats.length * basePrice;
  }

  void _toggleSeat(String seatId, String status) {
    if (status == 'occupied') return;
    setState(() {
      if (_selectedSeats.contains(seatId)) {
        _selectedSeats.remove(seatId);
      } else {
        if (_selectedSeats.length < 6) {
          _selectedSeats.add(seatId);
        }
      }
      _recalculatePrice();
    });
  }

  @override
  Widget build(BuildContext context) {
    final props = widget.component.props;
    final movieTitle = props['movie_title'] as String? ?? 'Movie Outing';
    final cinema = props['cinema'] as String? ?? 'Metropolis Cinema IMAX';
    final hall = props['hall'] as String? ?? 'IMAX Laser Hall';
    final dateTime = props['date_time'] as String? ?? 'Today 19:30';
    final seatGrid = (props['seat_grid'] as List<dynamic>?) ?? [];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: CinemaTheme.electricBlue.withOpacity(0.35), width: 1.2),
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
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Header info
          Text(
            movieTitle,
            style: const TextStyle(
              color: CinemaTheme.textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$cinema • $hall • $dateTime',
            style: const TextStyle(
              color: CinemaTheme.textSecondary,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 18),

          // Screen Curve Visual
          Container(
            width: double.infinity,
            height: 12,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  CinemaTheme.electricBlue.withOpacity(0.2),
                  CinemaTheme.neonCyan,
                  CinemaTheme.hotPink,
                  CinemaTheme.hotPink.withOpacity(0.2),
                ],
              ),
              borderRadius: BorderRadius.circular(6),
              boxShadow: [
                BoxShadow(
                  color: CinemaTheme.hotPink.withOpacity(0.3),
                  blurRadius: 10,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'IMAX CURVED SCREEN',
            style: TextStyle(
              color: CinemaTheme.textSecondary,
              fontSize: 10,
              letterSpacing: 2,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          // 2D Seat Grid
          if (seatGrid.isNotEmpty)
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Column(
                children: seatGrid.map((rowItem) {
                  final rowMap = rowItem as Map<String, dynamic>;
                  final rowLetter = rowMap['row'] as String? ?? '';
                  final seats = (rowMap['seats'] as List<dynamic>?) ?? [];

                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 20,
                          child: Text(
                            rowLetter,
                            style: const TextStyle(
                              color: CinemaTheme.textSecondary,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        ...seats.map((s) {
                          final seat = s as Map<String, dynamic>;
                          final seatId = seat['seat_id'] as String;
                          final status = seat['status'] as String? ?? 'available';
                          final isSelected = _selectedSeats.contains(seatId);
                          final isOccupied = status == 'occupied';

                          Color seatColor;
                          if (isSelected) {
                            seatColor = CinemaTheme.seatSelected;
                          } else if (isOccupied) {
                            seatColor = CinemaTheme.seatOccupied;
                          } else {
                            seatColor = CinemaTheme.seatAvailable;
                          }

                          return GestureDetector(
                            onTap: () => _toggleSeat(seatId, status),
                            child: Container(
                              width: 28,
                              height: 28,
                              margin: const EdgeInsets.symmetric(horizontal: 3),
                              decoration: BoxDecoration(
                                color: seatColor,
                                borderRadius: BorderRadius.circular(6),
                                border: isSelected
                                    ? Border.all(color: Colors.white, width: 1.5)
                                    : null,
                              ),
                              child: Center(
                                child: Text(
                                  seatId,
                                  style: TextStyle(
                                    color: isSelected
                                        ? Colors.black
                                        : (isOccupied ? Colors.white30 : Colors.white70),
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),

          const SizedBox(height: 16),

          // Legend
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildLegend(CinemaTheme.seatAvailable, 'Available'),
              const SizedBox(width: 14),
              _buildLegend(CinemaTheme.seatSelected, 'Selected'),
              const SizedBox(width: 14),
              _buildLegend(CinemaTheme.seatOccupied, 'Occupied'),
            ],
          ),

          const Divider(color: CinemaTheme.elevatedBackground, height: 28),

          // Summary and Booking Action Bar
          Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _selectedSeats.isEmpty
                        ? 'No seats selected'
                        : 'Seats: ${_selectedSeats.join(', ')}',
                    style: const TextStyle(
                      color: CinemaTheme.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'Total: \$${_totalPrice.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: CinemaTheme.goldAccent,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Container(
                decoration: BoxDecoration(
                  gradient: _selectedSeats.isEmpty ? null : CinemaTheme.bluePinkGradient,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: _selectedSeats.isEmpty
                      ? null
                      : [
                          BoxShadow(
                            color: CinemaTheme.hotPink.withOpacity(0.35),
                            blurRadius: 10,
                            offset: const Offset(0, 3),
                          ),
                        ],
                ),
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _selectedSeats.isEmpty ? Colors.grey.shade800 : Colors.transparent,
                    shadowColor: Colors.transparent,
                    foregroundColor: Colors.white,
                  ),
                  icon: const Icon(Icons.lock_outline, size: 16),
                  label: const Text('Hold & Pay'),
                  onPressed: _selectedSeats.isEmpty
                      ? null
                      : () {
                          widget.onAction(A2UIAction(
                            label: 'Hold Seats',
                            action: 'HOLD_SEATS',
                            payload: {
                              'showtime_id': props['showtime_id'] ?? 'SH-DUNE-1930',
                              'seats': _selectedSeats.toList(),
                            },
                          ));
                        },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegend(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 11),
        ),
      ],
    );
  }
}
