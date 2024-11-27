from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
import os
import subprocess
from dotenv import load_dotenv
import json

app = FastAPI()

load_dotenv()
API_KEY = os.getenv("API_KEY")

def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

def get_detailed_metadata(file_path: str):
    try:
        # Run ffprobe to get metadata
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        # Extract relevant details from the ffprobe output
        detailed_metadata = {
            "File": {
                "Filename": os.path.basename(file_path),
                "File Size": f"{os.path.getsize(file_path) / (1024 * 1024):.2f} MiB",
            },
            "Video": {},
            "Audio": {},
            "Composite": {}
        }

        # Extract general metadata
        for stream in metadata.get('streams', []):
            if stream['codec_type'] == 'video':
                detailed_metadata["Video"].update({
                    "Codec": stream.get('codec_name', 'N/A'),
                    "Width": stream.get('width', 'N/A'),
                    "Height": stream.get('height', 'N/A'),
                    "Frame Rate": eval(stream.get('r_frame_rate', '0')) if '/' in stream.get('r_frame_rate', '') else 'N/A',
                    "Bit Depth": stream.get('bits_per_raw_sample', 'N/A'),
                    "Rotation": stream.get('rotation', '0')
                })
            elif stream['codec_type'] == 'audio':
                detailed_metadata["Audio"].update({
                    "Audio Format": stream.get('codec_name', 'N/A'),
                    "Channels": stream.get('channels', 'N/A'),
                    "Sample Rate": stream.get('sample_rate', 'N/A')
                })
        
        # Extract file-level metadata (format details)
        format_info = metadata.get('format', {})
        detailed_metadata["File"].update({
            "File Type": format_info.get('format_name', 'N/A'),
            "MIME Type": format_info.get('mime_type', 'N/A'),
            "Duration": format_info.get('duration', 'N/A'),
            "Avg Bitrate": format_info.get('bit_rate', 'N/A'),
            "Create Date": format_info.get('tags', {}).get('creation_time', 'N/A')
        })
        
        # Calculate composite image size and megapixels (if video dimensions are available)
        if "Width" in detailed_metadata["Video"] and "Height" in detailed_metadata["Video"]:
            width = detailed_metadata["Video"]["Width"]
            height = detailed_metadata["Video"]["Height"]
            detailed_metadata["Composite"].update({
                "Image Size": f"{width}x{height}",
                "Megapixels": f"{(width * height) / 1e6:.3f}" if width and height else "N/A",
            })
        
        return detailed_metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing video: {e}")

@app.post("/parse-video-metadata/")
async def parse_video_metadata(api_key: str = Depends(verify_api_key), file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    file_path = f"./temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Get detailed metadata
    metadata = get_detailed_metadata(file_path)
    
    # Clean up the file after reading metadata
    os.remove(file_path)
    
    return {"metadata": metadata}

@app.get("/health/")
def health_check():
    return {"status": "API is up and running"}
