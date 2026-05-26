import streamlit as st
import pandas as pd
from waybacktweets import WaybackTweets, TweetsParser, TweetsExporter
from datetime import datetime
import requests
from pandas import json_normalize
from utils.utils import rotate_headers
import re
import hmac

# ----- SECURITY -----
# Password protection function
def check_password():
    """Returns True if the user has the correct password."""
    
    def password_entered():
        """Check if the password is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["passwords"]["main_password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Return True if password is correct.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.title("🔒 Twitter Archive Analyzer")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("❌ Password incorrect")
    return False

# Check password before running the app
if not check_password():
    st.stop()

# Set page configuration
st.set_page_config(
    page_title="Twitter Archive Analyzer",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----- COLLECTION -----
# Step 1: Memory.lol API call
def get_memorylol_account_info(username):
    """
    Get account information from Memory.lol API
    
    Args:
        username (str): Twitter username without @
        
    Returns:
        dict: Account information or None if error
    """
    
    headers = rotate_headers()
    
    try:
        url = f"https://api.memory.lol/v1/tw/{username}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except Exception as e:
        st.error(f"❌ Error fetching Memory.lol data: {e}")
        return None

# Display Memory.lol results
def display_memorylol_summary(username):
    """
    Display formatted summary of Memory.lol account information
    """
    account_info = get_memorylol_account_info(username)
    
    if not account_info:
        st.warning(f"No account information found for @{username}")
        return None
    
    # Create summary data for dashboard
    summary_data = {
        'username': username,
        'total_accounts': 0,
        'known_screen_names': [],
        'account_ids': []
    }
    
    if 'accounts' in account_info and account_info['accounts']:
        summary_data['total_accounts'] = len(account_info['accounts'])
        
        for i, account in enumerate(account_info['accounts'], 1):
            summary_data['account_ids'].append(account.get('id_str', 'N/A'))
            
            if 'screen_names' in account:
                for name, dates in account['screen_names'].items():
                    date_range = " to ".join(dates) if len(dates) > 1 else f"since {dates[0]}"
                    summary_data['known_screen_names'].append({
                        'name': name,
                        'date_range': date_range
                    })
    
    return summary_data

# Step 2: Fetch and parse tweets using WaybackTweets
def get_waybacktweets_archive(username, from_date=None, to_date=None, limit=None):
    """
    Get archived tweets using WaybackTweets
    
    Args:
        username (str): Twitter username without @
        from_date (str): Start date in YYYYmmdd format
        to_date (str): End date in YYYYmmdd format
        limit (int): Maximum number of results
        
    Returns:
        tuple: (parsed_tweets, dataframe) or (None, None) if error
    """
    try:
        # Initialize API with parameters
        api_params = {'username': username}
        
        if from_date:
            api_params['timestamp_from'] = from_date
        if to_date:
            api_params['timestamp_to'] = to_date
        if limit:
            api_params['limit'] = limit
            
        api = WaybackTweets(**api_params)
        archived_tweets = api.get()
        
        if not archived_tweets:
            st.warning("No archived tweets found.")
            return None, None
        
        # Define fields to include
        field_options = [
            "archived_urlkey",
            "archived_timestamp",
            "parsed_archived_timestamp",
            "archived_tweet_url",
            "parsed_archived_tweet_url",
            "original_tweet_url",
            "parsed_tweet_url",
            "available_tweet_text",
            "available_tweet_is_RT",
            "available_tweet_info",
            "resumption_key",
        ]
        
        # Parse tweets
        parser = TweetsParser(archived_tweets, username, field_options)
        parsed_tweets = parser.parse()
        
        # Create dataframe using WaybackTweets method
        df = None
        
        # Approach 1: Use TweetsExporter to create dataframe
        try:
            exporter = TweetsExporter(parsed_tweets, username, field_options)
            # Check if TweetsExporter has a method to get dataframe
            if hasattr(exporter, '_create_dataframe'):
                df = exporter._create_dataframe()
            elif hasattr(exporter, 'dataframe'):
                df = exporter.dataframe
            else:
                # Try to access the dataframe attribute directly
                df = exporter.df if hasattr(exporter, 'df') else None
        except Exception as e:
            st.warning(f"Could not create dataframe via TweetsExporter: {e}")
        
        # Approach 2: If above fails, try to create dataframe manually
        if df is None:
            try:
                # Normalize the JSON data
                df = json_normalize(parsed_tweets)
            except Exception as e:
                st.warning(f"Could not normalize JSON: {e}")
                # Last resort: try direct conversion with error handling
                try:
                    df = pd.DataFrame(parsed_tweets)
                except ValueError as e:
                    st.error(f"Could not create dataframe: {e}")
                    df = None
        
        return parsed_tweets, df
        
    except Exception as e:
        st.error(f"❌ Error fetching WaybackTweets data: {e}")
        return None, None

# Parse Wayback Tweets results to dataframe
def export_to_dataframe(parsed_tweets, username):
    """
    Convert parsed tweets to pandas DataFrame using WaybackTweets' methods
    """
    if not parsed_tweets:
        return pd.DataFrame()
    
    # Define field options
    field_options = [
        "archived_urlkey",
        "archived_timestamp",
        "parsed_archived_timestamp",
        "archived_tweet_url",
        "parsed_archived_tweet_url",
        "original_tweet_url",
        "parsed_tweet_url",
        "available_tweet_text",
        "available_tweet_is_RT",
        "available_tweet_info",
        "archived_mimetype",
        "archived_statuscode",
        "archived_digest",
        "archived_length",
        "resumption_key",
    ]
    
    try:
        # Use TweetsExporter to handle dataframe creation
        exporter = TweetsExporter(parsed_tweets, username, field_options)
        
        # Try different methods to get the dataframe
        if hasattr(exporter, '_create_dataframe'):
            df = exporter._create_dataframe()
        elif hasattr(exporter, 'dataframe'):
            df = exporter.dataframe
        elif hasattr(exporter, 'df'):
            df = exporter.df
        else:
            # Fallback: try to access the dataframe after export
            exporter.save_to_csv()  # This might create the dataframe internally
            if hasattr(exporter, 'df'):
                df = exporter.df
            else:
                # Last resort: manual conversion
                df = pd.DataFrame(parsed_tweets)
        
        return df
        
    except Exception as e:
        st.error(f"Error creating dataframe: {e}")
        # Try manual conversion as fallback
        try:
            return pd.DataFrame(parsed_tweets)
        except:
            return pd.DataFrame()

# Filter dataframe for posts that contain keyword(s)
def filter_tweets_by_keywords(df, keywords):
    """
    Filter tweets by keywords, returning unique matches with matched keywords.
    """
    if df.empty:
        return pd.DataFrame()
    
    mask = pd.Series([False] * len(df))
    matched_keywords = pd.Series([[] for _ in range(len(df))])  # Initialize empty lists for each row
    
    for kw in keywords:
        if 'available_tweet_text' in df.columns and df['available_tweet_text'].dtype == 'object':
            kw_mask = df['available_tweet_text'].str.contains(kw, case=False, na=False)
            mask |= kw_mask
            
            # Add matched keyword to the list for rows that match
            for idx in kw_mask[kw_mask].index:
                matched_keywords[idx] = matched_keywords[idx] + [kw]
    
    filtered_df_total = df[mask].copy()  # Use copy to avoid SettingWithCopyWarning
    
    # Add matched_keyword column - join multiple keywords with comma
    filtered_df_total.loc[:, 'matched_keyword'] = matched_keywords[mask].apply(
        lambda kw_list: ', '.join(kw_list) if kw_list else 'No match'
    )
    
    # Remove duplicates (keeping the first occurrence)
    filtered_df_total = filtered_df_total.drop_duplicates()

    return filtered_df_total

# Main app
def main():
    st.title("🐦 Twitter Archive Analyzer")
    st.markdown("Analyze archived Twitter data using WaybackTweets and Memory.lol APIs")
    
    # Sidebar
    st.sidebar.header("Search Parameters")
    
    USERNAME = st.sidebar.text_input("Twitter Username (without @)", value=None, placeholder="e.g., realdonaldtrump")
    FROM_DATE = st.sidebar.text_input("From Date (YYYYmmdd)",value=None, placeholder="20250601", help="Tip: Use the account's creation date")
    TO_DATE = st.sidebar.text_input("To Date (YYYYmmdd)", value=None, placeholder="20250926", help="Tip: Leave empty for up to today")

    # Handle empty TO_DATE - use today's date if empty
    if TO_DATE is None or TO_DATE.strip() == "":
        TO_DATE = datetime.now().strftime("%Y%m%d")
        st.sidebar.info(f"If empty, using today's date: {TO_DATE}")
    
    LIMIT = st.sidebar.number_input("Limit (optional)", min_value=1, value=None, placeholder="Leave empty for no limit", help="Sets the maximum number of results to return")
    
    # Keywords for filtering
    st.sidebar.header("Keyword Filtering")
    keywords_input = st.sidebar.text_area(
        "Keywords (one per line)",
        value=None,
        placeholder="CEO\nelites\nmanager\nmanagement\nexecutive\ndirector\nboard",
        help="Enter keywords to filter tweets, one per line"
    )

    # Handle None case and empty input
    if keywords_input is None or keywords_input.strip() == "":
        keywords = []
    else:
        keywords = [kw.strip() for kw in keywords_input.split('\n') if kw.strip()]
    
    # Analyze button
    if st.sidebar.button("🚀 Analyze Twitter Archive", type="primary"):
        if not USERNAME:
            st.error("Please enter a Twitter username")
            return
        
        # Show loading spinner
        with st.spinner("Analyzing Twitter archive...", show_time=True):
            # Step 1: Get Memory.lol account information
            st.subheader("1. 🔍 Memory.lol Account History")
            memorylol_data = display_memorylol_summary(USERNAME)

            # Display Memory.lol summary if available
            if memorylol_data and memorylol_data['known_screen_names']:
                st.subheader("👤 Profile Name History")
                for name_info in memorylol_data['known_screen_names']:
                    st.write(f"**@{name_info['name']}** - {name_info['date_range']}")
            else:
                st.info(f"No known screen names found for @{USERNAME}")
            
            # Step 2: Get WaybackTweets archive
            st.subheader("2. 📂 Archived Tweets Search")
            parsed_tweets, df = get_waybacktweets_archive(
                username=USERNAME,
                from_date=FROM_DATE,
                to_date=TO_DATE,
                limit=LIMIT
            )
            
            if parsed_tweets and df is not None:
                # Convert timestamp once, right after getting the dataframe
                if 'archived_timestamp' in df.columns:
                    try:
                        df['archived_timestamp'] = pd.to_datetime(df['archived_timestamp'], format='%Y%m%d%H%M%S', errors='coerce')
                    except Exception as e:
                        st.error(f"❌ Error converting archived_timestamp: {e}")
                
                st.success(f"✅ Found {len(df)} archived tweets")

                # Filter by keywords: Always define filtered_df
                if keywords and not df.empty:
                    filtered_df = filter_tweets_by_keywords(df, keywords)
                    st.info(f"🔍 Found {len(filtered_df)} tweets matching your keywords")
                    st.dataframe(df.head(5))  # Show sample of original dataframe
                    
                    # Download buttons for full dataset (not just filtered)
                    st.subheader("💾 Download Full Dataset")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # CSV download for full dataset
                        csv_full = df.to_csv(index=False)
                        st.download_button(
                            label="Download Full CSV",
                            data=csv_full,
                            file_name=f"{USERNAME}_FULL_tweets_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
                            mime="text/csv",
                            help="Download the complete dataset (not filtered by keywords)"
                        )
                    
                    with col2:
                        # JSON download for full dataset
                        json_full = df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="Download Full JSON",
                            data=json_full,
                            file_name=f"{USERNAME}_FULL_tweets_{datetime.now().strftime('%Y%m%d%H%M%S')}.json",
                            mime="application/json",
                            help="Download the complete dataset (not filtered by keywords)"
                        )
                    
                    with col3:
                        # HTML download for full dataset
                        html_full = df.to_html(index=False)
                        st.download_button(
                            label="Download Full HTML",
                            data=html_full,
                            file_name=f"{USERNAME}_FULL_tweets_{datetime.now().strftime('%Y%m%d%H%M%S')}.html",
                            mime="text/html",
                            help="Download the complete dataset (not filtered by keywords)"
                        )
                    
                else:
                    filtered_df = df  # If no keywords, use full dataframe
                    st.info("ℹ️ Showing all tweets (no keyword filtering applied)")
                
                # Analysis Dashboard
                st.subheader("📊 Analysis Dashboard")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if 'archived_timestamp' in df.columns and not df['archived_timestamp'].isna().all():
                        first_post = df['archived_timestamp'].min()
                        last_post = df['archived_timestamp'].max()
                        st.metric("Date Range", f"{first_post.strftime('%Y-%m-%d')} to {last_post.strftime('%Y-%m-%d')}")
                    else:
                        st.metric("Date Range", "N/A")
                
                with col2:
                    if (
                        'available_tweet_info' in df.columns
                        and 'available_tweet_is_RT' in df.columns
                        and df['available_tweet_info'].notna().any()
                    ):
                        # Only consider rows where available_tweet_is_RT is False
                        name_df = df[(df['available_tweet_is_RT'] == False) & df['available_tweet_info'].notna()]
                        name_pattern = r"^(.*?)\s+\(@"
                        names = name_df['available_tweet_info'].apply(
                            lambda x: re.match(name_pattern, x).group(1) if re.match(name_pattern, x) else None
                        )
                        unique_names = names.dropna().unique()
                        st.metric("Profile Names Found", len(unique_names))
                    else:
                        st.metric("Profile Names Found", 0)
                
                with col3:
                    # This is the CORRECT keyword matches count
                    if keywords:
                        st.metric("Keyword Matches", len(filtered_df))
                    else:
                        st.metric("Keyword Matches", "N/A")
                
                # Enhanced Analysis Section
                st.subheader("🔍 Enhanced Analysis")

                if not df.empty:
                    # Create tabs for different analyses
                    tab1, tab2, tab3 = st.tabs(["📊 Statistics", "🕒 Timeline", "🔗 Content"])
                    
                    with tab1:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if 'available_tweet_is_RT' in df.columns:
                                rt_count = (df['available_tweet_is_RT'] == True).sum()
                                st.metric("Retweets", f"{rt_count} ({rt_count/len(df)*100:.1f}%)")
                        
                        with col2:
                            if 'archived_timestamp' in df.columns:
                                days_span = (df['archived_timestamp'].max() - df['archived_timestamp'].min()).days
                                st.metric("Archived Activity Span", f"{days_span} days")
                        
                        with col3:
                            if 'available_tweet_text' in df.columns:
                                avg_length = df['available_tweet_text'].str.len().mean()
                                st.metric("Avg Length", f"{avg_length:.0f} chars")
                        
                        # Additional stats in a second row
                        col4, col5, col6 = st.columns(3)

                        with col4:
                            if 'available_tweet_text' in df.columns:
                                hashtag_count = df['available_tweet_text'].str.count('#').sum()
                                st.metric("Total Hashtags", hashtag_count)                        
                        
                        with col5:
                            if 'available_tweet_text' in df.columns:
                                mention_count = df['available_tweet_text'].str.count('@').sum()
                                st.metric("Total Mentions", mention_count)
                        
                        with col6:
                            if 'available_tweet_text' in df.columns:
                                url_count = df['available_tweet_text'].str.count('http').sum()
                                st.metric("Links Shared", url_count)
                        
                    with tab2:
                        if 'archived_timestamp' in df.columns:
                            # Smart time grouping based on date range
                            date_range_days = (df['archived_timestamp'].max() - df['archived_timestamp'].min()).days
                            
                            if date_range_days <= 90:  # Less than 3 months - show daily
                                st.write("**Daily Archived Posts**")
                                time_series = df.set_index('archived_timestamp').resample('D').size()
                                time_series_df = time_series.reset_index()
                                time_series_df.columns = ['date', 'posts']
                                time_series_df = time_series_df.set_index('date')
                                st.bar_chart(time_series_df)
                                st.caption(f"Showing archived activity for {date_range_days} days")
                                
                            elif date_range_days <= 730:  # Less than 2 years - show monthly
                                st.write("**Monthly Archived Posts**")
                                time_series = df.set_index('archived_timestamp').resample('ME').size()
                                time_series_df = time_series.reset_index()
                                time_series_df.columns = ['date', 'posts']
                                time_series_df['date'] = time_series_df['date'].dt.strftime('%Y-%m')
                                time_series_df = time_series_df.set_index('date')
                                st.bar_chart(time_series_df)
                                st.caption(f"Showing monthly activity for {date_range_days//30} months")
                                
                            else:  # More than 2 years - show yearly
                                st.write("**Yearly Archived Posts**")
                                time_series = df.set_index('archived_timestamp').resample('YE').size()
                                time_series_df = time_series.reset_index()
                                time_series_df.columns = ['date', 'posts']
                                time_series_df['date'] = time_series_df['date'].dt.strftime('%Y')
                                time_series_df = time_series_df.set_index('date')
                                st.bar_chart(time_series_df)
                                st.caption(f"Showing yearly activity for {date_range_days//365} years")
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if 'available_tweet_text' in df.columns:
                                # Top mentions
                                mentions = df['available_tweet_text'].str.findall(r'@(\w+)').explode().value_counts().head(10)
                                if not mentions.empty:
                                    st.write("**Top 10 Mentions:**")
                                    for user, count in mentions.items():
                                        st.write(f"@{user}: {count} mentions")
                                else:
                                    st.write("No mentions found")
                        
                        with col2:
                            if 'available_tweet_text' in df.columns:
                                # Top hashtags
                                hashtags = df['available_tweet_text'].str.findall(r'#(\w+)').explode().value_counts().head(10)
                                if not hashtags.empty:
                                    st.write("**Top 10 Hashtags:**")
                                    for tag, count in hashtags.items():
                                        st.write(f"#{tag}: {count} uses")
                                else:
                                    st.write("No hashtags found")
                        
                        # Content type analysis with explanations
                        st.write("**Content Types**")
                        if 'available_tweet_text' in df.columns:
                            def categorize_tweet(text):
                                text = str(text).lower()
                                categories = []
                                if text.startswith('rt @') or ' retweet ' in text:
                                    categories.append('Retweet')
                                if any(term in text for term in ['http://', 'https://', 'www.']):
                                    categories.append('Contains Link')
                                if any(term in text for term in ['?', 'what', 'why', 'how', 'when', 'where', 'who']):
                                    categories.append('Question')
                                if text.count('@') >= 2:  # 2 mentions or more
                                    categories.append('Multi-mention')
                                if text.count('#') >= 2:  # 2 hashtags or more
                                    categories.append('Multi-hashtag')
                                
                                return categories if categories else ['Standard Tweet']
                            
                            all_categories = df['available_tweet_text'].apply(categorize_tweet).explode()
                            category_counts = all_categories.value_counts()
                            
                            # Category explanations
                            category_explanations = {
                                'Contains Link': "Tweets containing URLs or links",
                                'Standard Tweet': "Regular tweets without special characteristics",
                                'Question': "Tweets that ask questions or contain question marks",
                                'Retweet': "Tweets that are retweets of other users",
                                'Multi-mention': "Tweets mentioning 2 or more users",
                                'Multi-hashtag': "Tweets using 2 or more hashtags"
                            }
                            
                            for category, count in category_counts.items():
                                percentage = (count / len(df)) * 100
                                explanation = category_explanations.get(category, "Content category")
                                st.write(f"**{category}**: {count} tweets ({percentage:.1f}%)")
                                st.caption(f"*{explanation}*")
                
                # Display dataframe
                st.subheader("📋 Keyword Matches Data")
                if not filtered_df.empty:
                    st.dataframe(filtered_df, width='stretch')
                    
                    # Download buttons
                    st.subheader("💾 Download Filtered Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # CSV download
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"{USERNAME}_tweets_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        # JSON download
                        json_str = filtered_df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=f"{USERNAME}_tweets_{datetime.now().strftime('%Y%m%d%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    with col3:
                        # HTML download
                        html = filtered_df.to_html(index=False)
                        st.download_button(
                            label="Download HTML",
                            data=html,
                            file_name=f"{USERNAME}_tweets_{datetime.now().strftime('%Y%m%d%H%M%S')}.html",
                            mime="text/html"
                        )
                    
                    # Show keyword breakdown if keywords were used
                    if keywords:
                        st.subheader("🔍 Keyword Breakdown")
                        keyword_counts = {}
                        for kw in keywords:
                            if 'available_tweet_text' in df.columns and df['available_tweet_text'].dtype == 'object':
                                # Count unique tweets containing each keyword
                                count = len(df[df['available_tweet_text'].str.contains(kw, case=False, na=False)])
                                keyword_counts[kw] = count
                            else:
                                keyword_counts[kw] = 0
                        
                        keyword_df = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])
                        st.dataframe(keyword_df, width='stretch')
                        
                else:
                    st.warning("No data to display after filtering.")
                
            else:
                st.error("❌ No archived tweets found for the specified criteria.")
    
    # Instructions
    st.sidebar.markdown("---")
    st.sidebar.subheader("Instructions")
    st.sidebar.markdown("""
    1. Enter Twitter username (without @)
    2. Set date range in YYYYmmdd format
    3. Optional: Set limit and keywords
    4. Click 'Analyze Twitter Archive'
    5. View results and download data
    """)

if __name__ == "__main__":
    main()
