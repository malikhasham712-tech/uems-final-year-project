import shutil
import os
from datetime import datetime

# Database path
DB_PATH = r"E:\Project 619\event_management_system\uems\db.sqlite3"

# Backup folder
BACKUP_FOLDER = r"E:\Project 619\db_backups"

# Ensure backup folder exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# Timestamp for filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Backup file path
backup_file = os.path.join(BACKUP_FOLDER, f"db_backup_{timestamp}.sqlite3")

# Copy database
shutil.copy2(DB_PATH, backup_file)

print("Backup created successfully:")
print(backup_file)