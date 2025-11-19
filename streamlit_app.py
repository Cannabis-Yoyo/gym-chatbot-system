import streamlit as st
import sys
import os
from pathlib import Path
import shutil

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from config import Config
    from data_loader import DataLoader
    from member_bot import MemberBot
    from sales_bot import SalesBot
    from insights_bot import InsightsBot
    from logger import logger
except ModuleNotFoundError as e:
    st.error(f"Import Error: {e}")
    st.error("Please ensure all required files are in the same directory as streamlit_app.py")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Gym Chatbot Management System",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #3b82f6;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 1rem;
    }
    .stat-card {
        background-color: #f3f4f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #eff6ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #3b82f6;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f59e0b;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d1fae5;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #10b981;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: none;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = None
    if 'member_bot' not in st.session_state:
        st.session_state.member_bot = None
    if 'sales_bot' not in st.session_state:
        st.session_state.sales_bot = None
    if 'insights_bot' not in st.session_state:
        st.session_state.insights_bot = None
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {}
    if 'current_bot' not in st.session_state:
        st.session_state.current_bot = None
    if 'data_folder_path' not in st.session_state:
        st.session_state.data_folder_path = Config.DATA_FOLDER
    if 'user_input_key' not in st.session_state:
        st.session_state.user_input_key = 0

def get_data_files():
    """Get list of data files in data folder"""
    data_folder = Config.DATA_FOLDER
    if not os.path.exists(data_folder):
        return []
    
    files = []
    for filename in os.listdir(data_folder):
        if filename.endswith(('.xlsx', '.xls', '.csv')):
            filepath = os.path.join(data_folder, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath) / 1024  # KB
                files.append({'name': filename, 'size': size})
    return files

def delete_data_file(filename):
    """Delete a data file"""
    try:
        filepath = os.path.join(Config.DATA_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, f"Deleted {filename}"
    except Exception as e:
        return False, f"Error deleting {filename}: {str(e)}"
    return False, "File not found"

def clear_all_data():
    """Clear all data files"""
    try:
        data_folder = Config.DATA_FOLDER
        for filename in os.listdir(data_folder):
            if filename.endswith(('.xlsx', '.xls', '.csv')):
                filepath = os.path.join(data_folder, filename)
                os.remove(filepath)
        
        # Clear cache
        cache_folder = Config.CSV_CACHE_FOLDER
        if os.path.exists(cache_folder):
            shutil.rmtree(cache_folder)
            os.makedirs(cache_folder)
        
        return True, "All data files cleared"
    except Exception as e:
        return False, f"Error clearing data: {str(e)}"

def initialize_system():
    """Initialize the chatbot system"""
    try:
        Config.validate()
        logger.info(f"Configuration validated successfully. Data folder: {Config.DATA_FOLDER}")
        
        st.session_state.data_loader = DataLoader()
        
        if not st.session_state.data_loader.load_all_data():
            st.warning("No data files found. Please upload data files.")
            logger.warning("No data files loaded")
            return False
        
        st.session_state.member_bot = MemberBot(st.session_state.data_loader)
        st.session_state.sales_bot = SalesBot(st.session_state.data_loader)
        st.session_state.insights_bot = InsightsBot(st.session_state.data_loader)
        
        st.session_state.initialized = True
        
        st.session_state.chat_history = {
            'member': [],
            'sales': [],
            'insights': []
        }
        
        logger.info("System initialized successfully")
        return True
        
    except Exception as e:
        logger.error_with_trace(e, "System initialization")
        st.error(f"Initialization failed: {e}")
        return False

def display_stats():
    """Display system statistics"""
    if not st.session_state.initialized:
        return
    
    stats = st.session_state.data_loader.get_summary_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown("**Total Members**")
        st.markdown(f"## {stats.get('total_members', 0):,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown("**Total Orders**")
        st.markdown(f"## {stats.get('total_orders', 0):,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown("**Paid Orders**")
        st.markdown(f"## {stats.get('paid_orders', 0):,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown("**Total Revenue**")
        st.markdown(f"## CAD ${stats.get('total_revenue', 0):,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

def display_chat_interface(bot_name, bot_instance, bot_key):
    """Display chat interface for selected bot"""
    st.markdown(f'<div class="sub-header">{bot_name}</div>', unsafe_allow_html=True)
    
    if bot_key not in st.session_state.chat_history:
        st.session_state.chat_history[bot_key] = []
    
    chat_history = st.session_state.chat_history[bot_key]
    
    chat_container = st.container()
    
    with chat_container:
        for message in chat_history:
            if message['role'] == 'user':
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    formatted_content = message["content"].replace('\n', '  \n')
                    st.markdown(formatted_content)
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message:", 
            key=f"user_input_{bot_key}_{st.session_state.user_input_key}", 
            label_visibility="collapsed", 
            placeholder="Ask me anything..."
        )
    
    with col2:
        send_button = st.button("Send", key=f"send_{bot_key}", use_container_width=True)
    
    if send_button and user_input:
        st.session_state.chat_history[bot_key].append({
            'role': 'user',
            'content': user_input
        })
        
        try:
            response = bot_instance.process_query(user_input)
            
            st.session_state.chat_history[bot_key].append({
                'role': 'bot',
                'content': response
            })
            
            st.session_state.user_input_key += 1
            
        except Exception as e:
            st.error(f"Error processing query: {e}")
            logger.error_with_trace(e, "Chat query processing")
        
        st.rerun()
    
    if st.button("Clear Chat", key=f"clear_{bot_key}", use_container_width=True):
        st.session_state.chat_history[bot_key] = []
        st.session_state.user_input_key += 1
        st.rerun()

def data_management_page():
    """Data management interface"""
    st.markdown('<div class="main-header">Data Management</div>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<div class="sub-header">Upload Data Files</div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload Excel or CSV files",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Upload your member data, orders, payments, or items files"
    )
    
    if uploaded_files:
        os.makedirs(Config.DATA_FOLDER, exist_ok=True)
        success_count = 0
        
        for file in uploaded_files:
            try:
                file_path = os.path.join(Config.DATA_FOLDER, file.name)
                with open(file_path, 'wb') as f:
                    f.write(file.getbuffer())
                success_count += 1
            except Exception as e:
                st.error(f"Error uploading {file.name}: {str(e)}")
        
        if success_count > 0:
            st.success(f"Successfully uploaded {success_count} file(s)")
            st.info("Click 'Initialize System' below to load the new data")
    
    st.markdown("---")
    
    # Current files section
    st.markdown('<div class="sub-header">Current Data Files</div>', unsafe_allow_html=True)
    
    data_files = get_data_files()
    
    if data_files:
        st.markdown(f'<div class="info-box">Total Files: {len(data_files)}</div>', unsafe_allow_html=True)
        
        for file_info in data_files:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.text(f"{file_info['name']}")
            
            with col2:
                st.text(f"{file_info['size']:.1f} KB")
            
            with col3:
                if st.button("Delete", key=f"delete_{file_info['name']}", use_container_width=True):
                    success, message = delete_data_file(file_info['name'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.markdown('<div class="warning-box">No data files found. Please upload files.</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Actions section
    st.markdown('<div class="sub-header">Actions</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Initialize System", use_container_width=True, type="primary"):
            with st.spinner("Initializing system..."):
                if initialize_system():
                    st.success("System initialized successfully!")
                    st.info("Navigate to chatbot pages from the sidebar")
                else:
                    st.error("Failed to initialize. Please upload data files.")
    
    with col2:
        if st.button("Clear All Data", use_container_width=True, type="secondary"):
            if len(data_files) > 0:
                if 'confirm_clear' not in st.session_state:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm clearing all data")
                else:
                    success, message = clear_all_data()
                    if success:
                        st.success(message)
                        st.session_state.initialized = False
                        del st.session_state.confirm_clear
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.info("No data to clear")

def main():
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        
        page = st.radio(
            "Select Page:",
            ["Data Management", "Dashboard", "Member Support Bot", "Sales & Orders Bot", "Data Insights Bot", "System Information"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # System status
        if st.session_state.initialized:
            st.success("System Active")
        else:
            st.warning("System Not Initialized")
        
        # Dataset info
        if st.session_state.data_loader and st.session_state.initialized:
            dataset_info = st.session_state.data_loader.get_dataset_info()
            if dataset_info:
                st.markdown("### Loaded Datasets")
                for info in dataset_info[:3]:
                    st.text(info)
                if len(dataset_info) > 3:
                    st.text(f"... and {len(dataset_info) - 3} more")
        
        st.markdown("---")
        st.markdown("**Version:** 1.0.0")
    
    # Main content
    if page == "Data Management":
        data_management_page()
    
    elif page == "Dashboard":
        if not st.session_state.initialized:
            st.warning("Please initialize the system from Data Management page")
            return
        
        st.markdown('<div class="main-header">Dashboard Overview</div>', unsafe_allow_html=True)
        display_stats()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### System Status")
            datasets = st.session_state.data_loader.get_all_dataframes()
            st.info(f"Datasets Loaded: {len(datasets)}")
            st.info(f"Data Files: {len(get_data_files())}")
        
        with col2:
            st.markdown("### Configuration")
            st.info(f"Model: {Config.MODEL_NAME}")
            st.info(f"Temperature: {Config.TEMPERATURE}")
            st.info(f"Max Tokens: {Config.MAX_TOKENS}")
    
    elif page == "Member Support Bot":
        if not st.session_state.initialized:
            st.warning("Please initialize the system from Data Management page")
            return
        
        if st.session_state.member_bot:
            display_chat_interface("Member Support Bot", st.session_state.member_bot, "member")
        else:
            st.error("Member bot not initialized")
    
    elif page == "Sales & Orders Bot":
        if not st.session_state.initialized:
            st.warning("Please initialize the system from Data Management page")
            return
        
        if st.session_state.sales_bot:
            display_chat_interface("Sales & Orders Bot", st.session_state.sales_bot, "sales")
        else:
            st.error("Sales bot not initialized")
    
    elif page == "Data Insights Bot":
        if not st.session_state.initialized:
            st.warning("Please initialize the system from Data Management page")
            return
        
        if st.session_state.insights_bot:
            display_chat_interface("Data Insights Bot", st.session_state.insights_bot, "insights")
        else:
            st.error("Insights bot not initialized")
    
    elif page == "System Information":
        st.markdown('<div class="main-header">System Information</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Configuration")
            st.text(f"Data Folder: {Config.DATA_FOLDER}")
            st.text(f"Model: {Config.MODEL_NAME}")
            st.text(f"Temperature: {Config.TEMPERATURE}")
            st.text(f"Max Tokens: {Config.MAX_TOKENS}")
        
        with col2:
            st.markdown("### Statistics")
            if st.session_state.initialized:
                stats = st.session_state.data_loader.get_summary_stats()
                st.text(f"Total Members: {stats.get('total_members', 0):,}")
                st.text(f"Total Orders: {stats.get('total_orders', 0):,}")
                st.text(f"Paid Orders: {stats.get('paid_orders', 0):,}")
                st.text(f"Total Revenue: CAD ${stats.get('total_revenue', 0):,.2f}")
            else:
                st.text("System not initialized")

if __name__ == "__main__":
    main()