from scapy.all import *
from telegram.ext import *
import json
import time


def get_mac_vendor(mac):
    """
    This function gets the mac address vendor by reading it from a file.
    :param mac: the mac address in question
    :return: the vendor name or 'Unknown' if not found
    """
    mac = mac.upper().replace(':', '')[0:6]  # format the mac address
    try:
        with open("mac-vendor.txt", "r") as f:
            for line in f:
                if mac in line:
                    return line[7:]
    except FileNotFoundError:
        exit("Error: mac-vendor.txt file not found.")
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
                msg = "New device connected: {} ({})".format(
                    mac_vendor, ip_address)
                context.bot.send_message(chat_id=CHAT_ID, text=msg)
            connected_hosts[mac_address] = (mac_vendor, ip_address)
        # check for disconnected devices
        for mac_address in old_hosts:
            if mac_address not in hosts:
                mac_vendor, ip_address = connected_hosts[mac_address]
                msg = "Device disconnected: {} ({})".format(
                    mac_vendor, ip_address)
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
        msg += "{} ({})\n".format(mac_vendor, ip_address)
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


with open('auth.json') as f:
    auth = json.load(f)
    TOKEN = auth["TOKEN"]
    CHAT_ID = auth["CHAT_ID"]
    NETWORK = "192.168.56.0/24"

start_bot()
