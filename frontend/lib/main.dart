import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const NewsAIApp());
}

class NewsAIApp extends StatelessWidget {
  const NewsAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NewsRoom AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.light().copyWith(
        scaffoldBackgroundColor: const Color(0xFFF2F2F2),
        useMaterial3: true,
        colorScheme: ColorScheme.light(
          primary: Colors.tealAccent,
        ),
      ),

      home: const HomeScreen(),
    );
  }
}
