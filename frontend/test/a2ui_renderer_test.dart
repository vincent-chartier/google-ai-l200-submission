import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cinema_outings/models/a2ui_models.dart';
import 'package:cinema_outings/widgets/a2ui_renderer.dart';
import 'package:cinema_outings/services/agent_client.dart';
import 'package:cinema_outings/screens/outing_chat_screen.dart';
import 'package:cinema_outings/widgets/movie_card_widget.dart';
import 'package:cinema_outings/main.dart';

void main() {
  testWidgets('A2UIRenderer renders movie_card correctly', (WidgetTester tester) async {
    final comp = A2UIComponent(
      id: 'test_card_1',
      type: 'movie_card',
      props: {
        'title': 'Dune: Part Two',
        'location': 'Metropolis Cinema IMAX • 450 7th Ave',
        'showtimes': ['19:30'],
      },
      actions: [
        A2UIAction(label: 'Book Now', action: 'SELECT_SHOWTIME', payload: {}),
      ],
    );

    A2UIAction? triggeredAction;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: A2UIRenderer(
            component: comp,
            onAction: (act) {
              triggeredAction = act;
            },
          ),
        ),
      ),
    );

    expect(find.text('Dune: Part Two'), findsOneWidget);
    expect(find.text('Metropolis Cinema IMAX • 450 7th Ave'), findsOneWidget);
    expect(find.text('19:30'), findsOneWidget);

    // Verify extra fields and action buttons are not rendered
    expect(find.text('Book Now'), findsNothing);
    expect(find.text('Matches Interstellar'), findsNothing);

    await tester.tap(find.text('19:30'));
    await tester.pump();
    expect(triggeredAction?.action, 'SELECT_SHOWTIME');
  });

  testWidgets('MovieCardWidget renders standout styling with group title', (WidgetTester tester) async {
    final comp = A2UIComponent(
      id: 'test_card_on_show',
      type: 'movie_card',
      props: {
        'title': 'Dune: Part Two',
        'location': 'Metropolis Cinema IMAX • 450 7th Ave',
        'showtimes': ['19:30'],
        'group': 'On Show',
      },
      actions: [],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MovieCardWidget(
            component: comp,
            onAction: (_) {},
          ),
        ),
      ),
    );

    expect(find.text('On Show'), findsOneWidget);
    expect(find.text('Dune: Part Two'), findsOneWidget);
    expect(find.text('19:30'), findsOneWidget);
  });

  testWidgets('A2UIRenderer renders ticket_pass correctly', (WidgetTester tester) async {
    final comp = A2UIComponent(
      id: 'test_ticket_1',
      type: 'ticket_pass',
      props: {
        'booking_id': 'BK-TEST99',
        'movie_title': 'Interstellar',
        'cinema': 'Metropolis Cinema IMAX',
        'hall': 'IMAX Laser Hall',
        'date_time': '2026-09-12 18:00',
        'seats': ['F7', 'F8'],
        'total_amount': 44.0,
      },
      actions: [],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: A2UIRenderer(
            component: comp,
            onAction: (_) {},
          ),
        ),
      ),
    );

    expect(find.text('BK-TEST99'), findsWidgets);
    expect(find.text('Interstellar'), findsOneWidget);
    expect(find.text('F7, F8'), findsOneWidget);
    expect(find.text('\$44.00'), findsOneWidget);
  });

  testWidgets('A2UIRenderer renders calendar_invite_card correctly', (WidgetTester tester) async {
    final comp = A2UIComponent(
      id: 'test_cal_1',
      type: 'calendar_invite_card',
      props: {
        'movie_title': 'Dune: Part Two',
        'cinema': 'Metropolis Cinema IMAX',
        'start_time': '2026-09-12 19:30',
        'seats': ['F7', 'F8'],
      },
      actions: [],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: A2UIRenderer(
            component: comp,
            onAction: (_) {},
          ),
        ),
      ),
    );

    expect(find.text('Cinema Outing: Dune: Part Two'), findsOneWidget);
    expect(find.text('Add to Calendar'), findsOneWidget);
  });

  testWidgets('OutingChatScreen renders Truman Show background and top search bar without titles', (WidgetTester tester) async {
    final client = AgentClient(baseUrl: 'http://127.0.0.1:9999'); // offline mock port

    await tester.pumpWidget(
      MaterialApp(
        home: OutingChatScreen(client: client),
      ),
    );
    await tester.pumpAndSettle();

    // Verify titles/subtitles are removed
    expect(find.text('Cinema Outings AI'), findsNothing);
    expect(find.text('OutingCoordinatorAgent'), findsNothing);

    // Verify search bar is present at the top with search icon and hint
    expect(find.byIcon(Icons.search), findsOneWidget);
    expect(find.text('Search movies, screenings, seats, tickets...'), findsOneWidget);

    // Verify introducing text is removed from initial load
    expect(find.textContaining('Connected in offline simulation mode'), findsNothing);
  });

  testWidgets('MainNavigationScreen has Home and My Cinema navigation items', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: MainNavigationScreen(),
      ),
    );
    await tester.pump();

    expect(find.text('Home'), findsOneWidget);
    expect(find.text('My Cinema'), findsOneWidget);
  });
}
