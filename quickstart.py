"""
Quick Start Script for Zintoo Backend
Initializes database, generates data, and starts server
"""
import sys
import os
import subprocess
from pathlib import Path

def setup_environment():
    """Setup Python environment"""
    print("🔧 Setting up Zintoo environment...")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("✓ Project directory set")
    return project_root

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Dependencies installed successfully")
    else:
        print(f"✗ Error installing dependencies:\n{result.stderr}")
        return False
    
    return True

def generate_data():
    """Generate synthetic data"""
    print("\n📊 Generating synthetic data...")
    
    result = subprocess.run(
        [sys.executable, "data/generate_data.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"⚠ Warning: Data generation encountered issues:\n{result.stderr}")
    
    return True

def start_server():
    """Start FastAPI server"""
    print("\n🚀 Starting Zintoo Backend Server...")
    print("\nServer will be available at: http://localhost:8000")
    print("API Documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 60)
    
    result = subprocess.run(
        [sys.executable, "backend/main.py"],
        text=True
    )
    
    return result.returncode == 0

def main():
    """Main setup and launch"""
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 16 + "ZINTOO BACKEND - QUICK START" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Setup environment
    project_root = setup_environment()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please install dependencies manually:")
        print("   pip install -r requirements.txt")
        return
    
    # Generate data
    if not generate_data():
        print("\n⚠ Data generation had issues, but continuing...")
    
    # Start server
    success = start_server()
    
    if success:
        print("\n✅ Server stopped gracefully")
    else:
        print("\n❌ Server encountered an error")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Zintoo Backend stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
