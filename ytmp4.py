import yt_dlp
import sys
import os  # Import os module to check file existence
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Custom Logger to suppress yt-dlp's internal output
class QuietLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


# Function to convert bytes to MB for visual display only
def bytes_to_mb(bytes):
    return round(bytes / (1024 * 1024), 2)


# Function to update the progress bar
def progress_hook(d):
    if d['status'] == 'downloading':
        # Get total_bytes and downloaded_bytes from the progress hook
        total_bytes = d.get('total_bytes')
        downloaded_bytes = d.get('downloaded_bytes')

        # Only perform calculations if total_bytes and downloaded_bytes are valid
        if total_bytes is not None and downloaded_bytes is not None and total_bytes != 0:
            # Convert bytes to MB for display
            downloaded_mb = bytes_to_mb(downloaded_bytes)
            total_mb = bytes_to_mb(total_bytes)

            # Display the custom progress bar
            progress = int((downloaded_bytes / total_bytes) * 50)  # 50 is the length of the bar
            bar = "█" * progress + "-" * (50 - progress)

            # Print the progress bar with the downloaded MB / total MB
            sys.stdout.write(f"\r{Fore.CYAN}[{bar}] {Fore.GREEN}{downloaded_mb:.2f} MB {Style.RESET_ALL}/ {Fore.YELLOW}{total_mb:.2f} MB")
            sys.stdout.flush()
        else:
            # In case total_bytes or downloaded_bytes are invalid, just show downloaded MB
            if downloaded_bytes is not None:
                downloaded_mb = bytes_to_mb(downloaded_bytes)
                sys.stdout.write(f"\r{Fore.CYAN}Downloading... {Fore.GREEN}{downloaded_mb:.2f} MB / - MB")
                sys.stdout.flush()
    elif d['status'] == 'finished':
        # Clear the progress bar completely (move cursor to the start of the line and overwrite it)
        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line

        # When the download finishes, finalize the progress bar and print only the speed info
        downloaded_mb = bytes_to_mb(d.get('downloaded_bytes', 0))
        download_speed = d.get('speed', 0)  # Get download speed (in bytes per second)
        download_speed_mbps = bytes_to_mb(download_speed) * 8 / 1000 if download_speed else 0  # Convert to Mbps

        # Print the final message without redundant size info or progress bar
        sys.stdout.write(f"{Fore.GREEN}Download finished: {downloaded_mb:.2f} MB at {download_speed_mbps:.2f} Mbps\n")
        sys.stdout.flush()


# Function to download YouTube video (or playlist) using yt-dlp with a custom progress bar
def download_video(url, output_dir='.'):
    try:
        # Options for downloading the video or playlist
        ydl_opts = {
            'format': 'best',  # Choose the best quality
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Save to specified directory
            'progress_hooks': [progress_hook],  # Hook to update progress bar
            'quiet': True,  # Suppress yt-dlp's internal output
            'no_warnings': True,  # Disable warnings
            'logger': QuietLogger(),  # Suppress all internal yt-dlp logs
            'noplaylist': False,  # Ensure playlist is handled correctly
            'extract_flat': True,  # Only fetch URLs from the playlist
        }

        # Create a yt-dlp object and start downloading
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract URL for the first video
            info_dict = ydl.extract_info(url, download=False)

            # If it's a playlist, process each video
            if 'entries' in info_dict:  # This means it's a playlist
                print(f"{Fore.YELLOW}Preparing download for playlist: {Fore.CYAN}{info_dict['title']}{Style.RESET_ALL}")

                # Create subdirectory for playlist if it doesn't exist
                playlist_dir = os.path.join(output_dir, info_dict['title'])
                if not os.path.exists(playlist_dir):
                    os.makedirs(playlist_dir)
                    print(f"{Fore.GREEN}Created subdirectory: {playlist_dir}{Style.RESET_ALL}")
                
                # Update the output template to include the playlist directory
                ydl_opts['outtmpl'] = os.path.join(playlist_dir, '%(title)s.%(ext)s')
                with yt_dlp.YoutubeDL(ydl_opts) as playlist_ydl:
                    # Check all filenames before downloading
                    entries_to_download = []
                    for idx, entry in enumerate(info_dict['entries'], start=1):
                        entry['ext'] = 'mp4'  # Ensure the extension is set correctly
                        filename = playlist_ydl.prepare_filename(entry)
                        base_filename = os.path.basename(filename)
                        full_path = os.path.join(playlist_dir, base_filename)
                        
                        # Check if the file already exists
                        if os.path.exists(full_path):
                            print(f"{Fore.RED}File already exists: {Fore.YELLOW}{full_path}{Style.RESET_ALL}. {Fore.RED}Skipping download.")
                        else:
                            entries_to_download.append((idx, entry['url'], full_path))

                    # Download the videos that do not exist
                    for idx, video_url, full_path in entries_to_download:
                        print(f"{Fore.YELLOW}Starting download for video {idx}: {Fore.CYAN}{full_path}{Style.RESET_ALL}")
                        try:
                            playlist_ydl.download([video_url])
                        except Exception as e:
                            print(f"{Fore.RED}An error occurred while downloading {full_path}: {e}")
            else:
                # It's a single video, download it
                filename = ydl.prepare_filename(info_dict)
                base_filename = os.path.basename(filename)
                full_path = os.path.join(output_dir, base_filename)
                if os.path.exists(full_path):  # Check if the file already exists
                    print(f"{Fore.RED}File already exists: {Fore.YELLOW}{full_path}{Style.RESET_ALL}. {Fore.RED}Skipping download.")
                else:
                    print(f"{Fore.YELLOW}Starting download for: {Fore.CYAN}{full_path}{Style.RESET_ALL}")
                    ydl.download([url])  # Download the video

    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Download interrupted by user. {Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}")

# Main function to handle URL from command-line argument
if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"{Fore.RED}Usage: python downloader.py <YouTube_URL> [output_directory]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) == 3 else '.'
    print(f"{Fore.CYAN}Starting download for URL: {Fore.GREEN}{url}")
    print(f"{Fore.CYAN}Output directory: {Fore.GREEN}{output_dir}")
    download_video(url, output_dir)
