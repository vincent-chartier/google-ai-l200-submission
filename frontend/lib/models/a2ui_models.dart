/// A2UI (Agent-to-UI) Protocol Dart Models
///
/// Defines structured declarative UI components streamed from Python agents
/// and consumed by the Flutter dynamic renderer.

class A2UIAction {
  final String label;
  final String action;
  final String? icon;
  final Map<String, dynamic> payload;

  A2UIAction({
    required this.label,
    required this.action,
    this.icon,
    required this.payload,
  });

  factory A2UIAction.fromJson(Map<String, dynamic> json) {
    return A2UIAction(
      label: json['label'] as String? ?? '',
      action: json['action'] as String? ?? '',
      icon: json['icon'] as String?,
      payload: (json['payload'] as Map<String, dynamic>?) ?? {},
    );
  }

  Map<String, dynamic> toJson() => {
    'label': label,
    'action': action,
    if (icon != null) 'icon': icon,
    'payload': payload,
  };
}

class A2UIComponent {
  final String id;
  final String type;
  final Map<String, dynamic> props;
  final List<A2UIAction> actions;

  A2UIComponent({
    required this.id,
    required this.type,
    required this.props,
    required this.actions,
  });

  factory A2UIComponent.fromJson(Map<String, dynamic> json) {
    final rawActions = json['actions'] as List<dynamic>? ?? [];
    return A2UIComponent(
      id: json['id'] as String? ?? 'cmp_${DateTime.now().millisecondsSinceEpoch}',
      type: json['type'] as String? ?? 'unknown',
      props: (json['props'] as Map<String, dynamic>?) ?? {},
      actions: rawActions
          .map((a) => A2UIAction.fromJson(a as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type,
    'props': props,
    'actions': actions.map((a) => a.toJson()).toList(),
  };
}

class A2UIQuickReply {
  final String label;
  final String action;
  final Map<String, dynamic> payload;

  A2UIQuickReply({
    required this.label,
    required this.action,
    required this.payload,
  });

  factory A2UIQuickReply.fromJson(Map<String, dynamic> json) {
    return A2UIQuickReply(
      label: json['label'] as String? ?? '',
      action: json['action'] as String? ?? '',
      payload: (json['payload'] as Map<String, dynamic>?) ?? {},
    );
  }

  Map<String, dynamic> toJson() => {
    'label': label,
    'action': action,
    'payload': payload,
  };
}

class A2UIMessage {
  final String protocolVersion;
  final String sessionId;
  final String agent;
  final String text;
  final List<A2UIComponent> components;
  final List<A2UIQuickReply> quickReplies;
  final Map<String, dynamic> stateUpdates;

  A2UIMessage({
    this.protocolVersion = '1.0',
    required this.sessionId,
    required this.agent,
    required this.text,
    required this.components,
    required this.quickReplies,
    this.stateUpdates = const {},
  });

  factory A2UIMessage.fromJson(Map<String, dynamic> json) {
    final rawComponents = json['components'] as List<dynamic>? ?? [];
    final rawReplies = json['quick_replies'] as List<dynamic>? ?? [];

    return A2UIMessage(
      protocolVersion: json['protocol_version'] as String? ?? '1.0',
      sessionId: json['session_id'] as String? ?? '',
      agent: json['agent'] as String? ?? 'CoordinatorAgent',
      text: json['text'] as String? ?? '',
      components: rawComponents
          .map((c) => A2UIComponent.fromJson(c as Map<String, dynamic>))
          .toList(),
      quickReplies: rawReplies
          .map((r) => A2UIQuickReply.fromJson(r as Map<String, dynamic>))
          .toList(),
      stateUpdates: (json['state_updates'] as Map<String, dynamic>?) ?? {},
    );
  }
}

class ChatEntry {
  final String id;
  final String sender; // 'user' or agent name like 'SearchRecoAgent'
  final String text;
  final DateTime timestamp;
  final A2UIMessage? a2uiPayload;

  ChatEntry({
    required this.id,
    required this.sender,
    required this.text,
    required this.timestamp,
    this.a2uiPayload,
  });

  bool get isUser => sender == 'user';
}
