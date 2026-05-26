# **🐦 Twitter Archive Analyzer**

A Streamlit application for analyzing archived Twitter data using [WaybackTweets]('https://github.com/claromes/waybacktweets') and [Memory.lol]('https://github.com/travisbrown/memory.lol') APIs. This tool helps researchers explore historical Twitter activity with advanced filtering and analysis capabilities.

It is useful for investigating "anonymous" accounts to see if they have previously used a real identity, or for accounts that have deleted posts that are now unavailable on the X GUI. However, this only contains archived data and does not capture all posts or information for an account.

**🔍 Features**
1. Memory.lol Integration

- Account History: View complete profile name history with date ranges
- Multiple Accounts: Detect and display all known account IDs associated with a username
- Timeline Tracking: See when profile names changed over time

2. WaybackTweets Archive Search

- Date Range Filtering: Search tweets between specific dates (YYYYmmdd format)
- Custom Limits: Set maximum number of results to return
- Comprehensive Data: Access archived tweets with full metadata including:
  - Archived timestamps and URLs
  - Original tweet content and URLs
  - Retweet identification
  - Archive status codes and digests

3. Advanced Keyword Filtering

- Multi-keyword Search: Filter tweets using multiple keywords (one per line)
- Case-insensitive Matching: Find all variations of your search terms
- Unique Results: Automatic duplicate removal for clean data
- Keyword Breakdown: See counts for each individual keyword

**📊 Analysis Dashboard**

Real-time Metrics
Date Range: First and last tweet dates in the dataset

Profile Names: Number of unique profile names found

Keyword Matches: Count of tweets matching your search criteria

**Enhanced Analysis Tabs**

📊 Statistics Tab

Retweet Analysis: Count and percentage of retweets vs original content

Activity Span: Total days of Twitter activity in the dataset

Content Metrics:

- Average tweet length
- Total hashtags and mentions
- Links shared
- Average tweets per day
- Peak posting hour

**🕒 Timeline Tab**
Smart Time Grouping: Automatically adjusts display based on date range:

- Daily: For periods under 3 months
- Monthly: For periods under 2 years
- Yearly: For longer time spans
- Interactive Charts: Visualize posting patterns and activity spikes

**🔗 Content Tab**

- Top Mentions: Most frequently mentioned users (Top 10)
- Popular Hashtags: Most used hashtags (Top 10)
- Content Categorization:
- Contains Link: Tweets with URLs
- Standard Tweet: Regular text-only tweets
- Question: Tweets asking questions
- Retweet: Shared content from others
- Multi-mention: Tweets mentioning 2+ users
- Multi-hashtag: Tweets using 2+ hashtags

**💾 Data Export**

Download Options:

- CSV: Comma-separated values for spreadsheet analysis
- JSON: Structured data for developers and APIs
- HTML: Formatted tables for reports and presentations

**🔧 How to Use**

Basic Search:

1. Enter Twitter Username (without @ symbol)
2. Set Date Range using YYYYmmdd format: (Tip: Use account creation date for "From Date")
3. Leave "To Date" empty to search up to today
4. Optional: Set result limit if needed
5. Click "Analyze Twitter Archive"

Advanced Filtering:

- Add Keywords in the sidebar text area (one per line)
- Use Specific Terms for better results
- Combine Multiple Keywords to narrow search
- Review Keyword Breakdown to see individual match counts

**Note**: This tool is designed for research and analysis purposes. Always comply with Twitter's Terms of Service and applicable laws when using archived social media data.
