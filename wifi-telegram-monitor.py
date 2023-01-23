from scapy.all import *
from telegram.ext import *
import json
import time
import requests


def get_mac_vendor(mac):
    """
    This function takes in a MAC address as a string and returns the vendor of that address.
    If the vendor cannot be determined, the function returns 'Unknown'.
    :param mac: the mac address in question
    :return: the vendor name or 'Unknown' if not found
    """
    url = "https://api.macvendors.com/" + mac
    r = requests.get(url)
    # Check if the API call is successful (status code 200)
    if r.status_code == 200:
        return r.text
    # format the mac address
    mac = mac.upper().replace(':', '')[0:6]
    try:
        # open the local file to search for the mac address
        with open("mac-vendor.txt", "r", encoding='utf-8') as f:
            for line in f:
                if mac in line:
                    # return the vendor name after the mac address in the file
                    return line[7:]
    except FileNotFoundError:
        exit("Error: mac-vendor.txt file not found.")
    # if mac address is not found in the file or file not found
    return 'Unknown'


def start_command(update, context):
    """
    This function scans the network and sends a message to the Telegram bot when a new device is connected or disconnected.
    :param update: update object for the Telegram bot
    :param context: context object for the Telegram bot
    """
    connected_hosts = {}
    old_hosts = []
    while True:
        # scan the network
        ans, _ = arping(NETWORK, verbose=0)
        hosts = [host[1].src for host in ans]
        # check for new or updated devices
        for host in ans:
            mac_address = host[1].src
            mac_vendor = get_mac_vendor(mac_address).strip()
            ip_address = host[1].psrc
            if mac_address not in connected_hosts:
                msg = "New device connected: {} ({} - {})".format(
                    mac_vendor, ip_address, mac_address)
                context.bot.send_message(chat_id=CHAT_ID, text=msg)
            connected_hosts[mac_address] = (mac_vendor, ip_address)
        # check for disconnected devices
        for mac_address in old_hosts:
            if mac_address not in hosts:
                mac_vendor, ip_address = connected_hosts[mac_address]
                msg = "Device disconnected: {} ({} - {})".format(
                    mac_vendor, ip_address, mac_address)
                context.bot.send_message(chat_id=CHAT_ID, text=msg)
                del connected_hosts[mac_address]
        old_hosts = hosts
        time.sleep(10)


def showall_command(update, context):
    """
    This function sends a message to the Telegram bot with the connected devices.
    :param update: update object for the Telegram bot
    :param context: context object for the Telegram bot
    """
    msg = ""
    ans, _ = arping(NETWORK, verbose=0)
    # check for new or updated devices
    for host in ans:
        mac_address = host[1].src
        mac_vendor = get_mac_vendor(mac_address).strip()
        ip_address = host[1].psrc
        msg += "[+] {} ({} - {})\n".format(mac_vendor, ip_address, mac_address)
    context.bot.send_message(chat_id=CHAT_ID, text=msg)


def error(update, context):
    """
    This function prints the update and error message if an error occurs in the Telegram bot.
    :param update: update object for the Telegram bot
    :param context: context object for the Telegram bot
    """
    print(f"Update {update} caused error {context.error}")


def start_bot():
    """
    This function starts the Telegram bot and sets up the command handlers.
    """
    updater = Updater(
        TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_command, run_async=True))
    dp.add_handler(CommandHandler("showall", showall_command))
    dp.add_error_handler(error)
    updater.start_polling()
    print("[+] BOT has started")


with open('conf.json') as f:
    conf = json.load(f)
    TOKEN = conf["TOKEN"]
    CHAT_ID = conf["CHAT_ID"]
    NETWORK = conf["NETWORK"]
    INTERVAL = conf["INTERVAL"]

start_bot()
