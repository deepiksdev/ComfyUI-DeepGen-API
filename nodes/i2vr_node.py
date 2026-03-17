from .task_utils import BaseTaskNode, load_models_for_task

class I2VRNode(BaseTaskNode):
    @classmethod
    def INPUT_TYPES(cls):
        models = load_models_for_task("I2VR")
        
        return {
            "required": {
                "model": (models,),
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "seed_value": ("INT", {"default": 1000}),
                "nb_results": ("INT", {"default": 1, "min": 1, "max": 10}),
                "output_prefix": ("STRING", {"default": ""}),
                "config_json": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "start_image": ("IMAGE",),
                "end_image": ("IMAGE",),
                "element_1__frontal_image": ("IMAGE",),
                "element_1__reference_image_1": ("IMAGE",),
                "element_1__video": ("VIDEO",),
                "element_2__frontal_image": ("IMAGE",),
                "element_2__reference_image_1": ("IMAGE",),
                "aspect_ratio": ("STRING", {"default": ""}),
                "resolution": ("STRING", {"default": ""}),
                "duration": ("INT", {"default": 5, "min": 1, "max": 60}),
                "generate_audio": ("BOOLEAN", {"default": True}),
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("VIDEO", "STRING", "FLOAT",)
    RETURN_NAMES = ("VIDEO", "output_prefix_and_model", "total_credits_used",)
    FUNCTION = "generate"
    CATEGORY = "DeepGen/Generators"

    def generate(self, **kwargs):
        return self.run_generation("I2VR", **kwargs)
