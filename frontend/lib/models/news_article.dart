class NewsArticle {
  final int id;
  final String title;
  final String url;
  final String source;
  final String summary; // This will be the ai_summary from backend
  final String topic;
  final DateTime publishedAt;
  final String? body; // Optional, might not always be included

  NewsArticle({
    required this.id,
    required this.title,
    required this.url,
    required this.source,
    required this.summary,
    required this.topic,
    required this.publishedAt,
    this.body,
  });

  factory NewsArticle.fromJson(Map<String, dynamic> json) {
    return NewsArticle(
      id: json['id'] as int,
      title: json['title'] as String,
      url: json['url'] as String,
      source: json['source'] as String,
      summary: json['ai_summary'] as String, // Backend field is ai_summary
      topic: json['topic'] as String,
      publishedAt: DateTime.parse(json['published_at'] as String),
      body: json['body'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'url': url,
      'source': source,
      'ai_summary': summary,
      'topic': topic,
      'published_at': publishedAt.toIso8601String(),
      'body': body,
    };
  }
}