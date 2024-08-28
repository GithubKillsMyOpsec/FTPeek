from FTPDL import monitor_ftp,regenerate_downloaded_files_pickle
from AsynFTPDL import AsyncDownloader
import time
import asyncio

version = "0.0.3"
def interactive_mode():
    print("     ____   __ __       _             ")
    print("    / __ \ / //_/___   (_)____   _____")
    print("   / /_/ // ,<  / _ \ / // __ \ / ___/")
    print("  / _, _// /| |/  __// // / / /(__  ) ")
    print(" /_/ |_|/_/ |_|\___//_//_/ /_//____/  ")

    print("FTPeek, FTP Monitoring and cloning tool.")
    print("This tool is for research purposes only.")
    print("Version " + version)
    debug = False
    waittime = 30
    while True:
        print("\n=======================================")
        print("\nSelect a module to run:")
        print("1. Monitor FTP")
        print("2. Regenerate PKL File Tracker")
        print("3. Run Async FTP Monitor (Beta)")
        print("4. Set Check Time Delay")
        print("5. Set Debug Flag")
        choice = input("Enter your choice: ")
        if choice == "1":
            webpls = input("Enter Discord Webhook (If applicable)")
            if webpls != '':
                print("Discord Webhook detected.")
                while True:
                    monitor_ftp(webpls, True)
                    time.sleep(waittime)
            else:
                print("No webhook detected. Manual Updating...")
                while True:
                    monitor_ftp()
                    time.sleep(waittime)
        elif choice =="2":
            print("Regenerating PKL File, please wait...")
            regenerate_downloaded_files_pickle()
        elif choice =="3":
            webpls = input("Enter Discord Webhook (If applicable)")
            if webpls != '':
                print("Discord Webhook detected.")
                while True:
                    runner = AsyncDownloader(debugflag=debug, webhook=webpls)
                    asyncio.run(runner.main())
                    time.sleep(waittime)
            else:
                print("No webhook detected. Manual Updating...")
                while True:
                    runner = AsyncDownloader(debugflag=debug, webhook=None)
                    asyncio.run(runner.main())
                    time.sleep(waittime)
        elif choice =="4":
            waittime = input("Enter The Sleep Time (In Seconds)")
        elif choice =="5":
            whatistheflag = input("Enter Flag State (T/F)")
            if whatistheflag == "T":
                debug = True
            else:
                debug = False




interactive_mode()
