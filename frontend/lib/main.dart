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
      builder: (context, child) {
        return Scaffold(
          backgroundColor: const Color(0xFF060714),
          body: Center(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 440),
              decoration: BoxDecoration(
                color: CinemaTheme.darkBackground,
                border: Border.symmetric(
                  vertical: BorderSide(
                    color: CinemaTheme.electricBlue.withOpacity(0.25),
                    width: 1,
                  ),
                ),
                boxShadow: [
                  BoxShadow(
                    color: CinemaTheme.electricBlue.withOpacity(0.15),
                    blurRadius: 30,
                    spreadRadius: 2,
                  ),
                  BoxShadow(
                    color: CinemaTheme.hotPink.withOpacity(0.15),
                    blurRadius: 40,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(0),
                child: child,
              ),
            ),
          ),
        );
      },
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
        backgroundColor: CinemaTheme.cardBackground.withOpacity(0.95),
        indicatorColor: CinemaTheme.hotPink.withOpacity(0.22),
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined, color: CinemaTheme.textSecondary),
            selectedIcon: Icon(Icons.home, color: CinemaTheme.hotPink),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.movie_filter_outlined, color: CinemaTheme.textSecondary),
            selectedIcon: Icon(Icons.movie_filter, color: CinemaTheme.electricBlue),
            label: 'My Cinema',
          ),
        ],
      ),
    );
  }
}
