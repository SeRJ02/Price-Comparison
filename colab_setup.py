# === COLAB CELL 1: Setup & Dependencies ===
# Run this cell first in Google Colab

import subprocess
import os

# Install dependencies
subprocess.run(["pip", "install", "-r", "/content/drive/MyDrive/earnkaro_bot/requirements.txt"], check=True)

# Mount Google Drive
from google.colab import drive
drive.mount("/content/drive")

# Set working directory
os.chdir("/content/drive/MyDrive/earnkaro_bot/")

print("✅ Setup complete")
