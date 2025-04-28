import os
import ftplib
import time
import shutil
import sys
from PyQt5.QtWidgets import QMessageBox

FTP_HOST = "31.24.251.69"
FTP_USER = "user250467"
FTP_PASSWORD = "DdO1ko5V0NwP"
REMOTE_VERSION_FILE = "version.txt"
LOCAL_VERSION_FILE = "version.txt"
REMOTE_UPDATE_FOLDER = "/dist"
LOCAL_APP_FOLDER = os.path.dirname(os.path.abspath(__file__))

def get_ftp_connection():
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASSWORD)
    return ftp

def get_remote_version(ftp):
    try:
        with open("remote_version.txt", "wb") as f:
            ftp.retrbinary(f"RETR {REMOTE_VERSION_FILE}", f.write)
        with open("remote_version.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None

def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None

def download_and_replace_files(ftp):
    filenames = ftp.nlst(REMOTE_UPDATE_FOLDER)
    for filename in filenames:
        local_file = os.path.join(LOCAL_APP_FOLDER, os.path.basename(filename))
        with open(local_file, "wb") as f:
            ftp.retrbinary(f"RETR {filename}", f.write)

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def check_for_update(parent=None):
    try:
        ftp = get_ftp_connection()
        remote_version = get_remote_version(ftp)
        local_version = get_local_version()

        if not remote_version:
            print("Не удалось получить версию с сервера.")
            return

        if remote_version != local_version:
            reply = QMessageBox.question(parent, "Доступно обновление",
                                         f"Обнаружена новая версия: {remote_version}.\nХотите обновить сейчас?",
                                         QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                download_and_replace_files(ftp)
                with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(remote_version)
                QMessageBox.information(parent, "Обновление", "Обновление завершено. Программа перезапустится.")
                ftp.quit()
                restart_program()
            else:
                ftp.quit()
        else:
            if parent:
                QMessageBox.information(parent, "Обновление", "У вас последняя версия.")
            ftp.quit()
    except Exception as e:
        print(f"Ошибка при обновлении: {e}")
