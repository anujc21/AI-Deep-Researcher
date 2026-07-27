import streamlit as st
from agents.research_agent import web_research_tool
from agents.drafting_agent import get_drafting_llm, draft_answer
from dotenv import load_dotenv
import time
import json
import pandas as pd
from datetime import datetime
import plotly.express as px

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Deep Researcher",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Set a default text color for all content */
    body, p, div, span, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;
    }
    
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #00b4d8;
    }
    
    .sub-header {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 0.6rem;
        margin-bottom: 1.2rem;
        color: #FFFFFF;
    }
    
    .card {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: #FFFFFF;
    }
    
    .research-card {
        background-color: #f0f7ff;
        border-left: 5px solid #3b82f6;
        color: #1e3a8a; /* Darker blue text for contrast */
    }
            
    .process-card{
        color: #FFFFFF;
        padding:20px;
    }
    
    .answer-card {
        background-color: #ecfdf5;
        border-left: 5px solid #10b981;
        color: #065f46; /* Darker green text for contrast */
    }
    
    /* Ensure all content inside cards has proper color */
    .card p, .card div, .card span, .card li {
        color: inherit;
    }
    
    .query-text {
        font-size: 1.2rem;
        font-weight: 600;
        color: #4b5563;
    }
    
    .timestamp {
        font-size: 0.8rem;
        color: #6b7280;
        font-style: italic;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        color: inherit; /* Inherit button text color from Streamlit */
    }
    
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #00b4d8;
    }
    
    .highlight {
        background-color: #ffffff;
        padding: 2px 4px;
        border-radius: 3px;
        color: #664d03; /* Amber text for highlights */
    }
    
    .tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 5px;
        margin-bottom: 5px;
        background-color: #e5e7eb;
        color: #4b5563; /* Explicit text color for tags */
    }
    
    .dashboard-metrics {
        background-color: #f9fafb;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
    }
    
    .footer {
        text-align: center;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
        font-size: 0.9rem;
        color: #6b7280;
    }
    
    /* Fix for any HTML content rendered in Streamlit markdown */
    .element-container div.stMarkdown p {
        color: #333333;
    }
    
    /* Ensure all links have proper color and hover states */
    a {
        color: #2563eb;
        text-decoration: underline;
    }
    
    a:hover {
        color: #1d4ed8;
    }
    
    /* Add styles for dark mode compatibility */
    @media (prefers-color-scheme: dark) {
        /* Only apply if the app supports dark mode */
        .stApp.stApp--darkTheme .card {
            color: #e5e7eb;
        }
        
        .stApp.stApp--darkTheme .research-card {
            background-color: rgba(59, 130, 246, 0.1);
            color: #93c5fd;
        }
        
        .stApp.stApp--darkTheme .answer-card {
            background-color: rgba(16, 185, 129, 0.1);
            color: #a7f3d0;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False
if "current_step" not in st.session_state:
    st.session_state.current_step = None
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []
if "tags" not in st.session_state:
    st.session_state.tags = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "research_depth": 3,
        "include_citations": True,
        "theme": "light",
        "max_sources": 5
    }
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "selected_research_id" not in st.session_state:
    st.session_state.selected_research_id = None
if "nav_option" not in st.session_state:
    st.session_state.nav_option = "🔍 Research"


# Helper functions
def generate_unique_id():
    """Generate a simple timestamp-based ID"""
    return int(datetime.now().timestamp() * 1000)

def save_research_to_history(query, research_result, final_answer):
    """Save research results to history with metadata"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    research_id = generate_unique_id()
    
    # Extract possible tags from query
    possible_tags = [word.lower() for word in query.split() 
                    if len(word) > 4 and word.lower() not in ["what", "where", "when", "which", "how", "does", "the", "and", "that", "this"]]
    
    # Take up to 3 most relevant tags
    suggested_tags = possible_tags[:3] if possible_tags else ["research"]
    
    # Add to history
    new_entry = {
        "id": research_id,
        "query": query,
        "research": research_result,
        "answer": final_answer,
        "timestamp": timestamp,
        "date_obj": datetime.now(),
        "tags": suggested_tags,
        "bookmarked": False,
        "word_count": len(final_answer.split()),
        "sources_count": research_result.count("Source:"),
    }
    
    st.session_state.history.append(new_entry)
    
    # Update tag collection
    for tag in suggested_tags:
        if tag not in st.session_state.tags:
            st.session_state.tags.append(tag)
    
    return research_id

def bookmark_research(research_id, status=True):
    """Bookmark or unbookmark a research item"""
    for item in st.session_state.history:
        if item["id"] == research_id:
            item["bookmarked"] = status
            if status and research_id not in st.session_state.bookmarks:
                st.session_state.bookmarks.append(research_id)
            elif not status and research_id in st.session_state.bookmarks:
                st.session_state.bookmarks.remove(research_id)
            break

def filter_history(search_term="", selected_tags=None, bookmarked_only=False):
    """Filter history based on criteria"""
    filtered = st.session_state.history
    
    if bookmarked_only:
        filtered = [item for item in filtered if item.get("bookmarked", False)]
    
    if search_term:
        search_lower = search_term.lower()
        filtered = [item for item in filtered if 
                   search_lower in item["query"].lower() or 
                   search_lower in item["answer"].lower()]
    
    if selected_tags and len(selected_tags) > 0:
        filtered = [item for item in filtered if 
                   any(tag in item.get("tags", []) for tag in selected_tags)]
    
    return filtered

def get_research_metrics():
    """Calculate research metrics for dashboard"""
    total_research = len(st.session_state.history)
    
    if total_research == 0:
        return {
            "total_research": 0,
            "avg_sources": 0,
            "avg_word_count": 0,
            "research_by_date": pd.DataFrame(columns=["date", "count"]),
            "popular_tags": []
        }
    
    # Calculate averages
    avg_sources = sum(item.get("sources_count", 0) for item in st.session_state.history) / total_research
    avg_word_count = sum(item.get("word_count", 0) for item in st.session_state.history) / total_research
    
    # Research by date
    dates = [item.get("date_obj", datetime.now()).date() for item in st.session_state.history]
    date_counts = {}
    for date in dates:
        date_str = date.strftime("%Y-%m-%d")
        if date_str in date_counts:
            date_counts[date_str] += 1
        else:
            date_counts[date_str] = 1
    
    research_by_date = pd.DataFrame([
        {"date": k, "count": v} for k, v in date_counts.items()
    ])
    
    # Count tag occurrences
    tag_counts = {}
    for item in st.session_state.history:
        for tag in item.get("tags", []):
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1
    
    # Sort tags by count
    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_research": total_research,
        "avg_sources": avg_sources,
        "avg_word_count": avg_word_count,
        "research_by_date": research_by_date,
        "popular_tags": popular_tags
    }

def export_history_to_json():
    """Convert history to JSON for export"""
    export_data = []
    for item in st.session_state.history:
        export_item = {k: v for k, v in item.items() if k != 'date_obj'}
        export_data.append(export_item)
    return json.dumps(export_data, indent=2)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-header">🧰 Research Console</div>', unsafe_allow_html=True)
    
    # Navigation
    nav_option = st.radio(
        "Navigation",
        ["🔍 Research", "📊 Dashboard", "🗂 My Research", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if nav_option == "🔍 Research":
        # About section
        with st.expander("ℹ️ About this tool"):
            st.write("""
            <div class="card">
            This AI research agent helps you gather information from the web and create 
            comprehensive answers to your queries. Simply enter your research question 
            and let the AI do the work!
            
            **Features:**
            - Web research from multiple sources
            - AI-powered answer generation
            - Save and review research history
            - Organize with tags and bookmarks
            </div>
            """, unsafe_allow_html=True)
        
        # Quick settings for research
        st.markdown("### Research Settings")
        research_depth = st.slider(
            "Research depth", 
            min_value=1, 
            max_value=5, 
            value=st.session_state.settings["research_depth"],
            help="Higher values mean more thorough research but slower response"
        )
        st.session_state.settings["research_depth"] = research_depth
        
        include_citations = st.toggle(
            "Include citations", 
            value=st.session_state.settings["include_citations"]
        )
        st.session_state.settings["include_citations"] = include_citations
        
        max_sources = st.slider(
            "Maximum sources", 
            min_value=1, 
            max_value=10, 
            value=st.session_state.settings["max_sources"],
            help="Maximum number of sources to include in research"
        )
        st.session_state.settings["max_sources"] = max_sources
    
    elif nav_option == "🗂 My Research":
        # Search and filter
        st.markdown("### Search & Filter")
        search_term = st.text_input("Search research", value=st.session_state.search_query)
        st.session_state.search_query = search_term
        
        selected_tags = st.multiselect(
            "Filter by tags",
            options=st.session_state.tags,
            default=None
        )
        
        bookmarked_only = st.toggle("Bookmarked only", value=False)
        
        # Export options
        st.markdown("### Export Options")
        if st.session_state.history:
            st.download_button(
                label="📥 Export All Research",
                data=export_history_to_json(),
                file_name=f"research_history_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Clear history
        if st.button("🧹 Clear All History", type="secondary", use_container_width=True):
            st.session_state.history = []
            st.session_state.bookmarks = []
            st.session_state.tags = []
            st.rerun()
    
    elif nav_option == "⚙️ Settings":
        st.markdown("### Application Settings")
        
        # Theme selection
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "System Default"],
            index=0 if st.session_state.settings["theme"] == "light" else 
                  1 if st.session_state.settings["theme"] == "dark" else 2
        )
        st.session_state.settings["theme"] = theme.lower().replace(" default", "")
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.number_input(
                "Request timeout (seconds)",
                min_value=10,
                max_value=120,
                value=60,
                step=5
            )
            st.selectbox(
                "Model provider",
                ["Default (Gemini)", "GPT-4", "Claude"],
                index=0
            )
        
        # Reset settings
        if st.button("Reset to Defaults", type="secondary", use_container_width=True):
            st.session_state.settings = {
                "research_depth": 3,
                "include_citations": True,
                "theme": "light",
                "max_sources": 5
            }
            st.rerun()

# Main content area based on navigation
if nav_option == "🔍 Research":
    st.markdown('<div class="main-header">🔍 AI Deep Researcher</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Harness AI to research topics, synthesize information, and generate comprehensive answers.</div>', unsafe_allow_html=True)
    
    # Initialize session state for query
    if "query_value" not in st.session_state:
        st.session_state.query_value = ""

    # Query input section
    query = st.text_input(
        "💬 Enter your research query:",
        placeholder="e.g., What are the latest AI trends in healthcare?",
        key="query_input",
        value=st.session_state.query_value,  # Bind to custom session state
        on_change=lambda: st.session_state.update(query_value=st.session_state.query_input)  # Sync on change
    )

    col1, col2 = st.columns([4, 1])
    with col1:
        search_pressed = st.button(
            "🚀 Start Research", 
            type="primary", 
            disabled=st.session_state.is_researching,
            use_container_width=True
        )

    with col2:
        example_question = st.button(
            "📝 Example Query", 
            type="secondary",
            use_container_width=True
        )
        if example_question:
            st.session_state.query_value = "What are the environmental impacts of electric vehicles compared to conventional cars?"
            st.rerun()  # Rerun to reflect the new value in the text input
    
    # Research process
    if search_pressed and query:
        st.session_state.is_researching = True
        st.session_state.current_step = "research"
        
        # Research progress
        progress_container = st.container()
        
        with progress_container:
            with st.status("🔎 Research in progress...", expanded=True) as status:
                st.write('<div class="process-card"Searching the web for relevant information...</div>', unsafe_allow_html=True)
                
                # Simulate web research with progress
                progress_bar = st.progress(0)
                for i in range(5):
                    # Simulating different search sources
                    sources = ["Academic journals", "News articles", "Research papers", 
                               "Expert opinions", "Statistical data"]
                    st.write(f'<div class="process-card">Analyzing {sources[i]}...</div>', unsafe_allow_html=True)
                    progress_bar.progress((i + 1) * 20)
                    time.sleep(0.5)  # Simulate processing time
                
                # Actual research execution
                research_result = web_research_tool.run(
                    query, 
                    depth=st.session_state.settings["research_depth"],
                    max_sources=st.session_state.settings["max_sources"]
                )
                st.write('<div class="process-card">✅ Web research completed</div>', unsafe_allow_html=True)
                
                st.session_state.current_step = "drafting"
                st.write('<div class="process-card">Analyzing and synthesizing information...</div>', unsafe_allow_html=True)
                time.sleep(1)  # Simulate processing time
                
                st.write('<div class="process-card">Drafting comprehensive answer...</div>', unsafe_allow_html=True)
                llm = get_drafting_llm()
                final_answer = draft_answer(
                    llm, 
                    research_result,
                    include_citations=st.session_state.settings["include_citations"]
                )
                st.write('<div class="process-card">✅ Answer generation completed</div>', unsafe_allow_html=True)
                
                status.update(label="✅ Research complete!", state="complete")
        
        # Save to history with metadata
        research_id = save_research_to_history(query, research_result, final_answer)
        
        st.session_state.is_researching = False
        st.session_state.current_step = None
        
        # Show latest result
        st.markdown('<div class="sub-header">📊 Research Results</div>', unsafe_allow_html=True)
        
        # Display query and metadata
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f'<div class="query-text">{query}</div>', unsafe_allow_html=True)
            timestamp = st.session_state.history[-1]["timestamp"]
            st.markdown(f'<div class="timestamp">Researched on {timestamp}</div>', unsafe_allow_html=True)
            
            # Display tags
            st.write("Tags:")
            for tag in st.session_state.history[-1]["tags"]:
                st.markdown(f"""
                <span class="tag" style="background-color: #e5e7eb; color: #4b5563;">
                    #{tag}
                </span>
                """, unsafe_allow_html=True)
        
        with col2:
            # Bookmark button
            if st.button("🔖 Bookmark this research", use_container_width=True):
                bookmark_research(research_id, True)
                st.success("Research bookmarked!")
        
        # Tabs for content
        tab1, tab2 = st.tabs(["✍️ Answer", "📚 Research Details"])
        
        with tab1:
            st.markdown(f"""
            <div class="card answer-card">
                {final_answer}
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown(f"""
            <div class="card research-card">
                {research_result}
            </div>
            """, unsafe_allow_html=True)
    
    # Display recent history preview if not researching
    elif not st.session_state.is_researching and st.session_state.history:
        st.markdown('<div class="sub-header">🕒 Recent Research</div>', unsafe_allow_html=True)
        
        # Show last 3 research items in a compact format
        recent_items = st.session_state.history[-3:] if len(st.session_state.history) >= 3 else st.session_state.history
        recent_items.reverse()  # Most recent first
        
        for item in recent_items:
            with st.container():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f'<div class="query-text">{item["query"]}</div>', unsafe_allow_html=True)
                with col2:
                    if item.get("bookmarked", False):
                        st.markdown("🔖 Bookmarked")
                
                st.markdown(f'<div class="timestamp">{item["timestamp"]}</div>', unsafe_allow_html=True)
                st.markdown(f'''
                <div style="margin-top: 8px; margin-bottom: 12px; overflow: hidden; text-overflow: ellipsis; max-height: 60px;">
                    {item["answer"][:150]}...
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"View full research", key=f"view_{item['id']}"):
                    # Navigate to My Research with this item selected
                    st.session_state.selected_research_id = item["id"]
                    st.session_state.nav_option = "🗂 My Research"
                    st.rerun()
                
                st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        
        if len(st.session_state.history) > 3:
            st.markdown(f"And {len(st.session_state.history) - 3} more research items in history...")
            if st.button("View all research history"):
                # Navigate to My Research page
                st.session_state.nav_option = "🗂 My Research"
                st.rerun()

elif nav_option == "📊 Dashboard":
    st.markdown('<div class="main-header">📊 Research Dashboard</div>', unsafe_allow_html=True)
    
    # Get metrics
    metrics = get_research_metrics()
    
    # Display metrics in cards
    st.markdown('<div class="dashboard-metrics">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-value">{metrics['total_research']}</div>
            <div class="metric-label">Total Research Queries</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-value">{metrics['avg_sources']:.1f}</div>
            <div class="metric-label">Avg. Sources Per Query</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-value">{metrics['avg_word_count']:.0f}</div>
            <div class="metric-label">Avg. Answer Word Count</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display charts if we have data
    if metrics["total_research"] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Research Activity")
            if not metrics["research_by_date"].empty:
                fig = px.line(
                    metrics["research_by_date"], 
                    x="date", 
                    y="count",
                    markers=True,
                    title="Research Queries Over Time"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to display chart")
        
        with col2:
            st.subheader("Popular Research Topics")
            if metrics["popular_tags"]:
                tag_df = pd.DataFrame(metrics["popular_tags"], columns=["tag", "count"])
                fig = px.bar(
                    tag_df,
                    x="tag",
                    y="count",
                    title="Most Common Research Tags"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to display chart")
        
        # Bookmarked research
        st.subheader("Bookmarked Research")
        bookmarked = [item for item in st.session_state.history if item.get("bookmarked", False)]
        
        if bookmarked:
            for item in bookmarked[:3]:  # Show up to 3 bookmarked items
                st.markdown(f"""
                <div class="card" style="background-color: #fffbeb; border-left: 5px solid #f59e0b;">
                    <div class="query-text">{item["query"]}</div>
                    <div class="timestamp">{item["timestamp"]}</div>
                    <div style="margin-top: 10px;">{item["answer"][:100]}...</div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(bookmarked) > 3:
                st.markdown(f"And {len(bookmarked) - 3} more bookmarked items...")
        else:
            st.info("No bookmarked research yet. Use the bookmark button to save important research.")
    else:
        st.info("Start researching to see your dashboard statistics")

elif nav_option == "🗂 My Research":
    st.markdown('<div class="main-header">🗂 My Research History</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_history = filter_history(
        search_term=st.session_state.search_query,
        selected_tags=st.session_state.get("selected_tags", []),
        bookmarked_only=st.session_state.get("bookmarked_only", False)
    )
    
    if not filtered_history:
        st.info("No research history found. Start researching to build your knowledge base.")
    else:
        # Display filtered research
        st.markdown(f"Showing {len(filtered_history)} research items")
        
        # Check if a specific research item is selected
        selected_research_id = st.session_state.get("selected_research_id", None)
        
        for i, item in enumerate(filtered_history):
            # Expand the item if it matches selected_research_id or if it's the first item
            is_expanded = (item["id"] == selected_research_id) or (i == 0 and selected_research_id is None)
            with st.expander(f"{item['query']} ({item['timestamp']})", expanded=is_expanded):
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Display tags
                    st.write("Tags:")
                    for tag in item.get("tags", []):
                        st.markdown(f"""
                        <span class="tag" style="background-color: #e5e7eb; color: #4b5563;">
                            #{tag}
                        </span>
                        """, unsafe_allow_html=True)
                
                with col2:
                    # Bookmark toggle
                    is_bookmarked = item.get("bookmarked", False)
                    if is_bookmarked:
                        if st.button("🔖 Unbookmark", key=f"unbookmark_{item['id']}"):
                            bookmark_research(item["id"], False)
                            st.rerun()
                    else:
                        if st.button("🔖 Bookmark", key=f"bookmark_{item['id']}"):
                            bookmark_research(item["id"], True)
                            st.rerun()
                
                # Content tabs
                tab1, tab2 = st.tabs(["✍️ Answer", "📚 Research Details"])
                
                with tab1:
                    st.markdown(f"""
                    <div class="card answer-card">
                        {item['answer']}
                    </div>
                    """, unsafe_allow_html=True)
                
                with tab2:
                    st.markdown(f"""
                    <div class="card research-card">
                        {item['research']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Clear selected_research_id after displaying to prevent persistent expansion
        if selected_research_id is not None:
            st.session_state.selected_research_id = None
            
elif nav_option == "⚙️ Settings":
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
    
    # Settings are handled in sidebar, so this is just a mirror
    st.markdown('<div class="card">Use the sidebar to manage application settings.</div>', unsafe_allow_html=True)
    
    st.markdown("### Current Settings")
    
    st.json(st.session_state.settings)
    
    st.markdown("### About")
    st.markdown("""
    <div class="card">
    AI Deep Researcher v1.0.0 <br> <br>
    This tool helps you conduct in-depth research on any topic using AI-powered web search
    and content synthesis capabilities.
    <br><br>
    <b>Features:</b> <br>
    - Web research across multiple sources <br>
    - AI-powered answer generation <br>
    - Research history management <br>
    - Dashboard analytics <br>
    - Tag and bookmark organization <br>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    AI Deep Researcher • Powered by Gemini • © 2025
</div>
""", unsafe_allow_html=True)