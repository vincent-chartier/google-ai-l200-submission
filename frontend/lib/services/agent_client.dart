import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/a2ui_models.dart';

class AgentClient {
  final String baseUrl;
  final String sessionId;

  AgentClient({
    String? baseUrl,
    this.sessionId = 'mobile_user_01',
  }) : baseUrl = baseUrl ?? (kIsWeb ? Uri.base.origin : 'http://localhost:8080');

  /// Sends a natural language message to the Agent Coordinator
  Future<A2UIMessage> sendMessage(String text) async {
    final uri = Uri.parse('$baseUrl/api/v1/agent/chat');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': sessionId,
          'message': text,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        return A2UIMessage.fromJson(data);
      } else {
        throw Exception('Server returned ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      // Fallback simulation if offline
      return _generateOfflineFallback(text);
    }
  }

  /// Sends an A2UI widget interaction action back to the Agent backend
  Future<A2UIMessage> sendAction(String action, Map<String, dynamic> payload) async {
    final uri = Uri.parse('$baseUrl/api/v1/a2ui/action');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': sessionId,
          'action': action,
          'payload': payload,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        return A2UIMessage.fromJson(data);
      } else {
        throw Exception('Server returned ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      return _generateOfflineFallback(action);
    }
  }

  /// Fetches the user's active session state (favorites, seen movies, active booking)
  Future<Map<String, dynamic>> fetchUserState() async {
    final uri = Uri.parse('$baseUrl/api/v1/user/state/$sessionId');
    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {}
    return {};
  }

  A2UIMessage _generateOfflineFallback(String input) {
    return A2UIMessage(
      sessionId: sessionId,
      agent: 'SearchRecoAgent',
      text: "Connected in offline simulation mode: exploring '$input'.",
      components: [
        A2UIComponent(
          id: 'demo_card_1',
          type: 'movie_card',
          props: {
            'title': 'Dune: Part Two',
            'genres': ['Sci-Fi', 'Adventure'],
            'rating': 8.6,
            'runtime': '166 min',
            'taste_match_reason': 'Matches your favorite: Interstellar',
            'synopsis': 'Paul Atreides unites with Chani and the Fremen to lead a revolt.',
            'showtimes': ['16:30', '19:30', '22:15'],
          },
          actions: [
            A2UIAction(
              label: 'View Seats (19:30)',
              action: 'SELECT_SHOWTIME',
              payload: {'showtime_id': 'SH-DUNE-1930'},
            )
          ],
        )
      ],
      quickReplies: [
        A2UIQuickReply(label: 'Show Seats 19:30', action: 'SELECT_SHOWTIME', payload: {'showtime_id': 'SH-DUNE-1930'}),
        A2UIQuickReply(label: 'Show My Watched Movies', action: 'VIEW_HISTORY', payload: {}),
      ],
    );
  }
}
