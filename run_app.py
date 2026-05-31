import streamlit.web.cli as stcli
import os
import sys

def resolve_path(path):
    # If running as a compiled executable, get the temporary extraction path _MEIPASS
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Resolve the absolute path to the main app file
    app_path = resolve_path("app.py")
    
    # Configure Streamlit arguments programmatically
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false"
    ]
    
    # Trigger CLI entry point
    sys.exit(stcli.main())
