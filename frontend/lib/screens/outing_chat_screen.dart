import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../services/agent_client.dart';
import '../widgets/a2ui_renderer.dart';
import '../theme/cinema_theme.dart';

class OutingChatScreen extends StatefulWidget {
  final AgentClient client;

  const OutingChatScreen({super.key, required this.client});

  @override
  State<OutingChatScreen> createState() => _OutingChatScreenState();
}

class _OutingChatScreenState extends State<OutingChatScreen> {
  final List<ChatEntry> _messages = [];
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  List<A2UIQuickReply> _quickReplies = [];
  String _activeAgent = 'OutingCoordinatorAgent';

  @override
  void initState() {
    super.initState();
    _sendInitialGreeting();
  }

  void _sendInitialGreeting() async {
    setState(() => _isLoading = true);
    final initialResp = await widget.client.sendMessage("Hello, what movies are playing today?");
    setState(() {
      _isLoading = false;
      _activeAgent = initialResp.agent;
      _quickReplies = initialResp.quickReplies;
      _messages.add(ChatEntry(
        id: 'msg_init',
        sender: initialResp.agent,
        text: '',
        timestamp: DateTime.now(),
        a2uiPayload: initialResp,
      ));
    });
  }

  Future<void> _handleUserSubmit(String text) async {
    if (text.trim().isEmpty) return;
    _textController.clear();

    setState(() {
      _messages.add(ChatEntry(
        id: 'usr_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'user',
        text: text,
        timestamp: DateTime.now(),
      ));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await widget.client.sendMessage(text);
      setState(() {
        _activeAgent = response.agent;
        _quickReplies = response.quickReplies;
        _messages.add(ChatEntry(
          id: 'agent_${DateTime.now().millisecondsSinceEpoch}',
          sender: response.agent,
          text: response.text,
          timestamp: DateTime.now(),
          a2uiPayload: response,
        ));
      });
      // Compact conversation history if messages accumulate
      if (_messages.length > 10) {
        widget.client.compactHistory();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Agent connection error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
      _scrollToBottom();
    }
  }

  Future<void> _handleA2UIAction(A2UIAction action) async {
    setState(() {
      _messages.add(ChatEntry(
        id: 'act_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'user',
        text: action.label.isNotEmpty ? action.label : 'Selected action: ${action.action}',
        timestamp: DateTime.now(),
      ));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await widget.client.sendAction(action.action, action.payload);
      setState(() {
        _activeAgent = response.agent;
        _quickReplies = response.quickReplies;
        _messages.add(ChatEntry(
          id: 'agent_${DateTime.now().millisecondsSinceEpoch}',
          sender: response.agent,
          text: response.text,
          timestamp: DateTime.now(),
          a2uiPayload: response,
        ));
      });
      if (_messages.length > 10) {
        widget.client.compactHistory();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Action error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        top: false,
        bottom: false,
        child: Column(
          children: [
            // Full width header with Pulp Fiction image (no titles, no subtitles)
            _buildPulpFictionHeader(),

            // Search bar moved to the top, directly after pictured header
            _buildTopSearchBar(),

            // Quick replies below search bar
            if (_quickReplies.isNotEmpty) _buildQuickReplies(),

            if (_isLoading)
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: CinemaTheme.goldAccent),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '$_activeAgent is planning your outing...',
                      style: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 12),
                    ),
                  ],
                ),
              ),

            // Chat & A2UI Stream
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final entry = _messages[index];
                  if (entry.isUser) {
                    return _buildUserBubble(entry.text);
                  } else {
                    return _buildAgentBubble(entry);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPulpFictionHeader() {
    return SizedBox(
      width: double.infinity,
      height: 190,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.asset(
            'assets/images/pulp_fiction.jpg',
            fit: BoxFit.cover,
            width: double.infinity,
            errorBuilder: (context, error, stackTrace) {
              return Image.network(
                'https://image.tmdb.org/t/p/w780/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg',
                fit: BoxFit.cover,
                width: double.infinity,
              );
            },
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            height: 35,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    CinemaTheme.darkBackground.withOpacity(0.85),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopSearchBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground,
        border: Border(
          bottom: BorderSide(
            color: Colors.white.withOpacity(0.08),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _textController,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Search movies, screenings, seats, tickets...',
                hintStyle: const TextStyle(color: CinemaTheme.textSecondary, fontSize: 13),
                filled: true,
                fillColor: CinemaTheme.darkBackground,
                prefixIcon: const Icon(Icons.search, color: CinemaTheme.goldAccent, size: 20),
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
              ),
              onSubmitted: _handleUserSubmit,
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            style: IconButton.styleFrom(
              backgroundColor: CinemaTheme.goldAccent,
              foregroundColor: Colors.black,
            ),
            icon: const Icon(Icons.send_rounded, size: 20),
            onPressed: () => _handleUserSubmit(_textController.text),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickReplies() {
    return Container(
      height: 44,
      padding: const EdgeInsets.symmetric(vertical: 4),
      color: CinemaTheme.darkBackground,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: _quickReplies.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final qr = _quickReplies[index];
          return ActionChip(
            backgroundColor: CinemaTheme.elevatedBackground,
            side: const BorderSide(color: CinemaTheme.goldAccent, width: 0.8),
            label: Text(
              qr.label,
              style: const TextStyle(color: CinemaTheme.goldAccent, fontSize: 12),
            ),
            onPressed: () {
              _handleA2UIAction(A2UIAction(
                label: qr.label,
                action: qr.action,
                payload: qr.payload,
              ));
            },
          );
        },
      ),
    );
  }

  Widget _buildUserBubble(String text) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: const BoxConstraints(maxWidth: 300),
        decoration: BoxDecoration(
          color: CinemaTheme.elevatedBackground,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white12),
        ),
        child: Text(
          text,
          style: const TextStyle(color: Colors.white, fontSize: 14),
        ),
      ),
    );
  }

  Widget _buildAgentBubble(ChatEntry entry) {
    final payload = entry.a2uiPayload;
    final isInitial = entry.id == 'msg_init';
    final hasText = !isInitial && entry.text.trim().isNotEmpty;

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Agent sender label (hidden for initial load)
            if (!isInitial) ...[
              Row(
                children: [
                  const Icon(Icons.smart_toy_outlined, size: 14, color: CinemaTheme.goldAccent),
                  const SizedBox(width: 4),
                  Text(
                    entry.sender,
                    style: const TextStyle(
                      color: CinemaTheme.goldAccent,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
            ],

            // Text message bubble
            if (hasText)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 6),
                decoration: BoxDecoration(
                  color: CinemaTheme.cardBackground,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Text(
                  entry.text,
                  style: const TextStyle(color: CinemaTheme.textPrimary, fontSize: 14, height: 1.3),
                ),
              ),

            // Dynamic A2UI Components
            if (payload != null && payload.components.isNotEmpty)
              ...payload.components.map((comp) {
                return A2UIRenderer(
                  component: comp,
                  onAction: _handleA2UIAction,
                );
              }),
          ],
        ),
      ),
    );
  }
}
