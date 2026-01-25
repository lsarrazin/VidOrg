import subprocess
import json
import os

class VideoUtils:
    @staticmethod
    def get_metadata(file_path):
        """Returns a dictionary of video metadata using ffprobe."""
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        cmd = [
            'ffprobe', 
            '-v', 'quiet', 
            '-print_format', 'json', 
            '-show_format', 
            '-show_streams', 
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Simple extraction
            info = {
                "Filename": os.path.basename(file_path),
                "Path": file_path,
                "Size": f"{os.path.getsize(file_path) / (1024*1024):.2f} MB",
            }
            
            # Format info
            fmt = data.get('format', {})
            duration = float(fmt.get('duration', 0))
            info["Duration"] = f"{int(duration // 60)}:{int(duration % 60):02d}s"
            info["Format"] = fmt.get('format_long_name', 'Unknown')
            
            # Stream info (primary video stream)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    info["Resolution"] = f"{stream.get('width')}x{stream.get('height')}"
                    info["Codec"] = stream.get('codec_name')
                    info["FPS"] = stream.get('avg_frame_rate')
                    break
                    
            return info
            
        except Exception as e:
            return {"error": str(e)}
