"""
Snowflake Brand Guidelines for Streamlit
=========================================
Based on https://www.snowflake.com/brand-guidelines/

Colors:
- Primary: Snowflake Blue (#29B5E8), Mid Blue (#11567F), Midnight (#000000)
- Secondary: Star Blue (#71D3DC), Valencia Orange (#FF9F36), Purple Moon (#7D44CF)
- Fonts: Lato (Google Fonts)
"""

import streamlit as st

# Snowflake Brand Colors
SNOWFLAKE_BLUE = "#29B5E8"
MID_BLUE = "#11567F"
MIDNIGHT = "#000000"
STAR_BLUE = "#71D3DC"
VALENCIA_ORANGE = "#FF9F36"
PURPLE_MOON = "#7D44CF"
FIRST_LIGHT = "#D45B90"
WINDY_CITY = "#8A999E"
ICEBERG = "#003545"

BRAND_CSS = """
<style>
    /* Import Lato font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');
    
    /* Snowflake Brand Colors */
    :root {
        --snowflake-blue: #29B5E8;
        --mid-blue: #11567F;
        --midnight: #000000;
        --star-blue: #71D3DC;
        --valencia-orange: #FF9F36;
        --purple-moon: #7D44CF;
        --first-light: #D45B90;
        --windy-city: #8A999E;
        --iceberg: #003545;
    }
    
    /* Apply Lato font globally */
    html, body, [class*="css"] {
        font-family: 'Lato', sans-serif;
    }
    
    /* Main header styling */
    .main h1 {
        color: #11567F;
        font-weight: 900;
    }
    
    /* Subheader styling */
    .main h2, .main h3 {
        color: #11567F;
        font-weight: 700;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #11567F 0%, #003545 100%);
        min-height: 100vh;
    }
    
    /* Ensure sidebar content doesn't scroll/hide */
    [data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        overflow: visible !important;
        height: auto !important;
        min-height: 100vh;
    }
    
    /* ALL SIDEBAR TEXT WHITE */
    [data-testid="stSidebar"] {
        color: white !important;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stCaption * {
        color: #71D3DC !important;
    }
    
    /* Sidebar links */
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] a * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] a:hover,
    [data-testid="stSidebar"] a:hover * {
        color: #29B5E8 !important;
    }
    
    /* Sidebar buttons text */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] button span {
        color: white !important;
    }
    
    /* Sidebar selectbox/dropdown text */
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: white !important;
    }
    
    /* Sidebar checkbox labels */
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stCheckbox span {
        color: white !important;
    }
    
    /* Sidebar expander */
    [data-testid="stSidebar"] .streamlit-expanderHeader,
    [data-testid="stSidebar"] .streamlit-expanderHeader * {
        color: white !important;
        background-color: transparent !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] * {
        color: white !important;
    }
    
    /* Page navigation in sidebar */
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] span {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1rtdyuf {
        color: white !important;
    }
    
    [data-testid="stSidebarNav"] li span {
        color: white !important;
    }
    
    [data-testid="stSidebarNav"] a span {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] nav a {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] nav a span {
        color: white !important;
    }
    
    /* Page navigation - show all pages, no scroll, no hiding */
    [data-testid="stSidebarNav"] {
        order: 2;
        margin-top: 0;
        padding-top: 0;
        overflow: visible !important;
        max-height: none !important;
        height: auto !important;
    }
    
    [data-testid="stSidebar"] > div:first-child > div:first-child {
        order: 1;
    }
    
    /* Remove dropdown/expander - show all pages as flat list */
    [data-testid="stSidebarNav"] > ul {
        padding-left: 0 !important;
        max-height: none !important;
        overflow: visible !important;
    }
    
    /* Hide the "Pages" expander header/toggle */
    [data-testid="stSidebarNav"] summary,
    [data-testid="stSidebarNav"] [data-testid="stExpander"],
    [data-testid="stSidebarNavItems"] summary {
        display: none !important;
    }
    
    /* Remove expander styling, show pages directly */
    [data-testid="stSidebarNav"] details {
        border: none !important;
        background: transparent !important;
        max-height: none !important;
        overflow: visible !important;
    }
    
    [data-testid="stSidebarNav"] details[open] > summary {
        display: none !important;
    }
    
    /* Force details to always be open */
    [data-testid="stSidebarNav"] details {
        display: block !important;
    }
    
    [data-testid="stSidebarNav"] details > div {
        display: block !important;
        max-height: none !important;
        overflow: visible !important;
    }
    
    /* Show all list items - no hiding */
    [data-testid="stSidebarNav"] ul {
        max-height: none !important;
        overflow: visible !important;
        height: auto !important;
    }
    
    [data-testid="stSidebarNav"] li {
        display: list-item !important;
        visibility: visible !important;
        opacity: 1 !important;
        margin: 0.2rem 0;
        list-style: none;
    }
    
    /* Style page links as clean list */
    [data-testid="stSidebarNav"] a {
        display: block !important;
        padding: 0.4rem 1rem;
        border-radius: 4px;
        transition: background-color 0.2s;
        font-size: 0.9rem;
    }
    
    [data-testid="stSidebarNav"] a:hover {
        background-color: rgba(41, 181, 232, 0.2);
    }
    
    /* Active page highlight */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: rgba(41, 181, 232, 0.3);
        border-left: 3px solid #29B5E8;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #29B5E8;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #11567F;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #29B5E8;
        color: white !important;
        border: none;
        border-radius: 80px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 0.5rem 1.5rem;
    }
    
    .stButton > button:hover {
        background-color: #11567F;
        color: white !important;
    }
    
    /* Info box styling */
    .stAlert {
        border-left-color: #29B5E8;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #29B5E8;
        color: white;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #F8FAFC;
        border-left: 4px solid #29B5E8;
    }
    
    /* Divider styling */
    hr {
        border-color: #71D3DC;
    }
    
    /* Link styling in main area */
    .main a {
        color: #29B5E8;
    }
    
    .main a:hover {
        color: #11567F;
    }
    
    /* Data editor / dataframe styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #71D3DC;
    }
    
    /* Custom branding header styling - more compact */
    .sidebar-branding {
        padding: 0.75rem;
        text-align: center;
        border-bottom: 1px solid rgba(113, 211, 220, 0.3);
        margin-bottom: 0.5rem;
    }
    
    .sidebar-branding h2 {
        font-size: 1.1rem !important;
        margin: 0.3rem 0 0.2rem 0 !important;
        color: white !important;
    }
    
    .sidebar-branding p {
        font-size: 0.75rem !important;
        color: #71D3DC !important;
    }
</style>
"""

SIDEBAR_LOGO = """
<div class="sidebar-branding">
    <svg width="160" height="45" viewBox="0 0 300 80" xmlns="http://www.w3.org/2000/svg">
        <g fill="#29B5E8">
            <polygon points="40,10 45,20 55,20 47,27 50,37 40,31 30,37 33,27 25,20 35,20"/>
            <polygon points="40,43 45,53 55,53 47,60 50,70 40,64 30,70 33,60 25,53 35,53"/>
            <polygon points="15,26 20,36 30,36 22,43 25,53 15,47 5,53 8,43 0,36 10,36"/>
            <polygon points="65,26 70,36 80,36 72,43 75,53 65,47 55,53 58,43 50,36 60,36"/>
        </g>
        <text x="95" y="50" fill="white" font-family="Lato, sans-serif" font-size="28" font-weight="700">SNOWFLAKE</text>
    </svg>
    <h2 style="color: white; margin: 0.5rem 0 0.25rem 0; font-size: 1.1rem;">Cortex AI Cost Simulator</h2>
    <p style="color: #71D3DC; margin: 0; font-size: 0.85rem;">Cost Intelligence & Model Selection</p>
</div>
"""


def apply_snowflake_branding():
    """Apply Snowflake brand CSS to the current page."""
    st.markdown(BRAND_CSS, unsafe_allow_html=True)


def render_sidebar_branding():
    """Render the Snowflake branded sidebar with logo at top, above page navigation."""
    with st.sidebar:
        st.markdown(SIDEBAR_LOGO, unsafe_allow_html=True)
