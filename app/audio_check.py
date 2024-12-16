import mimetypes
import magic  # You need to install python-magic
import os
import io
import subprocess
def guess_extension_from_file(file_path):
    try:
        # Detect the MIME type using the magic library
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        
        # Guess the file extension using mimetypes
        extension = mimetypes.guess_extension(mime_type)
        print(f"Detected MIME type: {mime_type}")
        print(f"Guessed file extension: {extension}")
        return extension
    except Exception as e:
        print(f"Error guessing extension: {e}")
        return None

# Example usage
file_path = r"temp\audio"
# extension = guess_extension_from_file(file_path)
# if extension:
#     print(f"File extension is likely: {extension}")
# else:
#     print("Could not determine the file extension.")
# import subprocess

def force_convert_to_wav(input_path, output_path):
    try:
        # Try forcing raw audio decoding
        result = subprocess.run(
            ["ffmpeg", "-f", "rawaudio", "-ar", "44100", "-ac", "2", "-i", input_path, output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"Conversion successful: {output_path}")
        else:
            print(f"FFmpeg error: {result.stderr}")
    except Exception as e:
        print(f"Error during conversion: {e}")

# Example usage
force_convert_to_wav("temp/audio.bin", "output.wav")
