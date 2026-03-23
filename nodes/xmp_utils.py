import subprocess
import json
import logging

def get_xmp_metadata(filepath):
    """
    Extracts 'Description', 'Dialogues', and 'Assets' from XMP metadata using exiftool.
    Returns a tuple of three UI strings: (description, dialogues, assets)
    """
    try:
        # Run exiftool and parse output as JSON
        result = subprocess.run(
            ['exiftool', '-j', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        output = json.loads(result.stdout)
        if not output:
            return ("", "", "")
            
        data = output[0]
        
        # Helper to do flexible key matching in case keys are prefixed (e.g. XMP:Description)
        def get_field(data_dict, exact_key, suffix):
            if exact_key in data_dict:
                val = data_dict[exact_key]
            else:
                # Fallback fuzzy match
                val = next((v for k, v in data_dict.items() if k.endswith(suffix)), "")
                
            # If the value is a list (e.g. multiple Assets), join with commas
            if isinstance(val, list):
                return ", ".join(str(item) for item in val)
            
            return str(val) if val is not None else ""

        description = get_field(data, 'Description', 'Description')
        dialogues = get_field(data, 'Dialogues', 'Dialogues')
        assets = get_field(data, 'Assets', 'Assets')
        
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
