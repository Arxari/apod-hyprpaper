#!/usr/bin/env python3
import os
import requests
import subprocess
import re
import time
from datetime import datetime
from pathlib import Path

WALLPAPER_DIR = "/home/arx/Pictures/Wallpapers/apod" # where wallpapers are saved
HYPRPAPER_CONFIG = os.path.expanduser("~/.config/hypr/hyprpaper.conf")
APOD_URL = "https://apod.nasa.gov/apod/"

def get_image_info(element, text):
    regex = f'<{element}="(image.*?)"'
    match = re.search(regex, text, re.IGNORECASE)
    
    if not match:
        return None, None, None
        
    file_url = match.group(1)
    if not file_url.startswith('http'):
        file_url = f"{APOD_URL}{file_url}"
        
    try:
        response = requests.head(file_url)
        response.raise_for_status()
        file_size = float(response.headers.get("content-length", 0))
        filename = os.path.basename(file_url)
        return file_url, filename, file_size
    except requests.RequestException:
        return None, None, None

def get_image_url():
    try:
        response = requests.get(APOD_URL)
        response.raise_for_status()
        
        file_url, filename, file_size = get_image_info('a href', response.text)
        
        if file_url is None or file_size < 500:
            file_url, filename, file_size = get_image_info('img src', response.text)
            
        if file_url is None or file_size < 500:
            print("Could not find a valid image on the APOD page")
            return None, None
            
        return file_url, filename
        
    except requests.RequestException as e:
        print(f"Error fetching APOD page: {e}")
        return None, None

def download_image(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        os.makedirs(WALLPAPER_DIR, exist_ok=True)
        
        if not filename:
            ext = '.jpg'
            filename = f"apod_{datetime.now().strftime('%Y%m%d')}{ext}"
        
        filepath = os.path.join(WALLPAPER_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

def update_hyprpaper_config(filepath):
    try:
        config_dir = os.path.dirname(HYPRPAPER_CONFIG)
        os.makedirs(config_dir, exist_ok=True)
        
        if os.path.exists(HYPRPAPER_CONFIG):
            with open(HYPRPAPER_CONFIG, 'r') as f:
                config_lines = f.readlines()
        else:
            config_lines = []

        new_config = []
        preload_found = False
        wallpaper_found = False

        for line in config_lines:
            if line.startswith('preload = '):
                new_config.append(f'preload = {filepath}\n')
                preload_found = True
            elif line.startswith('wallpaper = '):
                new_config.append(f'wallpaper = ,{filepath}\n')
                wallpaper_found = True
            else:
                new_config.append(line)

        if not preload_found:
            new_config.append(f'preload = {filepath}\n')
        if not wallpaper_found:
            new_config.append(f'wallpaper = ,{filepath}\n')

        with open(HYPRPAPER_CONFIG, 'w') as f:
            f.writelines(new_config)

        return True
    except Exception as e:
        print(f"Error updating config file: {e}")
        return False

def restart_hyprpaper(): # thanks hyprpaper for being so easy to use you become a nightmare
    try:
        subprocess.run(['killall', '-e', 'hyprpaper'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        
        time.sleep(1)
        subprocess.Popen(['hyprpaper'])
        time.sleep(1)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error restarting hyprpaper: {e}")
        return False

def main():
    image_url, filename = get_image_url()
    if not image_url:
        print("Failed to get APOD image URL")
        return

    filepath = download_image(image_url, filename)
    if not filepath:
        print("Failed to download APOD image")
        return

    if update_hyprpaper_config(filepath) and restart_hyprpaper():
        print("Wallpaper set successfully")
    else:
        print("Failed to set wallpaper")

if __name__ == "__main__":
    main()
