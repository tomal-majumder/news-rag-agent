import 'package:flutter/material.dart';

class FilterBar extends StatelessWidget {
  const FilterBar({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Row(
        children: const [
          Text("Filter bar coming soon...", style: TextStyle(color: Colors.white54)),
        ],
      ),
    );
  }
}
