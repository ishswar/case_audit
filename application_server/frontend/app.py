import streamlit as st
import requests
import time
import pandas as pd
import json
import os
import io
import base64
from urllib.parse import urljoin
from importlib import import_module

# API endpoint
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="TIBCO Case Audit Tool",
    page_icon="📊",
    layout="wide",
)
st.logo("https://res.cloudinary.com/dpot1w2xt/image/upload/f_auto,q_auto/v1/uploads/eum6ztkkgfpcnbn4ofbn")

st.title("TIBCO Support Case Quality Audit")
st.markdown("Upload TIBCO case PDFs for AI-powered quality analysis.")

# Session state for job tracking
if "jobs" not in st.session_state:
    st.session_state.jobs = {}
if "current_job_id" not in st.session_state:
    st.session_state.current_job_id = None
if "showing_report" not in st.session_state:
    st.session_state.showing_report = False
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "last_status_check" not in st.session_state:
    st.session_state.last_status_check = 0
if "status_visible" not in st.session_state:
    st.session_state.status_visible = False

# Import the page modules
from pages.upload_audit import main as upload_audit_main
from pages.view_reports import main as view_reports_main

# Define the pages for the navigation system
def upload_audit_page():
    upload_audit_main()

def view_reports_page():
    view_reports_main()

# Configure navigation
current_page = st.navigation(
    pages=[
        st.Page(upload_audit_page, title="Upload Case Audit"),
        st.Page(view_reports_page, title="View Audit Reports")
    ]
)

# Run the current page
current_page.run() 