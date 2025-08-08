import 'package:flutter/material.dart';

class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> dotOneAnim;
  late Animation<double> dotTwoAnim;
  late Animation<double> dotThreeAnim;

  @override
  void initState() {
    super.initState();
    _controller =
        AnimationController(duration: const Duration(milliseconds: 1500), vsync: this)
          ..repeat();

    dotOneAnim = Tween<double>(begin: 0, end: -4).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.0, 0.3, curve: Curves.easeOut)),
    );
    dotTwoAnim = Tween<double>(begin: 0, end: -4).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.2, 0.5, curve: Curves.easeOut)),
    );
    dotThreeAnim = Tween<double>(begin: 0, end: -4).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.4, 0.7, curve: Curves.easeOut)),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _buildDot(Animation<double> animation) {
    return AnimatedBuilder(
      animation: animation,
      builder: (_, __) => Transform.translate(
        offset: Offset(0, animation.value),
        child: const Padding(
          padding: EdgeInsets.symmetric(horizontal: 2),
          child: CircleAvatar(radius: 4, backgroundColor: Colors.grey),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _buildDot(dotOneAnim),
        _buildDot(dotTwoAnim),
        _buildDot(dotThreeAnim),
      ],
    );
  }
}
