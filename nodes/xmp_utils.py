import logging
import mmap
import os
import xml.etree.ElementTree as ET

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
            
        # Use mmap for memory-efficient searching (fast even for huge video files)
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
