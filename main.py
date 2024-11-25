from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pymediainfo import MediaInfo
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
API_KEY = os.getenv("API_KEY")

def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

def get_detailed_metadata(file_path: str):
    try:
        media_info = MediaInfo.parse(file_path)
        detailed_metadata = {
            "File": {
                "Filename": os.path.basename(file_path),
                "File Size": f"{os.path.getsize(file_path) / (1024 * 1024):.2f} MiB",
            },
            "Video": {},
            "Audio": {},
            "Composite": {}
        }
        
        for track in media_info.tracks:
            if track.track_type == "General":
                detailed_metadata["File"].update({
                    "File Type": track.file_extension.upper() if track.file_extension else "N/A",
                    "MIME Type": track.internet_media_type,
                    "Duration": f"{int(track.duration / 1000)} s" if track.duration else "N/A",
                    "Avg Bitrate": f"{track.overall_bit_rate / 1000:.1f} kbps" if track.overall_bit_rate else "N/A",
                    "Major Brand": track.format,
                    "Compatible Brands": track.other_format if hasattr(track, "other_format") else [],
                    "Create Date": track.encoded_date,
                    "Modify Date": track.tagged_date,
                })
            elif track.track_type == "Video":
                detailed_metadata["Video"].update({
                    "Codec": track.format,
                    "Width": track.width,
                    "Height": track.height,
                    "Frame Rate": track.frame_rate,
                    "Bit Depth": track.bit_depth,
                    "Compressor ID": track.codec_id,
                    "Rotation": track.rotation if hasattr(track, "rotation") else 0,
                })
            elif track.track_type == "Audio":
                detailed_metadata["Audio"].update({
                    "Audio Format": track.format,
                    "Channels": track.channel_s,
                    "Bits Per Sample": track.bit_depth,
                    "Sample Rate": track.sampling_rate,
                })
        
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
