import importlib
import logging

from .nodes import api_routes
from .nodes.t2t_node import T2TNode
from .nodes.i2t_node import I2TNode
from .nodes.t2i_node import T2INode
from .nodes.i2i_node import I2INode
from .nodes.i2i3_node import I2I3Node
from .nodes.i2i10_node import I2I10Node
from .nodes.t2v_node import T2VNode
from .nodes.i2v_node import I2VNode
from .nodes.i2v2_node import I2V2Node
from .nodes.i2vr_node import I2VRNode
from .nodes.v2v_node import V2VNode
from .nodes.v2vr_node import V2VRNode
from .nodes.display_node import NODE_CLASS_MAPPINGS as DISPLAY_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as DISPLAY_NAMES
from .nodes.video_to_image_node import NODE_CLASS_MAPPINGS as VTI_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as VTI_NAMES

# Node order here controls display order in ComfyUI
NODE_CLASS_MAPPINGS = {
    "DeepGen_T2I": T2INode,
    "DeepGen_I2I": I2INode,
    "DeepGen_I2I3": I2I3Node,
    "DeepGen_I2I10": I2I10Node,
    "DeepGen_T2V": T2VNode,
    "DeepGen_I2V": I2VNode,
    "DeepGen_I2V2": I2V2Node,
    "DeepGen_I2VR": I2VRNode,
    "DeepGen_V2V": V2VNode,
    "DeepGen_V2VR": V2VRNode,
    "DeepGen_T2T": T2TNode,
    "DeepGen_I2T": I2TNode,
    **DISPLAY_MAPPINGS,
    **VTI_MAPPINGS,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepGen_T2T": "Invoke LLM",
    "DeepGen_I2T": "Review Images",
    "DeepGen_T2I": "Generate Image (from Text)",
    "DeepGen_I2I": "Edit Image",
    "DeepGen_I2I3": "Generate Image (from 3 Images)",
    "DeepGen_I2I10": "Generate Image (from 10 Images)",
    "DeepGen_T2V": "Generate Video (from Text)",
    "DeepGen_I2V": "Generate Video (from Start Frame)",
    "DeepGen_I2V2": "Generate Video (from Start and End Frames)",
    "DeepGen_I2VR": "Generate Video (from Images with Elements)",
    "DeepGen_V2V": "Edit Video",
    "DeepGen_V2VR": "Edit Video (with Elements)",
    **DISPLAY_NAMES,
    **VTI_NAMES,
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
