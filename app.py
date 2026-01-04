import os
import time
from urllib.parse import urlparse
import streamlit as st
from src.scrapers.workdayjobs import Workday
from multiprocessing import Process
from src.storage.database import Database
import signal
import hashlib
from datetime import datetime, timedelta
import streamlit_cookies_manager

# Simple authentication configuration
USERS = {
    "admin": hashlib.sha256("password123".encode()).hexdigest(),
    "user": hashlib.sha256("userpass".encode()).hexdigest(),
}

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30

# Initialize cookies manager
cookies = streamlit_cookies_manager.EncryptedCookieManager(
    prefix="myapp_",
    password="your_secret_password_here_change_this"  # Change this to a secure password
)
# Initialize database
db = Database()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username: str, password: str) -> bool:
    """Verify username and password against database"""
    user = db.get_user(username)
    if user:
        password_hash = hash_password(password)
        return user.password == password_hash
    return False

if not cookies.ready():
    st.stop()

def check_session_timeout():
    """Check if session has timed out"""
    if cookies.get("last_activity"):
        try:
            last_activity = datetime.fromisoformat(cookies["last_activity"])
            time_elapsed = datetime.now() - last_activity
            
            if time_elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                # Session expired
                logout()
                st.warning("Your session has expired. Please login again.")
                return True
        except Exception as _:
            pass
    
    # Update last activity time
    cookies["last_activity"] = datetime.now().isoformat()
    cookies.save()
    return False

def logout():
    """Clear session and cookies"""
    cookies["authenticated"] = ""
    cookies["username"] = ""
    cookies["login_time"] = ""
    cookies["last_activity"] = ""
    cookies.save()
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        username = st.session_state["username"]
        password = st.session_state["password"]
        
        if verify_password(username, password):            # Set cookies for persistent session
            cookies["authenticated"] = "true"
            cookies["username"] = username
            cookies["login_time"] = datetime.now().isoformat()
            cookies["last_activity"] = datetime.now().isoformat()
            cookies.save()
            
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = username
            del st.session_state["password"]  # Don't store password
            del st.session_state["username"]
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    # Check if already authenticated via cookies
    if cookies.get("authenticated") == "true" and cookies.get("username"):
        user = db.get_user(cookies["username"])
        if user and not check_session_timeout():
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = cookies["username"]
            return True
        else:
            logout()
            return False

    # Show login form
    st.title("🔐 Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=password_entered)
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Username or password incorrect")
    
    return False

# Check authentication before showing app
if not check_password():
    st.stop()

# Add logout button and session info in sidebar
with st.sidebar:
    st.write(f"👤 Logged in as: **{st.session_state.get('current_user', 'Unknown')}**")
    
    # Show session info
    if cookies.get("login_time"):
        try:
            login_time = datetime.fromisoformat(cookies["login_time"])
            session_duration = datetime.now() - login_time
            minutes_active = int(session_duration.total_seconds() / 60)
            st.caption(f"⏱️ Session active: {minutes_active} min")
        except Exception as _:
            pass
        
        # Show time until timeout
        if cookies.get("last_activity"):
            try:
                last_activity = datetime.fromisoformat(cookies["last_activity"])
                time_since_activity = datetime.now() - last_activity
                minutes_until_timeout = SESSION_TIMEOUT_MINUTES - int(time_since_activity.total_seconds() / 60)
                if minutes_until_timeout > 0:
                    st.caption(f"🔒 Auto-logout in: {minutes_until_timeout} min")
            except Exception as _:
                pass
    
    st.divider()
    
    # Password change form
    with st.expander("🔑 Change Password"):
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password", key="current_pwd")
            new_password = st.text_input("New Password", type="password", key="new_pwd")
            confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_pwd")
            
            submit_password = st.form_submit_button("Update Password")
            
            if submit_password:
                username = st.session_state.get('current_user')
                
                # Validate current password
                st.write(username, current_password, new_password)
                if not verify_password(username, current_password):
                    st.error("Current password is incorrect")
                elif not new_password:
                    st.error("New password cannot be empty")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                else:
                    # Hash and update password
                    hashed_password = hash_password(new_password)
                    result = db.update_user(username, hashed_password)
                    
                    if result:
                        st.success("Password updated successfully!")
                        # Clear form fields
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update password")
    
    st.divider()
    
    if st.button("Logout"):
        logout()
        st.rerun()


st.title("Myworkdayjobs Scraper 👋")

def run_scraper(save_to_db: bool, jobserver_id: float, platform_link: str, name: str, is_test: bool, process_id: int):
    scraper = Workday(
        save=save_to_db,
        companyid=int(jobserver_id), 
        user_link=platform_link,
        name=name,
        is_test=is_test,
        process_id=process_id
    ) 
    scraper.main()

def stop_process(pid: int, platform: str):
    """Stop a running process by PID"""
    try:
        os.kill(pid, signal.SIGKILL)
        db.update_process_status("stopped", platform) 
        return True
    except Exception as e:
        st.error(f"Error stopping process: {e}")
        return None


with st.form("app_form"):
    st.write("Inside the form")
    platform_link = st.text_input("The Platform Link", help="The first page of the job listing")
    jobserver_id = st.number_input("Job Server ID")
    save_to_db = st.checkbox("Save to DB")
    is_test = st.checkbox("Perform Test run")
    parsed_url = urlparse(platform_link)
    username = parsed_url.netloc.split(".")[0]
    domain = parsed_url.netloc
    path = parsed_url.path.split('/')[-1]
    name = f'Workday-{username}'


    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        p = Process(target=run_scraper, args=(save_to_db, jobserver_id, platform_link, name, is_test, 0))  # Pass 0, will be updated
        p.start()
        
        # Update the progress file with the actual PID
        time.sleep(5)  # Give process time to start
        try:
            if not p.pid:
                st.error("PROCESS IS NONE")
            else:
                db.update_process_id(name, int(p.pid))
                st.success(f"Scraper started! PID: {p.pid}")
        except ValueError as e:
            st.warning(f"Scraper started (PID: {p.pid}), but couldn't update process_id: {e}")
                

# Display progress from database
try: 
    all_progress =  db.get_all_process()
    if all_progress:
        # Status filter
        statuses = ["all"] + list(set(data.status for data in all_progress))
        selected_status = st.selectbox("Filter by status:", statuses)
        
        # Filter progress
        filtered_progress = [
            data for data in all_progress
            if selected_status == "all" or data.status == selected_status
        ]
        
        if not filtered_progress:
            st.info(f"No sites with status: {selected_status}")
        
        for data in filtered_progress:
            with st.expander(f"📊 {data.platform} - {data.status.upper()}", expanded=False):
                if data.status == 'running':
                     st.spinner(text="In progress...", show_time=True, width="content")
                progress = data.current / data.total if data.total > 0 else 0
                st.progress(progress)
                
                col1, col2,col3 = st.columns(3)
                with col1:
                    st.metric("Progress", f"{data.current}/{data.total}")
                    st.metric("✅ Successful", data.successful)
                with col2:
                    st.metric("Completion", f"{progress*100:.1f}%")
                    st.metric("❌ Failed", data.failed)
                with col3:
                    # Show stop button only for running processes
                    if data.status == "running" and data.process_id > 0:
                        if st.button("🛑 Stop", key=f"stop_{data.id}"):
                            result = stop_process(data.process_id, data.platform)
                            if result is True:
                                st.success("Process stopped successfully!")
                                st.rerun()
                            elif result is False:
                                st.warning("Process not found (may have already finished)")
                            else:
                                st.error("Failed to stop process (permission denied)")
                
                st.caption(f"Last updated: {data.last_updated}")
                st.caption(f"Process ID: {data.process_id}")
    else:
        st.info("No progress data available yet.")
        
except Exception as e:
    st.error(f"Error loading progress data: {e}")
