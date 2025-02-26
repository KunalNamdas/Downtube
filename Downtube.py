import yt_dlp
from optparse import OptionParser
from setup.sprint import sprint
from setup.colors import c, r, ran, lr, lc, lg, g, ly, y
from setup.banner import banner, banner2, clear
import sys
import os
import logging
import signal
import subprocess

# Setup logging
logging.basicConfig(
    filename='downloader.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Help menu
usage = """
<Script> [Options]

[Options]:
  -h, --help        show this help message and exit.
  -a, --audio-only  Flag to download only the audio source (True/False).
  -p, --playlist    Playlist flag if the provided link is a playlist not a single video.
  -u, --url         Parameter used to add YouTube link.
  -f, --file        Parameter used to add file that contains some YouTube links.
  -o, --output-dir  Directory to save the downloaded files.
  -q, --quality     Desired video quality (e.g., 720, 1080).

Notes:
1) You can't pass both -f and -u at the same time.
2) If a file that exists has the same name as a file to be downloaded, the current file WILL NOT be overwritten.
"""

# Load args
parser = OptionParser(usage=usage)
parser.add_option("-a", "--audio-only", action="store_true", dest="only_audio",
                  help="Flag to download only the audio source (True/False).")
parser.add_option("-p", "--playlist", action="store_true", dest="playlist",
                  help="Playlist flag if the provided link is a playlist not a single video.")
parser.add_option("-u", "--url", dest="url",
                  help="Parameter used to add YouTube link.")
parser.add_option("-f", "--file", dest="file",
                  help="Parameter used to add file that contains some YouTube links.")
parser.add_option("-o", "--output-dir", dest="output_dir", default="Downloads",
                  help="Directory to save the downloaded files.")
parser.add_option("-q", "--quality", dest="quality", default="720",
                  help="Desired video quality (e.g., 720, 1080).")

def download_with_ytdlp(url, only_audio=False, quality="720"):
    """Downloads content from YouTube using yt-dlp"""
    if only_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # Download audio as WAV for better conversion
                'preferredquality': '192',
            }],
            'postprocessor_args': ['-ar', '44100'],  # Set audio sample rate
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logging.info(f"Downloaded: {url}")
        if only_audio:
            # Convert WAV to MP3 using ffmpeg
            filename = f"{yt_dlp.YoutubeDL().extract_info(url, download=False)['title']}.wav"
            mp3_filename = filename.replace('.wav', '.mp3')
            subprocess.run(['ffmpeg', '-i', filename, '-q:a', '0', '-map', 'a', mp3_filename], check=True)
            os.remove(filename)  # Remove the WAV file after conversion
        return 1
    except Exception as e:
        logging.error(f"Error downloading {url}: {str(e)}")
        return 0

def choice_single_link(link, only_audio, quality):
    """Walkthrough algorithm if -p/--playlist flag is False"""
    return download_with_ytdlp(link, only_audio, quality)

def choice_playlist(link, only_audio, quality):
    """Walkthrough algorithm if -p/--playlist flag is True"""
    return download_with_ytdlp(link, only_audio, quality)

def file_handler(path, only_audio, quality):
    """Reads file that contains YouTube links and downloads them"""
    count = 0
    try:
        with open(path, "r") as file:
            for line in file.readlines():
                url = line.strip()
                if not url or "youtube" not in url:
                    continue
                count += choice_single_link(url, only_audio, quality)
    except FileNotFoundError:
        logging.error(f"File not found: {path}")
    except PermissionError:
        logging.error(f"Permission denied: {path}")
    except Exception as e:
        logging.error(f"Error reading file {path}: {str(e)}")
    return count

def check_download_folder(output_dir):
    """Checks if the specified folder exists. If not, creates one."""
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except PermissionError:
            logging.error(f"Couldn't create '{output_dir}' folder. Check write permissions.")
            raise
    os.chdir(output_dir)

def signal_handler(sig, frame):
    """Handles the Ctrl+C signal."""
    print("\nProgram stopped successfully.")
    logging.info("Program stopped by user.")
    sys.exit(0)

# Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Start checkpoint
if __name__ == "__main__":
    clear()
    banner()
    (options, args) = parser.parse_args()

    # flags
    only_audio = options.only_audio
    playlist = options.playlist
    link = options.url
    file = options.file
    output_dir = options.output_dir
    quality = options.quality

    # validate arguments
    if not bool(link) ^ bool(file):  # xor gate
        print(usage)
        sys.exit()

    # prepare Downloads directory
    check_download_folder(output_dir)

    try:
        if link:
            if playlist:
                count = choice_playlist(link, only_audio, quality)
            else:
                count = choice_single_link(link, only_audio, quality)
        else:
            count = file_handler(file, only_audio, quality)

        # print a small report
        print(f"\n[+] Downloaded {count} items")
        logging.info(f"Downloaded {count} items.")
    except KeyboardInterrupt:
        print("\nProgram stopped successfully.")
        logging.info("Program stopped by user.")
