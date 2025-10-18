import streamlit as st

# Page configuration
st.set_page_config(
    page_title="GhostBack.ai",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        margin-top: 3rem;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .feature-box {
        padding: 2rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border: 1px solid #667eea30;
        margin: 1rem 0;
    }
    .cta-section {
        text-align: center;
        margin-top: 3rem;
        margin-bottom: 3rem;
    }
    .stButton > button {
        font-size: 1.2rem;
        padding: 1rem 3rem;
        border-radius: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">👻 GhostBack.ai</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Find closure through AI-simulated conversations</p>', unsafe_allow_html=True)

# Introduction
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    ### We've all been there
    
    A conversation that just... stopped. No explanation. No closure. Just silence.
    
    **GhostBack.ai** helps you find peace by creating an AI simulation based on your past conversations.
    Talk through what you needed to say, understand the patterns, and finally get closure.
    """)

st.markdown("---")

# How it works
st.markdown("## How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-box">
        <h3>📱 1. Upload</h3>
        <p>Export your WhatsApp chat history and paste it in. We parse every message to understand their communication style.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <h3>🤖 2. AI Learns</h3>
        <p>Our AI analyzes their texting patterns, quirks, emotional tone, and creates an authentic simulation of how they communicate.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <h3>💬 3. Find Closure</h3>
        <p>Have the conversation you needed to have. Ask questions, express yourself, and process your emotions in a safe space.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Features
st.markdown("## What You Get")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🧠 Intelligent Analysis**
    - Sentiment tracking over time
    - Communication pattern detection
    - Emotional tone analysis
    - Writing style replication
    """)

with col2:
    st.markdown("""
    **💭 Emotional Support**
    - AI-generated closure insights
    - Safe space for processing
    - Privacy-first approach
    """)

st.markdown("---")

# Privacy notice
st.info("""
**🔒 Your Privacy Matters**

All conversations stay in your browser session. Nothing is stored permanently. 
No data is shared. This is a safe, private space for healing.
""")

# CTA
st.markdown('<div class="cta-section">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Let's Start", type="primary", use_container_width=True):
        st.markdown("**Redirecting to Chat page...**")
        st.markdown("Please click on '💬 Chat' in the sidebar to continue.")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Footer
st.caption("Built with 💜 | GhostBack.ai - Helping you find closure, one conversation at a time")