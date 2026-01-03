import os
import time
from urllib.parse import urlparse
import streamlit as st
from src.scrapers.workdayjobs import Workday
from multiprocessing import Process
from src.storage.database import Database
import signal

st.title("Myworkdayjobs Scraper 👋")
progress_file = "progress.json"
# Initialize database
db = Database()

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
