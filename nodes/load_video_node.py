import os
import cv2
import subprocess
import hashlib
import folder_paths

from .base_media_loader import BaseMediaLoaderNode
from .xmp_utils import get_xmp_metadata

class ComfyVideoMock:
    def __init__(self, filepath, width=512, height=512):
        self.filepath = filepath
        self.width = width
        self.height = height
        
    def get_dimensions(self):
        # Returns shape (width, height)
        return (self.width, self.height)
        
    def save_to(self, filepath, **kwargs):
        import shutil
        shutil.copy2(self.filepath, filepath)
        
    def __str__(self):
        return self.filepath

class LoadVideoNode(BaseMediaLoaderNode):
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        # Filter for common video extensions
        video_extensions = ['.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v']
        video_files = [f for f in files if any(f.lower().endswith(ext) for ext in video_extensions)]
        
        return {"required": {
                    "video": (sorted(video_files), {"video_upload": True}),
                    "force_height": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 8})
                    }
                }

    CATEGORY = "DeepGen/Loaders"
    RETURN_TYPES = ("VIDEO", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("video", "description", "dialogues", "assets")
    FUNCTION = "load_video"

    def load_video(self, video, force_height=0):
        video_path = folder_paths.get_annotated_filepath(video)
        orig_video_path = video_path
        
        # Determine original width/height using cv2
        cap = cv2.VideoCapture(video_path)
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        width = orig_width or 512
        height = orig_height or 512
        
        if force_height > 0 and height != force_height and orig_height > 0:
            width = int((force_height / orig_height) * orig_width)
            if width % 2 != 0:
                width += 1
            height = force_height
            
            path_hash = hashlib.md5(video_path.encode('utf-8')).hexdigest()[:8]
            base_name = os.path.basename(video_path)
            name, ext = os.path.splitext(base_name)
            temp_filename = f"{name}_{path_hash}_{height}p.mp4"
            temp_path = os.path.join(folder_paths.get_temp_directory(), temp_filename)
            
            if not os.path.exists(temp_path):
                print(f"DeepGen: Resizing video to {width}x{height} using cv2...")
                try:
                    cap_in = cv2.VideoCapture(video_path)
                    fps = cap_in.get(cv2.CAP_PROP_FPS)
                    if fps == 0 or fps != fps:
                        fps = 25.0
                    
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
                    
                    while True:
                        ret, frame = cap_in.read()
                        if not ret:
                            break
                        resized_frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
                        out.write(resized_frame)
                        
                    cap_in.release()
                    out.release()
                except Exception as e:
                    print(f"DeepGen: Failed to resize video using cv2: {e}")
                    temp_path = video_path
                    width = orig_width
                    height = orig_height
            
            video_path = temp_path
            
        mock_video = ComfyVideoMock(video_path, width, height)
        
        description, dialogues, assets = get_xmp_metadata(orig_video_path)
        
        return (mock_video, description, dialogues, assets)
