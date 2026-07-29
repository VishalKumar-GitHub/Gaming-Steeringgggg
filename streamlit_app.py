import platform
from datetime import datetime, timezone

import streamlit as st

st.set_page_config(
    page_title="Gaming Steering - Cloud Demo",
    page_icon="🎮",
    layout="wide",
)

st.title("Gaming Steering Cloud Demo")
st.caption("Deployed status page for the virtual steering project")

st.info(
    "This cloud app is a deploy-safe demo. The real controller needs a local desktop "
    "session with webcam and keyboard access, so run app.py on your Windows PC."
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Cloud Status")
    st.write("Service: Online")
    st.write(f"Server time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"Python platform: {platform.platform()}")

with col2:
    st.subheader("What Works Here")
    st.markdown("- Deployment validation")
    st.markdown("- Project info and usage guide")
    st.markdown("- Health status dashboard")

st.divider()

st.subheader("Run The Real Controller Locally (Windows)")
st.code("AUTO_RUN_WINDOWS.bat", language="batch")
st.markdown("Or in PowerShell:")
st.code("powershell -ExecutionPolicy Bypass -File .\\run_windows_fast.ps1", language="powershell")

st.subheader("Why local run is required")
st.markdown(
    "- Webcam feed is local hardware.\n"
    "- Keyboard control (pynput) targets local game windows.\n"
    "- Cloud containers cannot inject keys into your PC game."
)
