import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;

void main() {
  runApp(NewsAIChatApp());
}

// This is a simple AI-powered news chat application built with Flutter.
// The class `NewsAIChatApp` initializes the app and sets up the main chat screen.
// It includes a sidebar for chat history, a main chat area for messages, and an input area for user input.
// The app simulates AI responses based on user queries about recent news and current events.
class NewsAIChatApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'News AI Chat',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'SF Pro Display',
        scaffoldBackgroundColor: Color(0xFFF7F7F8),
      ),
      home: ChatScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// The `Chat` class represents a chat session with a unique ID, title, messages, and timestamps.
// It includes methods to create a copy of the chat with updated properties.
class Chat {
  final String id;
  final String title;
  final List<Message> messages;
  final DateTime createdAt;
  final DateTime updatedAt;

  Chat({
    required this.id,
    required this.title,
    required this.messages,
    required this.createdAt,
    required this.updatedAt,
  });

  Chat copyWith({
    String? title,
    List<Message>? messages,
    DateTime? updatedAt,
  }) {
    return Chat(
      id: this.id,
      title: title ?? this.title,
      messages: messages ?? this.messages,
      createdAt: this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

// The `Message` class represents a single message in a chat session.
// It includes properties for the message ID, content, whether it's from the user or AI,
// the timestamp of when it was sent, and an optional source indicating where the information came from
class Message {
  final String id;
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final String? source;

  Message({
    required this.id,
    required this.content,
    required this.isUser,
    required this.timestamp,
    this.source,
  });
}

// The `ChatScreen` widget is the main screen of the app, displaying the chat interface.
// It manages the chat history, current chat, user input, and AI responses.
// It uses a stateful widget to handle dynamic updates and animations.
class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

// The `_ChatScreenState` class manages the state of the `ChatScreen` widget.
class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  List<Chat> _chats = [];
  Chat? _currentChat;
  bool _isTyping = false;
  bool _sidebarExpanded = true;
  
  late AnimationController _typingController;
  late AnimationController _sidebarController;

  @override
  void initState() {
    super.initState();
    _typingController = AnimationController(
      duration: Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
    
    _sidebarController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    _controller.addListener(() {
      setState(() {}); // Forces UI to recheck if send button should be active
    });

    _initializeApp();
  }

  void _initializeApp() {
    // Create sample chat history
    _chats = [
      Chat(
        id: '1',
        title: 'Latest Technology News',
        messages: [
          Message(
            id: '1',
            content: 'What are the latest developments in AI?',
            isUser: true,
            timestamp: DateTime.now().subtract(Duration(hours: 2)),
          ),
          Message(
            id: '2',
            content: 'Recent AI developments include major breakthroughs in large language models, computer vision advances, and new applications in healthcare diagnostics...',
            isUser: false,
            timestamp: DateTime.now().subtract(Duration(hours: 2)),
            source: 'Vector DB',
          ),
        ],
        createdAt: DateTime.now().subtract(Duration(hours: 2)),
        updatedAt: DateTime.now().subtract(Duration(hours: 2)),
      ),
      Chat(
        id: '2',
        title: 'Climate Change Updates',
        messages: [
          Message(
            id: '3',
            content: 'Tell me about recent climate change news',
            isUser: true,
            timestamp: DateTime.now().subtract(Duration(days: 1)),
          ),
          Message(
            id: '4',
            content: 'Recent climate reports show significant developments in renewable energy adoption and new international climate agreements...',
            isUser: false,
            timestamp: DateTime.now().subtract(Duration(days: 1)),
            source: 'Web Search',
          ),
        ],
        createdAt: DateTime.now().subtract(Duration(days: 1)),
        updatedAt: DateTime.now().subtract(Duration(days: 1)),
      ),
    ];
    
    if (_chats.isNotEmpty) {
      _currentChat = _chats.first;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _typingController.dispose();
    _sidebarController.dispose();
    super.dispose();
  }
  void _createNewChat() {
    final newChat = Chat(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: 'New Chat',
      messages: [],
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    setState(() {
      _chats.insert(0, newChat);
      _currentChat = newChat; // Important: DO NOT set this to null
      _controller.clear();
    });
}


  void _selectChat(Chat chat) {
    setState(() {
      _currentChat = chat;
    });
    
    // Auto-collapse sidebar on mobile after selection
    if (MediaQuery.of(context).size.width < 768) {
      setState(() {
        _sidebarExpanded = false;
      });
    }
  }

  void _deleteChat(Chat chat) {
    setState(() {
      _chats.remove(chat);
      if (_currentChat?.id == chat.id) {
        _currentChat = _chats.isNotEmpty ? _chats.first : null;
      }
    });
  }

  void _sendMessage([String? text]) async {
    final messageText = text?.trim() ?? _controller.text.trim();
    if (messageText.isEmpty || _isTyping) return;

    final userMessage = Message(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: messageText,
      isUser: true,
      timestamp: DateTime.now(),
    );

    // Create new chat if none exists
    if (_currentChat == null) {
      _createNewChat();
    }

    // Add user message
    setState(() {
      _currentChat = _currentChat!.copyWith(
        messages: [..._currentChat!.messages, userMessage],
        title: _currentChat!.messages.isEmpty 
            ? _generateChatTitle(messageText) 
            : _currentChat!.title,
        updatedAt: DateTime.now(),
      );
      _updateChatInList(_currentChat!);
      _isTyping = true;
    });

    _controller.clear();
    _scrollToBottom();

    // Simulate AI response
    final botResponseText = await _generateBotResponse(messageText);

    final botMessage = Message(
      id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
      content: botResponseText, 
      isUser: false,
      timestamp: DateTime.now(),
      source: Random().nextBool() ? 'Vector DB' : 'Web Search',
    );


    setState(() {
      _currentChat = _currentChat!.copyWith(
        messages: [..._currentChat!.messages, botMessage],
        updatedAt: DateTime.now(),
      );
      _updateChatInList(_currentChat!);
      _isTyping = false;
    });

    _scrollToBottom();
  }

  void _updateChatInList(Chat updatedChat) {
    final index = _chats.indexWhere((chat) => chat.id == updatedChat.id);
    if (index != -1) {
      _chats[index] = updatedChat;
      // Move to top
      _chats.removeAt(index);
      _chats.insert(0, updatedChat);
    }
  }

  String _generateChatTitle(String firstMessage) {
    if (firstMessage.length > 50) {
      return firstMessage.substring(0, 50) + '...';
    }
    return firstMessage;
  }

  // String _generateBotResponse(String query) {
  //   // final responses = [
  //   //   "Based on the latest news data, here's what I found about \"$query\":\n\nThis topic has been trending recently with several important developments. The information comes from multiple reliable sources including major news outlets and recent reports.",
  //   //   "I've analyzed recent news articles related to your question about \"$query\".\n\nHere are the key findings:\n• Multiple sources are reporting on this topic\n• The situation is evolving rapidly\n• Expert opinions suggest significant implications",
  //   //   "From my analysis of current news and information regarding \"$query\":\n\nThe data shows interesting patterns and recent developments that are worth noting. This information is based on both my knowledge base and recent web searches.",
  //   // ];
  //   // return responses[Random().nextInt(responses.length)];
  // }
  // what is future here?
  // This function generates a bot response by making an HTTP request to a backend service.
  // It sends the user's input as a JSON payload and returns the AI-generated response.
  // It also handles the typing state to show a loading indicator while waiting for the response.
  Future<String> _generateBotResponse(String input) async {
    setState(() {
      _isTyping = true;
    });

    try {
      final uri = Uri.parse('http://localhost:8000/ask'); // or your IP on mobile
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'question': input}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final answer = data['answer'] ?? 'No answer received.';
        return answer;
      } else {
        throw Exception('Failed to get response: ${response.statusCode}');
      }

    } catch (e) {
      return '⚠️ Error generating response. Tap "Retry" below to try again.';

    } finally {
      setState(() {
        _isTyping = false;
      });
    }
 }


  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _toggleSidebar() {
    setState(() {
      _sidebarExpanded = !_sidebarExpanded;
    });
    
    if (_sidebarExpanded) {
      _sidebarController.forward();
    } else {
      _sidebarController.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 768;
    
    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          AnimatedContainer(
            duration: Duration(milliseconds: 300),
            width: _sidebarExpanded ? (isMobile ? 280 : 320) : 0,
            child: _sidebarExpanded ? _buildSidebar() : null,
          ),
          
          // Main Chat Area
          Expanded(
            child: _buildMainChatArea(isMobile),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebar() {
    return Container(
      decoration: BoxDecoration(
        color: Color(0xFF202123),
        border: Border(
          right: BorderSide(color: Colors.grey[800]!, width: 1),
        ),
      ),
      child: Column(
        children: [
          // Header with New Chat button
          Container(
            padding: EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _createNewChat,
                icon: Icon(Icons.add, size: 18),
                label: Text('New Chat'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Color(0xFF10A37F),
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
          ),
          
          // Chat History
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.symmetric(horizontal: 8),
              itemCount: _chats.length,
              itemBuilder: (context, index) {
                final chat = _chats[index];
                final isSelected = _currentChat?.id == chat.id;
                
                return Container(
                  margin: EdgeInsets.only(bottom: 4),
                  child: InkWell(
                    onTap: () => _selectChat(chat),
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: isSelected ? Color(0xFF343541) : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.chat_bubble_outline,
                            size: 16,
                            color: Colors.white70,
                          ),
                          SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  chat.title,
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w400,
                                  ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                SizedBox(height: 2),
                                Text(
                                  _formatChatTime(chat.updatedAt),
                                  style: TextStyle(
                                    color: Colors.white54,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          PopupMenuButton<String>(
                            icon: Icon(Icons.more_horiz, color: Colors.white54, size: 18),
                            color: Color(0xFF343541),
                            onSelected: (value) {
                              if (value == 'delete') {
                                _deleteChat(chat);
                              }
                            },
                            itemBuilder: (context) => [
                              PopupMenuItem(
                                value: 'delete',
                                child: Row(
                                  children: [
                                    Icon(Icons.delete_outline, color: Colors.red, size: 18),
                                    SizedBox(width: 8),
                                    Text('Delete', style: TextStyle(color: Colors.white)),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          
          // Footer
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: Colors.grey[800]!, width: 1)),
            ),
            child: GestureDetector(
              onTap: () {
                setState(() {
                  _currentChat = null;
                  _controller.clear();
                });
              },
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 16,
                    backgroundColor: Color(0xFF10A37F),
                    child: Icon(Icons.person, color: Colors.white, size: 18),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'News AI Assistant',
                      style: TextStyle(color: Colors.white, fontSize: 14),
                    ),
                  ),
                  Icon(Icons.settings_outlined, color: Colors.white54, size: 20),
                ],
              ),
            )
          ),
        ],
      ),
    );
  }

  Widget _buildMainChatArea(bool isMobile) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
      ),
      child: Column(
        children: [
          // Header
          _buildChatHeader(isMobile),
          
          // Messages Area
          Expanded(
            child: _currentChat == null || _currentChat!.messages.isEmpty
                ? _buildEmptyState()
                : _buildMessagesList(),
          ),
          
          // Input Area
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildChatHeader(bool isMobile) {
    return Container(
      height: 60,
      padding: EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
      ),
      child: Row(
        children: [
          if (!_sidebarExpanded || isMobile)
            IconButton(
              onPressed: _toggleSidebar,
              icon: Icon(Icons.menu),
              tooltip: 'Toggle Sidebar',
            ),
          
          Expanded(
            child: Text(
              _currentChat?.title ?? 'News AI Assistant',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Color(0xFF374151),
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          
          // Status indicator
          Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Color(0xFF10B981).withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: Color(0xFF10B981),
                    shape: BoxShape.circle,
                  ),
                ),
                SizedBox(width: 4),
                Text(
                  'Online',
                  style: TextStyle(
                    fontSize: 12,
                    color: Color(0xFF10B981),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF667eea), Color(0xFF764ba2)],
              ),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.smart_toy, color: Colors.white, size: 40),
          ),
          SizedBox(height: 24),
          Text(
            'Welcome to News AI!',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: Color(0xFF374151),
            ),
          ),
          SizedBox(height: 12),
          Text(
            'Ask me about recent news, current events, or any topic you\'re curious about.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Color(0xFF6B7280),
              height: 1.5,
            ),
          ),
          SizedBox(height: 32),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            alignment: WrapAlignment.center,
            children: [
              _buildSuggestionChip('📰', 'What are today\'s top news stories?'),
              _buildSuggestionChip('💻', 'Latest technology developments'),
              _buildSuggestionChip('🌍', 'Global news updates'),
              _buildSuggestionChip('📈', 'Business and market news'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSuggestionChip(String emoji, String text) {
    return InkWell(
      onTap: () {
        _controller.clear(); // optional
        _sendMessage(text);  // pass the actual text clicked

      },
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Color(0xFFF3F4F6),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Color(0xFFE5E7EB)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emoji, style: TextStyle(fontSize: 16)),
            SizedBox(width: 8),
            Text(
              text,
              style: TextStyle(
                color: Color(0xFF374151),
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessagesList() {
    return ListView.builder(
      controller: _scrollController,
      padding: EdgeInsets.all(16),
      itemCount: _currentChat!.messages.length + (_isTyping ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == _currentChat!.messages.length && _isTyping) {
          return _buildTypingIndicator();
        }
        return _buildMessageBubble(_currentChat!.messages[index]);
      },
    );
  }

  Widget _buildMessageBubble(Message message) {
    bool isRetryableError = !message.isUser &&
        message.content.contains('⚠️ Error generating response');

    return Container(
      margin: EdgeInsets.only(bottom: 24),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              gradient: message.isUser
                  ? LinearGradient(colors: [Color(0xFF667eea), Color(0xFF764ba2)])
                  : LinearGradient(colors: [Color(0xFF10A37F), Color(0xFF059669)]),
              shape: BoxShape.circle,
            ),
            child: Icon(
              message.isUser ? Icons.person : Icons.smart_toy,
              color: Colors.white,
              size: 18,
            ),
          ),
          SizedBox(width: 16),

          // Message Content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Message bubble + Retry
                Container(
                  padding: EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: message.isUser ? Color(0xFFF3F4F6) : Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: message.isUser ? Color(0xFFE5E7EB) : Color(0xFFE5E7EB),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SelectableText(
                        message.content,
                        style: TextStyle(
                          fontSize: 15,
                          height: 1.6,
                          color: Color(0xFF374151),
                        ),
                      ),
                      if (isRetryableError)
                        Align(
                          alignment: Alignment.centerLeft,
                          child: TextButton.icon(
                            onPressed: () {
                              final userMessage = _currentChat?.messages
                                  .reversed
                                  .firstWhere((m) => m.isUser, orElse: () => Message(
                                    id: '',
                                    content: '',
                                    isUser: true,
                                    timestamp: DateTime.now(),
                                  ));

                              if (userMessage != null && userMessage.content.isNotEmpty) {
                                _controller.text = userMessage.content;
                                _sendMessage(userMessage.content);
                              }
                            },
                            icon: Icon(Icons.refresh, size: 16, color: Colors.red),
                            label: Text(
                              "Retry",
                              style: TextStyle(color: Colors.red),
                            ),
                            style: TextButton.styleFrom(
                              padding: EdgeInsets.only(top: 12),
                              minimumSize: Size(0, 30),
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                SizedBox(height: 8),

                // Metadata
                Row(
                  children: [
                    Text(
                      _formatMessageTime(message.timestamp),
                      style: TextStyle(
                        fontSize: 12,
                        color: Color(0xFF9CA3AF),
                      ),
                    ),
                    if (message.source != null) ...[
                      SizedBox(width: 8),
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Color(0xFF3B82F6).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          message.source!,
                          style: TextStyle(
                            fontSize: 10,
                            color: Color(0xFF3B82F6),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildTypingIndicator() {
    return Container(
      margin: EdgeInsets.only(bottom: 24),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [Color(0xFF10A37F), Color(0xFF059669)]),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.smart_toy, color: Colors.white, size: 18),
          ),
          SizedBox(width: 16),
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Color(0xFFE5E7EB)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (int i = 0; i < 3; i++)
                  AnimatedBuilder(
                    animation: _typingController,
                    builder: (context, child) {
                      return Container(
                        margin: EdgeInsets.only(right: i < 2 ? 4 : 0),
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: Color(0xFF9CA3AF).withOpacity(
                            0.3 + 0.7 * ((_typingController.value + i * 0.3) % 1.0),
                          ),
                          shape: BoxShape.circle,
                        ),
                      );
                    },
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFE5E7EB))),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              constraints: BoxConstraints(maxHeight: 120),
              decoration: BoxDecoration(
                color: Color(0xFFF9FAFB),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Color(0xFFE5E7EB)),
              ),
              child: TextField(
                controller: _controller,
                enabled: !_isTyping,
                maxLines: 1,
                textInputAction: TextInputAction.send, // shows "Send" button on mobile keyboard
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: 'Message News AI...',
                  hintStyle: TextStyle(color: Color(0xFF9CA3AF)),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                ),
                onSubmitted: (value) {
                  if (value.trim().isNotEmpty) {
                    _sendMessage(value); // This function sends the message
                  }
                },
              ),
            ),
          ),
          SizedBox(width: 12),
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: _controller.text.trim().isNotEmpty && !_isTyping
                  ? LinearGradient(colors: [Color(0xFF10A37F), Color(0xFF059669)])
                  : null,
              color: _controller.text.trim().isEmpty || _isTyping
                  ? Color(0xFFE5E7EB)
                  : null,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              onPressed: _controller.text.trim().isNotEmpty && !_isTyping
                  ? _sendMessage
                  : null,
              icon: Icon(
                Icons.arrow_upward,
                color: _controller.text.trim().isNotEmpty && !_isTyping
                    ? Colors.white
                    : Color(0xFF9CA3AF),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatChatTime(DateTime time) {
    final now = DateTime.now();
    final difference = now.difference(time);
    
    if (difference.inDays == 0) {
      return 'Today';
    } else if (difference.inDays == 1) {
      return 'Yesterday';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} days ago';
    } else {
      return '${time.day}/${time.month}/${time.year}';
    }
  }

  String _formatMessageTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
}