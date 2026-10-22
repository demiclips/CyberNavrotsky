#Amit Navrotsky and Gal Katz Zamir

import os
import shutil
import time
import urllib.parse
import webbrowser
import win32file
import win32con
from datetime import datetime
import threading

#types of images
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

#api returns numbers
ACTIONS = {
    1: "Created",
    2: "Deleted",
    3: "Modified",
    4: "Renamed (Old Name)",
    5: "Renamed (New Name)"
}
#3 types of flags last thing worte file name and file directory
FLAGS = (
    win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
    win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
    win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
)

def listen_for_exit():
    """
    back thread that just runs and checks if inputed exit to terminate everything
    :return: none
    """
    while True:
        cmd = input().strip().lower()
        if cmd == "exit":
            print("\nExit command received. Program terminating...")
            os._exit(0)

#input of the directory
while True:
    target_dir = input("Enter directory path to monitor: ").strip()
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        target_dir = os.path.abspath(target_dir)
        break
    else:
        print("Invalid directory path or path does not exist. Try again.\n")

#sets direction to the path + images
destination_dir = os.path.join(target_dir, "images")
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)

pic = input("Enter picture search term: ").strip()


url = f"https://www.google.com/search?q={urllib.parse.quote(pic)}&tbm=isch"
webbrowser.open(url) #url to open in google

exit_thread = threading.Thread(target=listen_for_exit, daemon=True)
exit_thread.start()

#directory handle for WIN_API
FILE_LIST_DIRECTORY = 0x0001

h_directory = win32file.CreateFile(
    target_dir,
    FILE_LIST_DIRECTORY,
    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
    None,
    win32con.OPEN_EXISTING,
    win32con.FILE_FLAG_BACKUP_SEMANTICS,
    None
)

log_file_path = os.path.join(target_dir, "monitor_log.log")
print(" Type 'exit' and press Enter to quit.\n")

#main loop waiting for flag (is blocking)
while True:
    try:
        results = win32file.ReadDirectoryChangesW(h_directory,1024,True,FLAGS, None,None)

        for action_code, filename in results:
            #no need to add if it is in monitor)log
            if filename == "monitor_log.log" or filename.startswith("images"):
                continue

            #creates and puts the log msg s
            action_name = ACTIONS.get(action_code, f"Unknown ({action_code})")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] File: '{filename}' | Action: {action_name}"


            print(log_entry)
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(log_entry + "\n")


            #if it is create and it is an image copy it to the folder of images
            if action_code == 1 and filename.lower().endswith(IMAGE_EXTENSIONS):
                src_path = os.path.join(target_dir, filename)
                dst_path = os.path.join(destination_dir, os.path.basename(filename))

                # give time to download
                time.sleep(0.5)

                #if the image exist skip it no need to copy again
                if os.path.exists(src_path):
                    if os.path.exists(dst_path):
                        print(f"Image '{filename}' already exists in images folder. Skipped copy.")
                    else:
                        shutil.copy(src_path, dst_path)
                        print(f"COPIED IMAGE: '{filename}' -> {destination_dir}")

    except Exception:
        print("Program closed cleanly.")
        break