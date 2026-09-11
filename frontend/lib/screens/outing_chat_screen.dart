import 'package:flutter/material.dart';
import '../models/a2ui_models.dart';
import '../services/agent_client.dart';
import '../widgets/a2ui_renderer.dart';
import '../widgets/movie_card_widget.dart';
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
      backgroundColor: CinemaTheme.darkBackground,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Background Image (no transparency) - man on stairs in The Truman Show
          Positioned.fill(
            child: Image.asset(
              'assets/images/truman_show_stairs.jpg',
              fit: BoxFit.cover,
              width: double.infinity,
              height: double.infinity,
              errorBuilder: (context, error, stackTrace) {
                return Image.asset(
                  'assets/images/pulp_fiction.jpg',
                  fit: BoxFit.cover,
                  width: double.infinity,
                  height: double.infinity,
                );
              },
            ),
          ),

          // Foreground UI (Top search bar, quick replies, messages)
          SafeArea(
            child: Column(
              children: [
                // Top search bar without header
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
                          child: CircularProgressIndicator(strokeWidth: 2, color: CinemaTheme.hotPink),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '$_activeAgent is planning your outing...',
                          style: const TextStyle(color: CinemaTheme.softPink, fontSize: 12),
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
        ],
      ),
    );
  }

  Widget _buildTopSearchBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: CinemaTheme.cardBackground.withOpacity(0.92),
        border: Border(
          bottom: BorderSide(
            color: CinemaTheme.electricBlue.withOpacity(0.25),
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
                prefixIcon: const Icon(Icons.search, color: CinemaTheme.neonCyan, size: 20),
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide(color: CinemaTheme.electricBlue.withOpacity(0.2)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide(color: CinemaTheme.electricBlue.withOpacity(0.2)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: const BorderSide(color: CinemaTheme.electricBlue, width: 1.5),
                ),
              ),
              onSubmitted: _handleUserSubmit,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              gradient: CinemaTheme.bluePinkGradient,
              borderRadius: BorderRadius.circular(21),
              boxShadow: [
                BoxShadow(
                  color: CinemaTheme.hotPink.withOpacity(0.35),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: IconButton(
              padding: EdgeInsets.zero,
              icon: const Icon(Icons.send_rounded, size: 18, color: Colors.white),
              onPressed: () => _handleUserSubmit(_textController.text),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickReplies() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF141838), // Solid standout card background
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: CinemaTheme.neonCyan.withOpacity(0.5),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.5),
            blurRadius: 12,
            offset: const Offset(0, 3),
          ),
          BoxShadow(
            color: CinemaTheme.electricBlue.withOpacity(0.16),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: const [
              Icon(Icons.bolt, size: 16, color: CinemaTheme.neonCyan),
              SizedBox(width: 6),
              Text(
                'Quick actions',
                style: TextStyle(
                  color: CinemaTheme.neonCyan,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: _quickReplies.map((qr) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ActionChip(
                    backgroundColor: const Color(0xFF1C2248),
                    side: BorderSide(color: CinemaTheme.electricBlue.withOpacity(0.6), width: 1),
                    label: Text(
                      qr.label,
                      style: const TextStyle(
                        color: CinemaTheme.softPink,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    onPressed: () {
                      _handleA2UIAction(A2UIAction(
                        label: qr.label,
                        action: qr.action,
                        payload: qr.payload,
                      ));
                    },
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserBubble(String text) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        constraints: const BoxConstraints(maxWidth: 300),
        decoration: BoxDecoration(
          gradient: CinemaTheme.bluePinkGradient,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: CinemaTheme.hotPink.withOpacity(0.25),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Text(
          text,
          style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
    );
  }

  Widget _buildAgentBubble(ChatEntry entry) {
    final payload = entry.a2uiPayload;
    final isInitial = entry.id == 'msg_init';
    final hasText = !isInitial && entry.text.trim().isNotEmpty;

    // Filter movie_card components to group into "On Show" and "Suggested"
    final movieCards = payload?.components.where((c) => c.type == 'movie_card').toList() ?? [];
    final otherComponents = payload?.components.where((c) => c.type != 'movie_card').toList() ?? [];

    final onShowList = <A2UIComponent>[];
    final suggestedList = <A2UIComponent>[];

    for (int i = 0; i < movieCards.length; i++) {
      final c = movieCards[i];
      final cat = c.props['category'] as String?;
      final grp = c.props['group'] as String?;
      if (cat == 'suggested' || grp == 'Suggested' || (cat == null && grp == null && i > 0)) {
        suggestedList.add(c);
      } else {
        onShowList.add(c);
      }
    }

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
                  const Icon(Icons.smart_toy_outlined, size: 14, color: CinemaTheme.neonCyan),
                  const SizedBox(width: 4),
                  Text(
                    entry.sender,
                    style: const TextStyle(
                      color: CinemaTheme.neonCyan,
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
                  color: const Color(0xFF141838),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: CinemaTheme.electricBlue.withOpacity(0.4)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.4),
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Text(
                  entry.text,
                  style: const TextStyle(color: CinemaTheme.textPrimary, fontSize: 14, height: 1.3),
                ),
              ),

            // Grouped Movie Cards: "On Show" and "Suggested"
            if (onShowList.isNotEmpty)
              _buildMovieGroupCard(
                title: 'On Show',
                icon: Icons.movie_outlined,
                accentColor: CinemaTheme.electricBlue,
                components: onShowList,
              ),

            if (suggestedList.isNotEmpty)
              _buildMovieGroupCard(
                title: 'Suggested',
                icon: Icons.auto_awesome,
                accentColor: CinemaTheme.hotPink,
                components: suggestedList,
              ),

            // Other dynamic A2UI components
            if (otherComponents.isNotEmpty)
              ...otherComponents.map((comp) {
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

  Widget _buildMovieGroupCard({
    required String title,
    required IconData icon,
    required Color accentColor,
    required List<A2UIComponent> components,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 2),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF141838), // Solid standout dark background
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: accentColor.withOpacity(0.6),
          width: 1.4,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.65),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
          BoxShadow(
            color: accentColor.withOpacity(0.20),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: accentColor),
              const SizedBox(width: 6),
              Text(
                title,
                style: TextStyle(
                  color: accentColor,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          for (int i = 0; i < components.length; i++) ...[
            if (i > 0)
              Divider(
                color: accentColor.withOpacity(0.25),
                height: 20,
                thickness: 1,
              ),
            MovieCardWidget(
              component: components[i],
              onAction: _handleA2UIAction,
              isNested: true,
            ),
          ],
        ],
      ),
    );
  }
}
