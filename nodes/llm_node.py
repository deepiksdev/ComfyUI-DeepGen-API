from .deepgen_utils import DeepGenApiHandler, DeepGenConfig, ImageUtils, ResultProcessor
import os
import csv

# Initialize DeepGenConfig
deepgen_config = DeepGenConfig()


class LLMNode:
    # Base INPUT_TYPES left blank as this will be a dynamically generated subclass.
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}, "optional": {}}

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        """Bypass standard ComfyUI validation for dynamic combo boxes"""
        return True

    RETURN_TYPES = ("STRING", "STRING", "FLOAT",)
    RETURN_NAMES = ("output", "output_prefix_and_model", "total_credits_used",)
    FUNCTION = "generate_text"
    CATEGORY = "DeepGen/LLM"

    def generate_text(self, prompt, seed_value=-1, endpoint="https://api.deepgen.app", output_prefix="", **kwargs):
        try:
            alias_id = getattr(self, "alias_id", "gemini-3-flash")
            
            image_urls = []
            attachments_files = []
            for k, v in kwargs.items():
                if v is None:
                    continue
                if k in ["model", "prompt", "seed_value", "endpoint", "output_prefix"]:
                    continue

                if k.startswith("element_") and isinstance(v, dict):
                    for elem_key, elem_val in v.items():
                        if elem_val is None:
                            continue
                        
                        vid_path = None
                        if isinstance(elem_val, str):
                            try:
                                if os.path.exists(elem_val):
                                    vid_path = elem_val
                            except Exception:
                                pass
                        elif hasattr(elem_val, "filepath") and elem_val.filepath:
                            try:
                                if os.path.exists(elem_val.filepath):
                                    vid_path = elem_val.filepath
                            except Exception:
                                pass
                        
                        prefix = f"{k}_{elem_key}"
                        
                        if vid_path:
                            import base64
                            import mimetypes
                            import os as os_mod
                            mime_type, _ = mimetypes.guess_type(vid_path)
                            mime_type = mime_type or "application/octet-stream"
                            original_name = os_mod.basename(vid_path)
                            new_filename = f"{prefix}___{original_name}"
                            with open(vid_path, "rb") as vf:
                                b64 = base64.b64encode(vf.read()).decode("utf-8")
                                attachments_files.append({
                                    "attachment_bytes": b64,
                                    "attachment_mime_type": mime_type,
                                    "attachment_file_name": new_filename
                                })
                            continue
                        
                        if hasattr(elem_val, "shape"):
                            img = elem_val
                            if len(img.shape) == 4:
                                for i in range(img.shape[0]):
                                    single_image = img[i:i+1]
                                    attach = ImageUtils.get_attachment_file(single_image, filename=f"{prefix}___{i}.png")
                                    if attach:
                                        attachments_files.append(attach)
                            else:
                                attach = ImageUtils.get_attachment_file(img, filename=f"{prefix}___image.png")
                                if attach:
                                    attachments_files.append(attach)
                    continue

                vid_path = None
                if isinstance(v, str):
                    try:
                        if os.path.exists(v):
                            vid_path = v
                    except Exception:
                        pass
                elif hasattr(v, "filepath") and v.filepath:
                    try:
                        if os.path.exists(v.filepath):
                            vid_path = v.filepath
                    except Exception:
                        pass
                
                if vid_path:
                    import base64
                    import mimetypes
                    import os as os_mod
                    mime_type, _ = mimetypes.guess_type(vid_path)
                    mime_type = mime_type or "application/octet-stream"
                    original_name = os_mod.basename(vid_path)
                    new_filename = f"{k}__{original_name}"
                    with open(vid_path, "rb") as vf:
                        b64 = base64.b64encode(vf.read()).decode("utf-8")
                        attachments_files.append({
                            "attachment_bytes": b64,
                            "attachment_mime_type": mime_type,
                            "attachment_file_name": new_filename
                        })
                    continue
                
                if hasattr(v, "shape"):
                    img = v
                    if len(img.shape) == 4:
                        for i in range(img.shape[0]):
                            single_image = img[i:i+1]
                            attach = ImageUtils.get_attachment_file(single_image, filename=f"{k}__{i}.png")
                            if attach:
                                attachments_files.append(attach)
                    else:
                        attach = ImageUtils.get_attachment_file(img, filename=f"{k}__image.png")
                        if attach:
                            attachments_files.append(attach)
            
            arguments = {
                "prompt": prompt,
                "stream": False,
            }
            if seed_value != -1:
                arguments["seed"] = seed_value

            if image_urls:
                arguments["attachments_urls"] = image_urls
            if attachments_files:
                arguments["attachments_files"] = attachments_files

            result = DeepGenApiHandler.submit_and_get_result(alias_id, arguments, api_url=endpoint)
            
            res_obj = result[0] if isinstance(result, list) and len(result) > 0 else result
            text_result = ResultProcessor.process_text_result(result)
            
            def _get_attr(obj, key, default=None):
                if isinstance(obj, dict): return obj.get(key, default)
                return getattr(obj, key, default)
                
            agent_alias = _get_attr(res_obj, "agent_alias", "")
            prefixed_model = f"{output_prefix}_{agent_alias}" if output_prefix else agent_alias
            
            cred = _get_attr(res_obj, "total_credits_used")
            if cred is None:
                out_obj = _get_attr(res_obj, "output", {})
                cred = _get_attr(out_obj, "total_credits_used", _get_attr(res_obj, "aiCredits", 0.0))
            credits_out = float(cred or 0.0)
            return (text_result[0], prefixed_model, credits_out)
        except ValueError as ve:
            raise ve
        except Exception as e:
            error_result = DeepGenApiHandler.handle_text_generation_error(alias_id, str(e))
            return (error_result[0], "", 0.0)



