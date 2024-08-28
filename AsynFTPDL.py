import aiohttp
import asyncio
import aioftp
import json
from pathlib import Path

debug = True

accounts_file = "ftp_accounts.txt"
tracking_file = "download_tracking.json"

def read_tracking_file(file_path):
    """Read the tracking file and return its contents."""
    try:
        if Path(file_path).exists():
            with open(file_path, "r") as f:
                return json.load(f)
    except Exception as f:
        print(f"File Load Error! {f}")
        print("Setting to EMPTY!")
        return {}

def write_tracking_file(file_path, data):
    """Write data to the tracking file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        print("File tracking updated successfully.")
    except Exception as e:
        print(f"Error updating file tracking: {e}")

def update_file_tracking(tracking_file_path):
    """Update the tracking file with the current state of downloaded files."""
    downloaded_files = {}
    for local_dir in Path(".").glob("*"):
        if local_dir.is_dir():
            for file in local_dir.glob("*"):
                downloaded_files[file.name] = local_dir.name
    write_tracking_file(tracking_file_path, downloaded_files)

def debugmsg(message):
    """Send Debugging Messages"""

    if debug:
        print(message)

def read_ftp_accounts(file_path):
    """Read FTP accounts from the specified file."""
    accounts = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                parts = line.strip().split(":::")
                if len(parts) == 2:
                    host, creds = parts
                    user, passwd = creds.split(":")
                    accounts.append({"host": host, "user": user, "passwd": passwd})
    return accounts

async def send_discord_notification(message, webhook_url):
    """Send a notification to Discord."""
    if webhook_url:
        data = {"content": message}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, json=data) as response:
                    if response.status == 200:
                        print("Notification sent to Discord.")
                    else:
                        print(f"Failed to send notification, status code: {response.status}")
            except aiohttp.ClientError as e:
                print(f"Error sending notification to Discord: {e}")

async def download_files(host, port, login, password):
    """Download files from the FTP server."""
    local_dir = Path(f"./{host.replace(':', '_')}")
    local_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        debugmsg(f"Connecting {login} to server")
        async with aioftp.Client.context(host, port, login, password) as client:
            debugmsg(f"ITHINK Connected Listing for {login}")
            for path, info in (await client.list(recursive=True)):
                if info["type"] == "file":
                    debugmsg(str(path.name))
                    if str(path.name) not in tracking_data:
                        print(f"Downloading from {host}: {path}")
                        await client.download(path, local_dir)
                    else:
                        debugmsg(f"Already downloaded: {path}")
    except Exception as e:
        print(f"Error Handling {login} at {host}: {e}")

async def main():
    global tracking_data
    accounts = read_ftp_accounts(accounts_file)
    update_file_tracking(tracking_file)
    tracking_data = read_tracking_file(tracking_file)
    tasks = [asyncio.create_task(download_files(account['host'], 21, account['user'], account['passwd'])) for account in accounts]
    await asyncio.gather(*tasks)
    print("All Done =)")

if __name__ == "__main__":
    asyncio.run(main())
