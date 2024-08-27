import os
import ftplib
import pickle
import requests
from pathlib import Path

debug = True

# File containing FTP account details
accounts_file = "ftp_accounts.txt"

# File to keep track of downloaded files
tracking_file = "downloaded_files.pkl"

def debugmsg(message):
    if debug == True:
        print(message)

def regenerate_downloaded_files_pickle():
    downloaded_files = {}
    for local_dir in Path(".").glob("*"):
        if local_dir.is_dir():
            for file in local_dir.glob("*"):
                # Assuming file names are unique across different directories
                downloaded_files[file.name] = local_dir.name
    save_downloaded_files(downloaded_files)
    print("Regenerated the pickle file with current directory contents.")

def load_downloaded_files():
    if Path(tracking_file).exists():
        with open(tracking_file, "rb") as f:
            return pickle.load(f)
    return {}

def save_downloaded_files(downloaded_files):
    with open(tracking_file, "wb") as f:
        pickle.dump(downloaded_files, f)

def connect_ftp(host, user, passwd):
    ftp = ftplib.FTP(host)
    print(f"Connecting to {host} with user {user}")
    ftp.login(user, passwd)
    return ftp

def download_file(ftp, remote_file, local_path):
    with open(local_path, "wb") as f:
        ftp.retrbinary(f"RETR {remote_file}", f.write)

def read_ftp_accounts(file_path):
    accounts = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():  # Skip empty lines
                parts = line.strip().split(":::")
                if len(parts) == 2:
                    host, creds = parts
                    user, passwd = creds.split(":")
                    accounts.append({"host": host, "user": user, "passwd": passwd})
    return accounts

def send_discord_notification(message, webhook_url):
    if webhook_url:  # Only send notification if webhook_url is provided
        data = {
            "content": message
        }
        try:
            response = requests.post(webhook_url, json=data)
            response.raise_for_status()
            print("Notification sent to Discord.")
        except requests.exceptions.RequestException as e:
            print(f"Error sending notification to Discord: {e}")

def monitor_ftp(webhook=None, notify=False):
    downloaded_files = load_downloaded_files()
    accounts = read_ftp_accounts(accounts_file)

    for account in accounts:
        try:
            ftp = connect_ftp(account["host"], account["user"], account["passwd"])
            print("Logged In!")
            ftp.cwd('/')  # Set this to the desired remote directory if needed
            debugmsg("Directory Set")
            remote_files = ftp.nlst()
            local_dir = Path(f"./{account['host'].replace(':', '_')}")
            local_dir.mkdir(parents=True, exist_ok=True)
            
            # Filter out non-file entries
            remote_files = [f for f in remote_files if f and f not in (".", "..")]
            debugmsg("Time To Download!")
            for remote_file in remote_files:
                debugmsg(remote_file)
                if remote_file:
                    local_file = local_dir / remote_file
                    if remote_file not in downloaded_files:
                        print(f"Downloading {remote_file} from {account['host']}")
                        try:
                            download_file(ftp, remote_file, local_file)
                            downloaded_files[remote_file] = account['host']
                            
                            # Send notification to Discord if notify is True and webhook is provided
                            if notify and webhook:
                                message = f"New file downloaded: `{remote_file}` from `{account['host']}`"
                                send_discord_notification(message, webhook)
                        except Exception as download_error:
                            print(f"Error downloading file {remote_file}: {download_error}")

            # Save the state of downloaded files
            debugmsg("We are done. Moving on...")
            save_downloaded_files(downloaded_files)
            debugmsg("Closing Connection...")
            ftp.quit()
        except Exception as e:
            print(f"Error processing account {account['host']}: {e}")

if __name__ == "__main__":
    # Example usage:
    # monitor_ftp(webhook="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL", notify=True)
    
    # Call with no webhook or notification
    monitor_ftp()
    
    # Call with webhook and notifications enabled
    # monitor_ftp(webhook="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL", notify=True)
    
    # Call with webhook but notifications disabled
    # monitor_ftp(webhook="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL", notify=False)
