import aiohttp
import asyncio
import aioftp
import json
from pathlib import Path


class AsyncDownloader:
    def __init__(self, debugflag, webhook):
        self.debug = debugflag
        self.discordwebhook = webhook
        self.accounts_file = "ftp_accounts.txt"
        self.tracking_file = "download_tracking.json"
        self.tracking_data = self.read_tracking_file(self.tracking_file)

    def set_debug(self, somebool):
        """Sets the debug flag"""
        self.debug = somebool

    def set_discord_webhook(self, webhook):
        self.discordwebhook = webhook

    def read_tracking_file(self, file_path):
        """Read the tracking file and return its contents."""
        try:
            if Path(file_path).exists():
                with open(file_path, "r") as f:
                    return json.load(f)
        except Exception as f:
            print(f"File Load Error! {f}")
            print("Setting to EMPTY!")
            return {}

    def write_tracking_file(self, file_path, data):
        """Write data to the tracking file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            print("File tracking updated successfully.")
        except Exception as e:
            print(f"Error updating file tracking: {e}")

    def update_file_tracking(self):
        """Update the tracking file with the current state of downloaded files."""
        downloaded_files = {}
        for local_dir in Path(".").glob("*"):
            if local_dir.is_dir():
                for file in local_dir.glob("*"):
                    downloaded_files[file.name] = local_dir.name
        self.write_tracking_file(self.tracking_file, downloaded_files)

    def debugmsg(self, message):
        """Send Debugging Messages"""
        if self.debug:
            print(message)

    def read_ftp_accounts(self):
        """Read FTP accounts from the specified file."""
        accounts = []
        with open(self.accounts_file, "r") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(":::")
                    if len(parts) == 2:
                        host, creds = parts
                        user, passwd = creds.split(":")
                        accounts.append({"host": host, "user": user, "passwd": passwd})
        return accounts

    async def send_discord_notification(self, message):
        """Send a notification to Discord."""
        if self.discordwebhook:
            data = {"content": message}
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(self.discordwebhook, json=data) as response:
                        if response.status == 200:
                            print("Notification sent to Discord.")
                        else:
                            print(f"Failed to send notification, status code: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error sending notification to Discord: {e}")

    async def download_files(self, host, port, login, password):
        """Download files from the FTP server."""
        local_dir = Path(f"./{host.replace(':', '_')}")
        local_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.debugmsg(f"Connecting {login} to server")
            async with aioftp.Client.context(host, port, login, password) as client:
                self.debugmsg(f"ITHINK Connected Listing for {login}")
                for path, info in (await client.list(recursive=True)):
                    if info["type"] == "file":
                        self.debugmsg(str(path.name))
                        if str(path.name) not in self.tracking_data:
                            print(f"Downloading from {host}: {path}")
                            if self.discordwebhook != None:
                                self.debugmsg("Sending Discord Message...")
                                self.send_discord_notification(f"New File Detected at {host}: {str(path.name)}")
                            await client.download(path, local_dir)
                        else:
                            self.debugmsg(f"Already downloaded: {path}")
        except Exception as e:
            print(f"Error Handling {login} at {host}: {e}")

    async def main(self):
        self.update_file_tracking()
        self.tracking_data = self.read_tracking_file(self.tracking_file)
        accounts = self.read_ftp_accounts()
        tasks = [asyncio.create_task(self.download_files(account['host'], 21, account['user'], account['passwd'])) for account in accounts]
        await asyncio.gather(*tasks)
        print("All Done =)")


if __name__ == "__main__":
    runner = AsyncDownloader(debugflag=True, webhook="YOUR_DISCORD_WEBHOOK_URL")
    asyncio.run(runner.main())
