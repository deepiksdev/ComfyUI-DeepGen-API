import logging
import mmap
import os
import xml.etree.ElementTree as ET
from PIL import Image

def get_xmp_metadata(filepath):
    """
    Extracts 'Description', 'Dialogues', and 'Assets' from XMP metadata natively.
    Returns a tuple of three UI strings: (description, dialogues, assets)
    """
    try:
        if not os.path.exists(filepath):
            return ("", "", "")
            
        # Get file size to avoid mmap on empty files
        size = os.path.getsize(filepath)
        if size == 0:
            return ("", "", "")
            
        description = ""
        dialogues = ""
        assets_str = ""
        
        # 1. Try reading metadata natively for Supported Images (like PNG tEXt chunks) using PIL
        try:
            with Image.open(filepath) as img:
                info = img.info or {}
                # Some objects might have getxmp() if it's a JPEG or TIFF with XMP
                xmp_dict = img.getxmp() if hasattr(img, 'getxmp') else {}
                
                # Case-insensitive recursive dictionary search
                def find_key(d, tgt):
                    tgt_low = tgt.lower()
                    for k, v in d.items():
                        if k.lower() == tgt_low or k.lower().endswith(":" + tgt_low):
                            return v
                        if isinstance(v, dict):
                            res = find_key(v, tgt)
                            if res is not None: return res
                    return None
                
                desc_match = find_key(info, 'Description') or find_key(xmp_dict, 'Description')
                dial_match = find_key(info, 'Dialogues') or find_key(xmp_dict, 'Dialogues')
                asset_match = find_key(info, 'Assets') or find_key(xmp_dict, 'Assets')
                
                if desc_match: description = str(desc_match)
                if dial_match: dialogues = str(dial_match)
                if asset_match:
                    if isinstance(asset_match, list): assets_str = ", ".join(str(a) for a in asset_match)
                    else: assets_str = str(asset_match)
                    
                if description or dialogues or assets_str:
                    print(f"[DeepGen XMP] Found native Image metadata: Desc='{description}', Dial='{dialogues}', Assets='{assets_str}'")
                    return description, dialogues, assets_str
        except Exception as e:
            # Not an image or PIL failed, fall through to binary XML search
            pass
            
        # 2. Use mmap for memory-efficient searching (fast for video files or JPGs hiding raw XMP packets)
        with open(filepath, 'rb') as f:
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                start = mm.find(b'<x:xmpmeta')
                if start == -1:
                    start = mm.find(b'<xmpmeta')
                    
                if start == -1:
                    print(f"[DeepGen XMP] No XMP block found in {filepath}")
                    return ("", "", "")
                    
                end = mm.find(b'</x:xmpmeta>', start)
                tail_len = len(b'</x:xmpmeta>')
                if end == -1:
                    end = mm.find(b'</xmpmeta>', start)
                    tail_len = len(b'</xmpmeta>')
                    
                if end == -1:
                    print(f"[DeepGen XMP] Truncated XMP block in {filepath}")
                    return ("", "", "")
                    
                xmp_xml = mm[start:end+tail_len].decode('utf-8', errors='ignore')
                
        # Parse XML natively
        description = ""
        dialogues = ""
        assets = []
        
        root = ET.fromstring(xmp_xml)
        for elem in root.iter():
            tag = elem.tag.split('}')[1].lower() if '}' in elem.tag else elem.tag.lower()
            
            if tag == 'description' and elem.text and elem.text.strip():
                if len(elem) == 0:
                    description = elem.text.strip()
            elif tag == 'dialogues' and elem.text and elem.text.strip():
                if len(elem) == 0:
                    dialogues = elem.text.strip()
            elif tag == 'assets':
                for child in elem.iter():
                    child_tag = child.tag.split('}')[1].lower() if '}' in child.tag else child.tag.lower()
                    if child_tag == 'li' and child.text and child.text.strip():
                        if child.text.strip() not in assets:
                            assets.append(child.text.strip())
                            
        assets_str = ", ".join(assets)
        
        print(f"[DeepGen XMP] Extracted Description: {description}")
        print(f"[DeepGen XMP] Extracted Dialogues: {dialogues}")
        print(f"[DeepGen XMP] Extracted Assets: {assets_str}")
        
        return description, dialogues, assets_str

    except Exception as e:
        print(f"[DeepGen XMP] Error extracting XMP natively from {filepath}: {e}")
        return ("", "", "")
