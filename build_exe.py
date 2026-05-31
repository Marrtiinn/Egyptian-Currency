import os
import sys
import subprocess

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    print("=" * 60)
    print("  EGYPTIAN CURRENCY COUNTER EXECUTABLE BUILDER (PyInstaller)")
    print("=" * 60)
    
    # 1. Verify and install requirements if missing
    install_and_import("PyInstaller")
    install_and_import("streamlit")
    install_and_import("ultralytics")
    
    import PyInstaller.__main__
    
    # Define files to package
    entrypoint = "run_app.py"
    app_file = "app.py"
    weights_file = "best.pt"
    
    if not os.path.exists(entrypoint):
        print(f"Error: Entrypoint '{entrypoint}' not found. Please run this in the project root.")
        sys.exit(1)
        
    if not os.path.exists(app_file):
        print(f"Error: Streamlit app script '{app_file}' not found.")
        sys.exit(1)
        
    if not os.path.exists(weights_file):
        print(f"Warning: Model weights '{weights_file}' not found in the current directory.")
        print("The build will proceed, but you must place 'best.pt' next to the resulting EXE.")
    
    # Define data separator (';' for Windows, ':' for Linux/macOS)
    sep = ";" if os.name == "nt" else ":"
    
    # PyInstaller arguments
    pyinstaller_args = [
        entrypoint,
        "--onefile",
        "--name=EgyptianCurrencyCounter",
        "--clean",
        # Collect all dependencies, static assets, and configurations for Streamlit and Ultralytics
        "--collect-all=streamlit",
        "--collect-all=ultralytics",
        # Bundle the streamlit app script
        f"--add-data={app_file}{sep}.",
    ]
    
    # Bundle model weights if they exist
    if os.path.exists(weights_file):
        pyinstaller_args.append(f"--add-data={weights_file}{sep}.")
    
    print("\nRunning PyInstaller with arguments:")
    print(" ".join(pyinstaller_args))
    print("\nStarting build process (this may take a few minutes as it compiles PyTorch, Streamlit, and YOLO dependencies)...")
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n" + "=" * 60)
        print("  BUILD SUCCESSFUL!")
        print("  Executable created at: dist/EgyptianCurrencyCounter.exe")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"  BUILD FAILED: {str(e)}")
        print("=" * 60)
        sys.exit(1)
