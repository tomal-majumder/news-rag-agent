import 'package:flutter/material.dart';
import '../models/news_article.dart';
import 'package:intl/intl.dart'; // for date formatting
import 'package:url_launcher/url_launcher.dart' as launcher;


class NewsCard extends StatelessWidget {
  final NewsArticle article;

  const NewsCard({super.key, required this.article});

  void _launchURL(String url) async {
    final uri = Uri.parse(url);
    if (await launcher.canLaunchUrl(uri)) {
        await launcher.launchUrl(uri, mode: launcher.LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
        elevation: 3,
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: InkWell(
            onTap: () => _launchURL(article.url),
            borderRadius: BorderRadius.circular(16),
            child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                // TITLE
                Text(
                    article.title,
                    style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                    ),
                ),
                const SizedBox(height: 8),

                // SUMMARY
                Text(
                    article.summary,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                    color: Colors.black54,
                    fontSize: 14,
                    height: 1.4,
                    ),
                ),
                const SizedBox(height: 12),

                // METADATA
                Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                    // Source Chip
                    Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                        color: Colors.teal.shade50,
                        borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                        article.source,
                        style: const TextStyle(fontSize: 12, color: Colors.teal),
                        ),
                    ),

                    // Date
                    Text(
                        DateFormat('MMM d, h:mm a').format(article.publishedAt),
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    ],
                )
                ],
            ),
            ),
        ),
        );

  }
}
