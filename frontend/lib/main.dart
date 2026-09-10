import 'package:flutter/material.dart';
import 'theme/cinema_theme.dart';
import 'services/agent_client.dart';
import 'screens/outing_chat_screen.dart';
import 'screens/seen_history_screen.dart';

void main() {
  runApp(const CinemaOutingsApp());
}

class CinemaOutingsApp extends StatelessWidget {
  const CinemaOutingsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cinema Outings AI',
      debugShowCheckedModeBanner: false,
      theme: CinemaTheme.darkTheme,
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;
  late final AgentClient _client;

  @override
  void initState() {
    super.initState();
    _client = AgentClient(
      sessionId: 'cinema_fan_01',
    );
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      OutingChatScreen(client: _client),
      SeenHistoryScreen(client: _client),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        backgroundColor: CinemaTheme.cardBackground,
        indicatorColor: CinemaTheme.goldAccent.withOpacity(0.25),
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.forum_outlined, color: CinemaTheme.textSecondary),
            selectedIcon: Icon(Icons.forum, color: CinemaTheme.goldAccent),
            label: 'AI Planner',
          ),
          NavigationDestination(
            icon: Icon(Icons.movie_filter_outlined, color: CinemaTheme.textSecondary),
            selectedIcon: Icon(Icons.movie_filter, color: CinemaTheme.goldAccent),
            label: 'My Cinema Profile',
          ),
        ],
      ),
    );
  }
}
