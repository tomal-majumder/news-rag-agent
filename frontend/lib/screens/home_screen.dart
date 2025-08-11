import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:syncfusion_flutter_datepicker/datepicker.dart';
import 'dart:convert';
import '../widgets/news_card.dart';
import '../widgets/floating_chat_button.dart';
import '../models/news_article.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _searchController = TextEditingController();
  
  // Backend URL - Update this to your actual backend URL
  static const String baseUrl = 'http://127.0.0.1:8000';
  
  bool _isLoadingMore = false;
  bool _isRefreshing = false;
  bool _isInitialLoading = true;
  String _selectedTopic = 'All';
  String _searchQuery = '';
  DateTimeRange? _selectedDateRange;
  
  List<NewsArticle> _articles = [];
  List<String> _topics = ['All'];
  int _currentPage = 1;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_handleScroll);
    _initializeData();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _initializeData() async {
    await Future.wait([
      _loadTopics(),
      _loadNews(isInitial: true),
    ]);
  }

  Future<void> _loadTopics() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/topics'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _topics = List<String>.from(data['topics']);
        });
      }
    } catch (e) {
      print('Error loading topics: $e');
    }
  }

  void _handleScroll() {
    if (_scrollController.position.pixels >= 
        _scrollController.position.maxScrollExtent - 100 && 
        !_isLoadingMore && _hasMore) {
      _loadMoreNews();
    }
  }

  Future<void> _loadNews({bool isInitial = false, bool isRefresh = false}) async {
    if (isRefresh) {
      setState(() {
        _isRefreshing = true;
        _currentPage = 1;
        _hasMore = true;
      });
    } else if (isInitial) {
      setState(() => _isInitialLoading = true);
    }

    try {
      final queryParams = <String, String>{
        'page': _currentPage.toString(),
        'limit': '20',
      };

      // Add filters
      if (_selectedTopic != 'All') {
        queryParams['topic'] = _selectedTopic;
      }
      if (_searchQuery.isNotEmpty) {
        queryParams['search'] = _searchQuery;
      }
      // Add date range filtering
      if (_selectedDateRange != null) {
        queryParams['start_date'] = _selectedDateRange!.start.toIso8601String().split('T')[0];
        queryParams['end_date'] = _selectedDateRange!.end.toIso8601String().split('T')[0];
      }

      final uri = Uri.parse('$baseUrl/api/news').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> articlesJson = data['articles'];
        final List<NewsArticle> newArticles = articlesJson
            .map((json) => NewsArticle.fromJson(json))
            .toList();

        setState(() {
          if (isRefresh || isInitial) {
            _articles = newArticles;
          } else {
            _articles.addAll(newArticles);
          }
          _hasMore = data['has_more'] ?? false;
          _currentPage = data['page'] ?? 1;
        });
      } else {
        throw Exception('Failed to load news: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading news: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to load news: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() {
        _isInitialLoading = false;
        _isRefreshing = false;
      });
    }
  }

  Future<void> _loadMoreNews() async {
    setState(() => _isLoadingMore = true);
    
    _currentPage++;
    await _loadNews();
    
    setState(() => _isLoadingMore = false);
  }

  Future<void> _refreshNews() async {
    await _loadNews(isRefresh: true);
  }

  void _applyFilters() {
    setState(() {
      _currentPage = 1;
      _hasMore = true;
    });
    _loadNews(isRefresh: true);
  }

  void _showSyncfusionDateRangePicker() async {
    await showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Select Date Range'),
          content: Container(
            height: 400,
            width: 350,
            child: SfDateRangePicker(
              view: DateRangePickerView.month,
              selectionMode: DateRangePickerSelectionMode.range,
              showActionButtons: true,
              onCancel: () {
                Navigator.of(context).pop();
              },
              onSubmit: (Object? value) {
                if (value != null && value is PickerDateRange) {
                  final startDate = value.startDate;
                  final endDate = value.endDate ?? value.startDate;
                  
                  if (startDate != null && endDate != null) {
                    setState(() {
                      _selectedDateRange = DateTimeRange(
                        start: startDate,
                        end: endDate,
                      );
                    });
                    _applyFilters();
                  }
                }
                Navigator.of(context).pop();
              },
              initialSelectedRange: _selectedDateRange != null
                  ? PickerDateRange(
                      _selectedDateRange!.start,
                      _selectedDateRange!.end,
                    )
                  : null,
              minDate: DateTime.now().subtract(const Duration(days: 365 * 50)),
              maxDate: DateTime.now(),
              monthCellStyle: DateRangePickerMonthCellStyle(
                todayTextStyle: TextStyle(
                  color: Colors.teal.shade700,
                  fontWeight: FontWeight.bold,
                ),
              ),
              rangeSelectionColor: Colors.teal.shade100,
              startRangeSelectionColor: Colors.teal.shade600,
              endRangeSelectionColor: Colors.teal.shade600,
              selectionColor: Colors.teal.shade600,
              todayHighlightColor: Colors.teal.shade300,
              headerStyle: DateRangePickerHeaderStyle(
                textStyle: TextStyle(
                  color: Colors.teal.shade700,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  void _clearFilters() {
    setState(() {
      _selectedTopic = 'All';
      _searchQuery = '';
      _selectedDateRange = null;
      _searchController.clear();
      _currentPage = 1;
      _hasMore = true;
    });
    _loadNews(isRefresh: true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text("NewsRoom AI", style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refreshNews,
          ),
        ],
      ),
      body: Column(
        children: [
          // Enhanced Filter Section
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Search Bar
                Container(
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: "Search news articles...",
                      prefixIcon: const Icon(Icons.search, color: Colors.grey),
                      suffixIcon: _searchQuery.isNotEmpty 
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Colors.grey),
                            onPressed: () {
                              _searchController.clear();
                              setState(() => _searchQuery = '');
                              _applyFilters();
                            },
                          )
                        : null,
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    onChanged: (value) {
                      setState(() => _searchQuery = value);
                    },
                    onSubmitted: (value) => _applyFilters(),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Topics Filter
                Row(
                  children: [
                    const Text(
                      'Topics:',
                      style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: SizedBox(
                        height: 40,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: _topics.length,
                          itemBuilder: (context, index) {
                            final topic = _topics[index];
                            final isSelected = _selectedTopic == topic;
                            
                            return Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: FilterChip(
                                label: Text(topic),
                                selected: isSelected,
                                onSelected: (selected) {
                                  setState(() => _selectedTopic = topic);
                                  _applyFilters();
                                },
                                backgroundColor: Colors.grey.shade200,
                                selectedColor: Colors.teal.shade100,
                                checkmarkColor: Colors.teal.shade700,
                                labelStyle: TextStyle(
                                  color: isSelected ? Colors.teal.shade700 : Colors.black87,
                                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 12),
                
                // Date Range and Clear Filters
                Row(
                  children: [
                    // Date Range Button with better styling - Now uses Syncfusion picker
                    OutlinedButton.icon(
                      onPressed: _showSyncfusionDateRangePicker,
                      icon: Icon(Icons.date_range, size: 16, color: Colors.teal.shade700),
                      label: Text(
                        _selectedDateRange == null 
                          ? 'Date Range' 
                          : '${_selectedDateRange!.start.day}/${_selectedDateRange!.start.month} - ${_selectedDateRange!.end.day}/${_selectedDateRange!.end.month}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.teal.shade700,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        side: BorderSide(color: Colors.teal.shade300),
                        backgroundColor: _selectedDateRange != null 
                          ? Colors.teal.shade50 
                          : Colors.white,
                      ),
                    ),
                    const SizedBox(width: 8),
                    
                    if (_selectedTopic != 'All' || _searchQuery.isNotEmpty || _selectedDateRange != null)
                      TextButton.icon(
                        onPressed: _clearFilters,
                        icon: const Icon(Icons.clear, size: 16),
                        label: const Text('Clear', style: TextStyle(fontSize: 12)),
                        style: TextButton.styleFrom(
                          foregroundColor: Colors.red.shade600,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                      ),
                    
                    const Spacer(),
                    
                    // Results Count
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.teal.shade50,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '${_articles.length} articles',
                        style: TextStyle(
                          color: Colors.teal.shade700,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          // News List
          Expanded(
            child: _isInitialLoading 
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(color: Colors.teal),
                      SizedBox(height: 16),
                      Text('Loading news articles...'),
                    ],
                  ),
                )
              : _isRefreshing 
                ? const Center(child: CircularProgressIndicator(color: Colors.teal))
                : _articles.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.article_outlined, size: 64, color: Colors.grey.shade400),
                          const SizedBox(height: 16),
                          Text(
                            'No articles found',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey.shade600,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Try adjusting your filters or check your connection',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey.shade500,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: _refreshNews,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.teal,
                              foregroundColor: Colors.white,
                            ),
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _refreshNews,
                      color: Colors.teal,
                      child: ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.only(top: 8, bottom: 80),
                        itemCount: _articles.length + (_isLoadingMore ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (_isLoadingMore && index == _articles.length) {
                            return Container(
                              padding: const EdgeInsets.all(24),
                              alignment: Alignment.center,
                              child: const CircularProgressIndicator(color: Colors.teal),
                            );
                          }
                          
                          return EnhancedNewsCard(article: _articles[index]);
                        },
                      ),
                    ),
          ),
        ],
      ),
      floatingActionButton: const FloatingChatButton(),
    );
  }
}

// Enhanced News Card - Shows AI summary by default, click title for full article
class EnhancedNewsCard extends StatelessWidget {
  final NewsArticle article;

  const EnhancedNewsCard({super.key, required this.article});

  void _openFullArticle(BuildContext context, String url) async {
    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        // Fallback - show a snackbar
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Could not open article: $url'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error opening article: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Main Content
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Topic Tag
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getTopicColor(article.topic),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    article.topic,
                    style: TextStyle(
                      color: _getTopicTextColor(article.topic),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // Clickable Title - Opens full article
                MouseRegion(
                  cursor: SystemMouseCursors.click,
                  child: GestureDetector(
                    onTap: () => _openFullArticle(context, article.url),
                    child: Text(
                      article.title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                        height: 1.3,
                        decoration: TextDecoration.underline,
                        decorationColor: Colors.blue,
                      ),
                    ),
                  ),
                ),
                
                const SizedBox(height: 8),
                
                // AI-Generated Summary (always shown)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade100),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.auto_awesome, 
                            size: 16, 
                            color: Colors.blue.shade700),
                          const SizedBox(width: 4),
                          Text(
                            'AI Summary',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Colors.blue.shade700,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        article.summary, // This is the AI-generated summary from backend
                        style: TextStyle(
                          color: Colors.blue.shade800,
                          fontSize: 14,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // Metadata Row
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Source
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        article.source,
                        style: const TextStyle(fontSize: 12, color: Colors.black87),
                      ),
                    ),
                    
                    // Date
                    Text(
                      _formatDate(article.publishedAt),
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          // Action Footer
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: const BorderRadius.only(
                bottomLeft: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
            ),
            child: Row(
              children: [
                Icon(Icons.info_outline, size: 14, color: Colors.grey.shade600),
                const SizedBox(width: 4),
                Text(
                  'Click title to read full article',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                    fontStyle: FontStyle.italic,
                  ),
                ),
                const Spacer(),
                MouseRegion(
                  cursor: SystemMouseCursors.click,
                  child: GestureDetector(
                    onTap: () => _openFullArticle(context, article.url),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.teal,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.open_in_new, size: 14, color: Colors.white),
                          SizedBox(width: 4),
                          Text(
                            'Read Full',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getTopicColor(String topic) {
    switch (topic.toLowerCase()) {
      case 'technology':
        return Colors.blue.shade100;
      case 'business':
        return Colors.green.shade100;
      case 'health':
        return Colors.red.shade100;
      case 'environment':
        return Colors.teal.shade100;
      case 'politics':
        return Colors.purple.shade100;
      case 'sports':
        return Colors.orange.shade100;
      case 'entertainment':
        return Colors.pink.shade100;
      case 'science':
        return Colors.indigo.shade100;
      default:
        return Colors.grey.shade100;
    }
  }

  Color _getTopicTextColor(String topic) {
    switch (topic.toLowerCase()) {
      case 'technology':
        return Colors.blue.shade700;
      case 'business':
        return Colors.green.shade700;
      case 'health':
        return Colors.red.shade700;
      case 'environment':
        return Colors.teal.shade700;
      case 'politics':
        return Colors.purple.shade700;
      case 'sports':
        return Colors.orange.shade700;
      case 'entertainment':
        return Colors.pink.shade700;
      case 'science':
        return Colors.indigo.shade700;
      default:
        return Colors.grey.shade700;
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    // Handle future dates (shouldn't happen but just in case)
    if (difference.isNegative) {
      return 'Just now';
    }
    
    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else if (difference.inDays < 30) {
      final weeks = (difference.inDays / 7).floor();
      return '${weeks}w ago';
    } else if (difference.inDays < 365) {
      final months = (difference.inDays / 30).floor();
      return '${months}mo ago';
    } else {
      // For very old dates, show the actual date
      return '${date.day}/${date.month}/${date.year}';
    }
  }
}