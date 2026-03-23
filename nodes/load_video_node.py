import os
import folder_paths

from .base_media_loader import BaseMediaLoaderNode

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
                    "video": (sorted(video_files), {"video_upload": True})
                    }
                }

    CATEGORY = "DeepGen/Loaders"
    RETURN_TYPES = ("VIDEO",)
    FUNCTION = "load_video"

    def load_video(self, video):
        video_path = folder_paths.get_annotated_filepath(video)
        
        # Determine a dummy width/height. In a real scenario, you'd probe the video (e.g., using ffprobe or cv2)
        # However, for consistency with ComfyVideoMock and without extra dependencies, we default.
        width = 512
        height = 512
        
        mock_video = ComfyVideoMock(video_path, width, height)
        return (mock_video,)
