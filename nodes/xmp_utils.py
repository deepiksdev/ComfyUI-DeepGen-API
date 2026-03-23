import subprocess
import json
import logging
import shutil
import os

def get_exiftool_path():
    path = shutil.which('exiftool')
    if path:
        return path
        
    # Mac GUI apps often don't inherit the user shell PATH, check common locations
    for fallback in ['/opt/homebrew/bin/exiftool', '/usr/local/bin/exiftool']:
        if os.path.exists(fallback):
            return fallback
            
    return 'exiftool'

def get_xmp_metadata(filepath):
    """
    Extracts 'Description', 'Dialogues', and 'Assets' from XMP metadata using exiftool.
    Returns a tuple of three UI strings: (description, dialogues, assets)
    """
    try:
        exiftool_bin = get_exiftool_path()
        
        # Run exiftool and parse output as JSON
        result = subprocess.run(
            [exiftool_bin, '-j', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        output = json.loads(result.stdout)
        if not output:
            print(f"[DeepGen XMP] No EXIF/XMP output returned for {filepath}")
            return ("", "", "")
            
        data = output[0]
        print(f"[DeepGen XMP] EXIF/XMP dict for {filepath}:")
        print(json.dumps(data, indent=2))
        
        # Helper to do flexible key matching in case keys are prefixed (e.g. XMP:Description)
        def get_field(data_dict, exact_key, suffix):
            if exact_key in data_dict:
                val = data_dict[exact_key]
            else:
                # Fallback fuzzy match (case-insensitive)
                suffix_lower = suffix.lower()
                val = next((v for k, v in data_dict.items() if k.lower().endswith(suffix_lower)), "")
                
            # If the value is a list (e.g. multiple Assets), join with commas
            if isinstance(val, list):
                return ", ".join(str(item) for item in val)
            
            return str(val) if val is not None else ""

        description = get_field(data, 'Description', 'Description')
        dialogues = get_field(data, 'Dialogues', 'Dialogues')
        assets = get_field(data, 'Assets', 'Assets')
        
        print(f"[DeepGen XMP] Extracted Description: {description}")
        print(f"[DeepGen XMP] Extracted Dialogues: {dialogues}")
        print(f"[DeepGen XMP] Extracted Assets: {assets}")
        
        return description, dialogues, assets

    except FileNotFoundError:
        logging.warning("exiftool not found. Please assure it is installed to read XMP metadata.")
        return ("", "", "")
    except subprocess.CalledProcessError as e:
        logging.warning(f"Error reading XMP metadata from {filepath} via exiftool: {e.stderr}")
        return ("", "", "")
    except json.JSONDecodeError:
        logging.warning(f"Failed to parse exiftool JSON output for {filepath}.")
        return ("", "", "")
    except Exception as e:
        logging.warning(f"Unexpected error getting XMP metadata for {filepath}: {e}")
        return ("", "", "")
