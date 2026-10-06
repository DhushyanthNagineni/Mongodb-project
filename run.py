"""Launcher for the blog. Use the Anaconda ``blogenv`` Python to run this.

    conda activate blogenv
    python run.py
"""
from app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)