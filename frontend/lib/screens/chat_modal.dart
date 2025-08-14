import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import '../widgets/typing_indicator.dart';
import 'package:url_launcher/url_launcher.dart';

class ChatModal extends StatefulWidget {
  const ChatModal({super.key});

  @override
  State<ChatModal> createState() => _ChatModalState();
}

class _ChatModalState extends State<ChatModal> with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  List<Map<String, dynamic>> _messages = [];
  List<Map<String, dynamic>> chatHistory = [];
  bool _isTyping = false;
  int? _selectedChatIndex;
  StreamSubscription<String>? _streamSubscription;

  final List<String> _suggestedQuestions = [
    "What's happening in tech today?",
    "Latest political developments?",
    "Sports news updates",
    "Economic market trends",
    "Climate change news",
    "Healthcare breakthroughs"
  ];

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeInOut),
    );
    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _streamSubscription?.cancel();
    super.dispose();
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

  void _startNewChat() {
    if (_messages.isNotEmpty) {
      if (_selectedChatIndex != null) {
        // Update existing chat in history
        chatHistory[_selectedChatIndex!]['messages'] = List.from(_messages);
        chatHistory[_selectedChatIndex!]['timestamp'] = DateTime.now().millisecondsSinceEpoch;
      } else {
        // Create new chat entry
        final firstUserMessage = _messages.firstWhere(
          (msg) => msg['isUser'] == true,
          orElse: () => {'text': 'New Chat', 'isUser': true},
        );
        
        chatHistory.insert(0, {
          'messages': List.from(_messages),
          'title': (firstUserMessage['text'] as String).split('\n').first.trim(),
          'timestamp': DateTime.now().millisecondsSinceEpoch,
        });
      }
    }
    
    setState(() {
      _messages.clear();
      _selectedChatIndex = null;
    });
    _fadeController.reset();
    _fadeController.forward();
  }

  void _loadChat(int index) {
    setState(() {
      _messages = List.from(chatHistory[index]['messages']);
      _selectedChatIndex = index;
    });
    _scrollToBottom();
  }

  void _deleteChat(int index) {
    setState(() {
      chatHistory.removeAt(index);
      if (_selectedChatIndex == index) {
        _messages.clear();
        _selectedChatIndex = null;
        _fadeController.reset();
        _fadeController.forward();
      } else if (_selectedChatIndex != null && _selectedChatIndex! > index) {
        _selectedChatIndex = _selectedChatIndex! - 1;
      }
    });
  }

  Stream<String> _streamResponse(String message) async* {
    final request = http.Request(
      'POST',
      Uri.parse('http://13.59.168.233:8000/ask/stream'),
    );
    
    request.headers.addAll({
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    });
    
    request.body = jsonEncode({'question': message});
    
    final streamedResponse = await request.send();
    
    if (streamedResponse.statusCode == 200) {
      await for (var chunk in streamedResponse.stream.transform(utf8.decoder)) {
        // Handle Server-Sent Events format
        final lines = chunk.split('\n');
        for (var line in lines) {
          if (line.startsWith('data: ')) {
            final data = line.substring(6); // Remove 'data: ' prefix
            if (data.trim().isNotEmpty && data != '[DONE]') {
              yield data;
            }
          }
        }
      }
    } else {
      throw Exception('Failed to connect to streaming endpoint');
    }
  }

  Future<void> _sendMessageStream([String? predefinedMessage]) async {
    final messageText = predefinedMessage ?? _controller.text.trim();
    if (messageText.isEmpty || _isTyping) return;

    setState(() {
      _messages.add({'text': messageText, 'isUser': true});
      if (predefinedMessage == null) _controller.clear();
      _isTyping = true;
    });
    _scrollToBottom();

    // Add a status message that will be updated
    setState(() {
      _messages.add({
        'isStatus': true,
        'text': 'Thinking...',
        'step': 'init'
      });
    });
    _scrollToBottom();

    String currentAnswer = '';
    List<String> sources = [];
    
    try {
                _streamSubscription = _streamResponse(messageText).listen(
        (data) {
          try {
            final update = jsonDecode(data);
            
            setState(() {
              // Remove the last message if it's a status
              if (_messages.isNotEmpty && _messages.last['isStatus'] == true) {
                _messages.removeLast();
              }

              switch (update['type']) {
                case 'status':
                  _messages.add({
                    'isStatus': true,
                    'text': update['message'],
                    'step': update['step'],
                  });
                  break;
                
                case 'complete':
                  final data = update['data'];
                  currentAnswer = data['answer'];
                  sources = List<String>.from(data['sources'] ?? []);
                  
                  _messages.add({
                    'text': currentAnswer,
                    'isUser': false,
                    'sources': sources,
                    'method': data['method'],
                    'timeTaken': data['time_taken_seconds'],
                  });
                  _isTyping = false;
                  break;
                
                case 'error':
                  _messages.add({
                    'text': "❌ Error: ${update['message']}",
                    'isUser': false,
                  });
                  _isTyping = false;
                  break;
              }
            });
            _scrollToBottom();
          } catch (e) {
            print('Error parsing stream data: $e');
          }
        },
        onError: (error) {
          setState(() {
            if (_messages.isNotEmpty && 
                (_messages.last['isStatus'] == true || 
                 _messages.last['isPartialAnswer'] == true)) {
              _messages.removeLast();
            }
            _messages.add({
              'text': "❌ Connection error: $error",
              'isUser': false,
            });
            _isTyping = false;
          });
          _scrollToBottom();
        },
        onDone: () {
          setState(() {
            _isTyping = false;
          });
        },
      );
      
    } catch (e) {
      setState(() {
        if (_messages.isNotEmpty && 
            (_messages.last['isStatus'] == true || 
             _messages.last['isPartialAnswer'] == true)) {
          _messages.removeLast();
        }
        _messages.add({
          'text': "❌ Error: $e",
          'isUser': false,
        });
        _isTyping = false;
      });
      _scrollToBottom();
    }
  }

  // Fallback to original method if streaming fails
  Future<void> _sendMessage([String? predefinedMessage]) async {
    final messageText = predefinedMessage ?? _controller.text.trim();
    if (messageText.isEmpty || _isTyping) return;

    setState(() {
      _messages.add({'text': messageText, 'isUser': true});
      if (predefinedMessage == null) _controller.clear();
      _isTyping = true;
    });
    _scrollToBottom();

    setState(() {
      _messages.add({'isTyping': true});
    });
    _scrollToBottom();

    try {
      final response = await http.post(
        Uri.parse('http://13.59.168.233:8000/ask'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'question': messageText}),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> result = jsonDecode(response.body);
        final String botAnswer = result['answer'];
        final List<dynamic> sources = result['sources'] ?? [];

        setState(() {
          _messages.removeWhere((m) => m['isTyping'] == true);
          _messages.add({
            'text': botAnswer,
            'isUser': false,
            'sources': sources,
          });
        });
      } else {
        setState(() {
          _messages.removeWhere((m) => m['isTyping'] == true);
          _messages.add({'text': "❌ Error: Failed to get response", 'isUser': false});
        });
      }
    } catch (e) {
      setState(() {
        _messages.removeWhere((m) => m['isTyping'] == true);
        _messages.add({'text': "❌ Error: $e", 'isUser': false});
      });
    } finally {
      setState(() {
        _isTyping = false;
      });
      _scrollToBottom();
    }
  }

  String _getDomain(String url) {
    try {
      final uri = Uri.parse(url);
      return uri.host.replaceFirst('www.', '');
    } catch (_) {
      return 'source';
    }
  }

  String _formatTimestamp(int timestamp) {
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
    final now = DateTime.now();
    final diff = now.difference(date);
    
    if (diff.inDays == 0) {
      return "${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}";
    } else if (diff.inDays == 1) {
      return "Yesterday";
    } else if (diff.inDays < 7) {
      return "${diff.inDays} days ago";
    } else {
      return "${date.day}/${date.month}";
    }
  }

  Widget _buildStatusMessage(Map<String, dynamic> message) {
    final step = message['step'] ?? '';
    final details = message['details'];
    
    IconData icon;
    MaterialColor color;
    
    switch (step) {
      case 'init_vectorstore':
        icon = Icons.storage;
        color = Colors.blue;
        break;
      case 'local_search':
        icon = Icons.search;
        color = Colors.orange;
        break;
      case 'web_search':
        icon = Icons.public;
        color = Colors.green;
        break;
      case 'generate_answer':
        icon = Icons.psychology;
        color = Colors.purple;
        break;
      default:
        icon = Icons.info;
        color = Colors.grey;
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  message['text'],
                  style: TextStyle(
                    color: color.shade700,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                if (details != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Found ${details['chunk_count'] ?? details['source_count'] ?? ''} items',
                    style: TextStyle(
                      color: color.shade600,
                      fontSize: 11,
                    ),
                  ),
                ],
              ],
            ),
          ),
          SizedBox(
            width: 12,
            height: 12,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }



  Widget _buildWelcomeScreen() {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.teal.shade400, Colors.teal.shade600],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.teal.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.psychology,
                  size: 60,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Ask AI',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Get the latest news and insights with live feedback',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 40),
              const Text(
                'Try asking:',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: _suggestedQuestions.map((question) {
                  return GestureDetector(
                    onTap: () => _sendMessageStream(question),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(25),
                        border: Border.all(color: Colors.teal.shade200),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.05),
                            blurRadius: 10,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Text(
                        question,
                        style: TextStyle(
                          color: Colors.teal.shade700,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSidebar() {
    return Container(
      width: 280,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.grey.shade50,
            Colors.grey.shade100,
          ],
        ),
        border: Border(right: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.teal.shade100,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(Icons.chat_bubble_outline, 
                    color: Colors.teal.shade700, size: 20),
                ),
                const SizedBox(width: 12),
                const Text(
                  'Conversations',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
          ),
          
          // New Chat Button
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: ElevatedButton.icon(
              onPressed: _startNewChat,
              icon: const Icon(Icons.add, size: 20),
              label: const Text('New Chat'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.teal,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 2,
              ),
            ),
          ),
          
          const Divider(height: 1),
          
          // Chat History
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: chatHistory.length,
              itemBuilder: (context, index) {
                final chat = chatHistory[index];
                final isSelected = _selectedChatIndex == index;
                
                return Container(
                  margin: const EdgeInsets.symmetric(vertical: 2),
                  decoration: BoxDecoration(
                    color: isSelected ? Colors.teal.shade50 : null,
                    borderRadius: BorderRadius.circular(8),
                    border: isSelected ? Border.all(color: Colors.teal.shade200) : null,
                  ),
                  child: ListTile(
                    dense: true,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    leading: Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: isSelected ? Colors.teal.shade100 : Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Icon(
                        Icons.chat,
                        size: 16,
                        color: isSelected ? Colors.teal.shade700 : Colors.grey.shade600,
                      ),
                    ),
                    title: Text(
                      chat['title'] ?? 'Untitled',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                        color: isSelected ? Colors.teal.shade700 : Colors.black87,
                      ),
                    ),
                    subtitle: Text(
                      _formatTimestamp(chat['timestamp'] ?? 0),
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    trailing: PopupMenuButton<String>(
                      icon: Icon(
                        Icons.more_vert,
                        size: 16,
                        color: Colors.grey.shade600,
                      ),
                      onSelected: (value) {
                        if (value == 'delete') {
                          _deleteChat(index);
                        }
                      },
                      itemBuilder: (context) => [
                        const PopupMenuItem(
                          value: 'delete',
                          child: Row(
                            children: [
                              Icon(Icons.delete, size: 16, color: Colors.red),
                              SizedBox(width: 8),
                              Text('Delete'),
                            ],
                          ),
                        ),
                      ],
                    ),
                    onTap: () => _loadChat(index),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('Ask AI'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          // Toggle streaming mode (optional)
          PopupMenuButton<String>(
            onSelected: (value) {
              // You can add settings here
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'streaming',
                child: Row(
                  children: [
                    Icon(Icons.stream, size: 16),
                    SizedBox(width: 8),
                    Text('Streaming Mode'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Row(
        children: [
          _buildSidebar(),
          
          // Main Chat Area
          Expanded(
            child: Column(
              children: [
                // Chat Messages or Welcome Screen
                Expanded(
                  child: _messages.isEmpty 
                    ? _buildWelcomeScreen()
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(16),
                        itemCount: _messages.length,
                        itemBuilder: (context, index) {
                          final message = _messages[index];
                          final isUser = message['isUser'] ?? false;

                          // Handle status messages
                          if (message['isStatus'] == true) {
                            return Align(
                              alignment: Alignment.centerLeft,
                              child: _buildStatusMessage(message),
                            );
                          }

                          // Handle legacy typing indicator
                          if (message['isTyping'] == true) {
                            return Align(
                              alignment: Alignment.centerLeft,
                              child: Container(
                                margin: const EdgeInsets.symmetric(vertical: 8),
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.05),
                                      blurRadius: 10,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                                child: const TypingIndicator(),
                              ),
                            );
                          }

                          final sources = message['sources'] as List<dynamic>?;
                          final method = message['method'] as String?;
                          final timeTaken = message['timeTaken'] as double?;

                          return Align(
                            alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                            child: Column(
                              crossAxisAlignment: isUser
                                  ? CrossAxisAlignment.end
                                  : CrossAxisAlignment.start,
                              children: [
                                Container(
                                  constraints: BoxConstraints(
                                    maxWidth: MediaQuery.of(context).size.width * 0.7,
                                  ),
                                  margin: const EdgeInsets.symmetric(vertical: 8),
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    gradient: isUser
                                        ? LinearGradient(
                                            colors: [Colors.teal.shade400, Colors.teal.shade500],
                                          )
                                        : null,
                                    color: isUser ? null : Colors.white,
                                    borderRadius: BorderRadius.circular(16),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.05),
                                        blurRadius: 10,
                                        offset: const Offset(0, 2),
                                      ),
                                    ],
                                  ),
                                  child: Text(
                                    message['text'],
                                    style: TextStyle(
                                      color: isUser ? Colors.white : Colors.black87,
                                      fontSize: 15,
                                    ),
                                  ),
                                ),
                                
                                // Show method and timing info
                                if (!isUser && (method != null || timeTaken != null))
                                  Padding(
                                    padding: const EdgeInsets.only(left: 16, bottom: 4),
                                    child: Row(
                                      children: [
                                        if (method != null)
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            decoration: BoxDecoration(
                                              color: method == 'web_search' ? Colors.green.shade100 : Colors.blue.shade100,
                                              borderRadius: BorderRadius.circular(8),
                                            ),
                                            child: Text(
                                              method == 'web_search' ? 'Web' : 'Local',
                                              style: TextStyle(
                                                fontSize: 10,
                                                color: method == 'web_search' ? Colors.green.shade700 : Colors.blue.shade700,
                                                fontWeight: FontWeight.w500,
                                              ),
                                            ),
                                          ),
                                        if (method != null && timeTaken != null) const SizedBox(width: 8),
                                        if (timeTaken != null)
                                          Text(
                                            '${timeTaken.toStringAsFixed(1)}s',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.grey.shade600,
                                            ),
                                          ),
                                      ],
                                    ),
                                  ),
                                
                                // Sources
                                if (!isUser && sources != null && sources.isNotEmpty)
                                  Padding(
                                    padding: const EdgeInsets.only(left: 16, bottom: 8),
                                    child: Wrap(
                                      spacing: 8,
                                      children: sources.map((src) {
                                        return MouseRegion(
                                          cursor: SystemMouseCursors.click,
                                          child: GestureDetector(
                                            onTap: () => launchUrl(Uri.parse(src)),
                                            child: AnimatedContainer(
                                              duration: const Duration(milliseconds: 200),
                                              padding: const EdgeInsets.symmetric(
                                                horizontal: 8, vertical: 4),
                                              decoration: BoxDecoration(
                                                color: Colors.blue.shade50,
                                                borderRadius: BorderRadius.circular(12),
                                                border: Border.all(color: Colors.blue.shade200),
                                                boxShadow: [
                                                  BoxShadow(
                                                    color: Colors.blue.withOpacity(0.1),
                                                    blurRadius: 4,
                                                    offset: const Offset(0, 2),
                                                  ),
                                                ],
                                              ),
                                              child: Text(
                                                _getDomain(src),
                                                style: TextStyle(
                                                  color: Colors.blue.shade700,
                                                  fontSize: 12,
                                                  fontWeight: FontWeight.w500,
                                                ),
                                              ),
                                            ),
                                          ),
                                        );
                                      }).toList(),
                                    ),
                                  ),
                              ],
                            ),
                          );
                        },
                      ),
                ),
                
                // Input Area
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border(top: BorderSide(color: Colors.grey.shade200)),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.grey.shade50,
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: TextField(
                            controller: _controller,
                            decoration: const InputDecoration(
                              hintText: "Ask me anything about news...",
                              border: InputBorder.none,
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 20, vertical: 12),
                            ),
                            onSubmitted: (_) => _sendMessageStream(),
                            enabled: !_isTyping,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.teal.shade400, Colors.teal.shade500],
                          ),
                          borderRadius: BorderRadius.circular(24),
                        ),
                        child: IconButton(
                          icon: _isTyping 
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                ),
                              )
                            : const Icon(Icons.send, color: Colors.white),
                          onPressed: _isTyping ? null : _sendMessageStream,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}