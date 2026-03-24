import os
import torch
import numpy as np
from PIL import Image, ImageOps

import folder_paths
from .base_media_loader import BaseMediaLoaderNode
from .xmp_utils import get_xmp_metadata

class LoadImageNode(BaseMediaLoaderNode):
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        # Filter for common image extensions
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']
        image_files = [f for f in files if any(f.lower().endswith(ext) for ext in image_extensions)]
        
        return {"required": {
                    "image": (sorted(image_files), {"image_upload": True}),
                    "force_height": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 8})
                    }
                }

    CATEGORY = "DeepGen/Loaders"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "description", "dialogues", "assets")
    FUNCTION = "load_image"

    def load_image(self, image, force_height=0):
        image_path = folder_paths.get_annotated_filepath(image)
        
        # Load image via PIL
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        
        # Resize if force_height is provided
        if force_height > 0 and img.height != force_height:
            new_width = int((force_height / img.height) * img.width)
            img = img.resize((new_width, force_height), Image.LANCZOS)
        
        # Convert based on mode
        if img.mode == 'I':
            img = img.point(lambda i: i * (1 / 255))
        img = img.convert("RGB")
        
        # Normalize and convert to tensor
        image_np = np.array(img).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]
        
        # Mask handling (if image has alpha)
        if 'A' in img.getbands():
            mask = np.array(img.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - mask
        else:
            mask = np.zeros((img.height, img.width), dtype=np.float32)
            
        mask_tensor = torch.from_numpy(mask).unsqueeze(0)
        
        description, dialogues, assets = get_xmp_metadata(image_path)
        
        return (image_tensor, mask_tensor, description, dialogues, assets)
