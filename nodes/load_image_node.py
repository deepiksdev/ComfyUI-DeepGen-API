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
                    "filter": ("STRING", {"default": ""})
                    }
                }

    CATEGORY = "DeepGen/Loaders"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "description", "dialogues", "assets")
    FUNCTION = "load_image"

    def load_image(self, image, filter=""):
        image_path = folder_paths.get_annotated_filepath(image)
        
        # Load image via PIL
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        
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
