import 'package:flutter/material.dart';
import '../services/agent_client.dart';
import '../theme/cinema_theme.dart';

class SeenHistoryScreen extends StatefulWidget {
  final AgentClient client;

  const SeenHistoryScreen({super.key, required this.client});

  @override
  State<SeenHistoryScreen> createState() => _SeenHistoryScreenState();
}

class _SeenHistoryScreenState extends State<SeenHistoryScreen> {
  Map<String, dynamic> _state = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadState();
  }

  Future<void> _loadState() async {
    setState(() => _isLoading = true);
    final data = await widget.client.fetchUserState();
    setState(() {
      _state = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final seen = (_state['seen_movies'] as List<dynamic>?) ?? [];
    final favorites = (_state['favorite_movies'] as List<dynamic>?) ?? [];
    final activeBooking = _state['active_booking'] as Map<String, dynamic>?;

    return Scaffold(
      body: SafeArea(
        top: false,
        bottom: false,
        child: Column(
          children: [
            // Full width header with Truman Show stairs image (no titles, no subtitles)
            SizedBox(
              width: double.infinity,
              height: 190,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image.asset(
                    'assets/images/truman_show_stairs.jpg',
                    fit: BoxFit.cover,
                    width: double.infinity,
                    errorBuilder: (context, error, stackTrace) {
                      return Image.asset(
                        'assets/images/pulp_fiction.jpg',
                        fit: BoxFit.cover,
                        width: double.infinity,
                      );
                    },
                  ),
                  Positioned(
                    bottom: 16,
                    left: 16,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          'My Cinema',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.5,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Preferences & Watched Films',
                          style: TextStyle(
                            color: CinemaTheme.softPink,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Positioned(
                    top: 10,
                    right: 10,
                    child: SafeArea(
                      child: IconButton.filled(
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.black.withOpacity(0.6),
                          foregroundColor: CinemaTheme.goldAccent,
                        ),
                        icon: const Icon(Icons.refresh),
                        onPressed: _loadState,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator(color: CinemaTheme.goldAccent))
                  : RefreshIndicator(
                      onRefresh: _loadState,
                      color: CinemaTheme.goldAccent,
                      child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Active Booking Banner if present
                  if (activeBooking != null) ...[
                    _buildActiveBookingCard(activeBooking),
                    const SizedBox(height: 20),
                  ],

                  // Housekeeping Memory explanation banner
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: CinemaTheme.elevatedBackground,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: CinemaTheme.goldAccent.withOpacity(0.4)),
                    ),
                    child: const Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.psychology, color: CinemaTheme.goldAccent, size: 24),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'State / Memory Passing: The Housekeeping Agent shares your favorites with the Search & Reco Agent to generate hyper-personalized picks, while excluding movies you have already watched.',
                            style: TextStyle(
                              color: CinemaTheme.textSecondary,
                              fontSize: 12,
                              height: 1.3,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Favorites / Preferences Section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'MY PREFERENCES (${favorites.length})',
                        style: const TextStyle(
                          color: CinemaTheme.goldAccent,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1,
                        ),
                      ),
                      TextButton.icon(
                        icon: const Icon(Icons.add, size: 16),
                        label: const Text('Add Preference'),
                        style: TextButton.styleFrom(foregroundColor: CinemaTheme.goldAccent),
                        onPressed: _showAddFavoriteDialog,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (favorites.isEmpty)
                    const Text('No preferences saved yet.', style: TextStyle(color: CinemaTheme.textSecondary))
                  else
                    ...favorites.map((fav) => _buildFavoriteItem(fav)),

                  const SizedBox(height: 24),

                  // Watched Movies Section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'FILMS WATCHED (${seen.length})',
                        style: const TextStyle(
                          color: CinemaTheme.textSecondary,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (seen.isEmpty)
                    const Text('No watched movies yet.', style: TextStyle(color: CinemaTheme.textSecondary))
                  else
                    ...seen.map((item) => _buildSeenItem(item)),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

  Widget _buildActiveBookingCard(Map<String, dynamic> booking) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.greenAccent),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'UPCOMING OUTING',
                style: TextStyle(
                  color: Colors.greenAccent,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                ),
              ),
              Text(
                booking['booking_id'] ?? '',
                style: const TextStyle(color: Colors.white70, fontSize: 11),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            booking['movie_title'] ?? '',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '${booking['cinema']} • ${booking['date_time']}',
            style: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 4),
          Text(
            'Seats: ${(booking['seats'] as List<dynamic>?)?.join(', ') ?? ''}',
            style: const TextStyle(color: CinemaTheme.goldAccent, fontSize: 13, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildFavoriteItem(dynamic fav) {
    final title = fav['title'] as String? ?? '';
    final genre = fav['genre'] as String? ?? 'Movie';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.star, color: CinemaTheme.goldAccent, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                Text(genre, style: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 12)),
              ],
            ),
          ),
          const Icon(Icons.sync_alt, color: Colors.white24, size: 16),
        ],
      ),
    );
  }

  Widget _buildSeenItem(dynamic item) {
    final title = item['title'] as String? ?? '';
    final date = item['watched_date'] as String? ?? '';
    final score = item['user_score'] ?? 5;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle_outline, color: Colors.greenAccent, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                Text('Watched on $date', style: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 11)),
              ],
            ),
          ),
          Text('★ $score', style: const TextStyle(color: CinemaTheme.goldAccent, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  void _showAddFavoriteDialog() {
    final titleController = TextEditingController();
    final genreController = TextEditingController(text: 'Sci-Fi');

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: CinemaTheme.cardBackground,
          title: const Text('Add Favorite Movie', style: TextStyle(color: Colors.white)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  labelText: 'Movie Title',
                  labelStyle: TextStyle(color: CinemaTheme.textSecondary),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: genreController,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  labelText: 'Genre',
                  labelStyle: TextStyle(color: CinemaTheme.textSecondary),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (titleController.text.trim().isNotEmpty) {
                  await widget.client.sendAction('ADD_FAVORITE', {
                    'movie_title': titleController.text.trim(),
                    'genre': genreController.text.trim(),
                  });
                  Navigator.pop(context);
                  _loadState();
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }
}
