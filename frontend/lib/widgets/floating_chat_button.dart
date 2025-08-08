import 'package:flutter/material.dart';
import '../screens/chat_modal.dart';

class FloatingChatButton extends StatelessWidget {
  const FloatingChatButton({super.key});

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      backgroundColor: Colors.tealAccent,
      child: const Icon(Icons.chat_bubble_outline, color: Colors.black87),
      onPressed: () {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const ChatModal()),
        );
      },
    );
  }
}
