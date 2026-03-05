import { app } from "../../scripts/app.js";

// Keep a cached configuration from the backend
let modelsConfig = null;

async function fetchModelsConfig() {
    if (modelsConfig) return modelsConfig;
    try {
        const response = await fetch("/deepgen/models");
        const data = await response.json();
        modelsConfig = data.models || [];
        return modelsConfig;
    } catch (e) {
        console.error("DeepGen: Event listener failed to fetch model configs.", e);
        return [];
    }
}

function manageDynamicChoiceWidget(node, widgetName, optionsList) {
    if (!node.widgets) return;
    if (!node._hiddenWidgets) node._hiddenWidgets = {};

    let widget = node.widgets.find(w => w.name === widgetName);

    // If it's a converted widget, it's typically an input socket now, so we skip modifying it visually
    if (widget && widget.type === "converted-widget") return;

    if (optionsList && optionsList.length > 0) {
        // Show and update
        if (!widget) {
            widget = node._hiddenWidgets[widgetName];
            if (widget) {
                // Re-add hidden widget (for backward compatibility if it was spliced)
                node.widgets.push(widget);
                delete node._hiddenWidgets[widgetName];
            }
        }
        if (widget) {
            // Restore visibility if it was hidden visually
            if (widget.type === "hidden") {
                widget.type = widget.origType || "COMBO";
                if (widget.origComputeSize) {
                    widget.computeSize = widget.origComputeSize;
                } else {
                    delete widget.computeSize;
                }
            }
            widget.options.values = optionsList;
            if (!optionsList.includes(widget.value)) {
                widget.value = optionsList[0];
            }
        }
    } else {
        // Hide visually without removing from widget array to prevent saved value index shifting
        if (widget && widget.type !== "hidden") {
            widget.origType = widget.type;
            widget.origComputeSize = widget.computeSize;
            widget.type = "hidden";
            // A height of -4 combined with hidden type makes LiteGraph effectively ignore its layout space
            widget.computeSize = () => [0, -4];
        }
    }
}

function manageOptionalWidgetVisually(node, widgetName, isSupported) {
    if (!node.widgets) return;
    let widget = node.widgets.find(w => w.name === widgetName);
    if (!widget) return;

    // Ignore converted widgets as they are sockets now
    if (widget.type === "converted-widget") return;

    if (isSupported) {
        if (widget.type === "hidden") {
            widget.type = widget.origType || "customtype";
            if (widget.origComputeSize) {
                widget.computeSize = widget.origComputeSize;
            } else {
                delete widget.computeSize;
            }
        }
        if (widget.inputEl) {
            widget.inputEl.style.display = "";
            if (widget.inputEl.parentNode) {
                widget.inputEl.parentNode.style.display = "";
            }
        } else if (widget.element) {
            widget.element.style.display = "";
        }
    } else {
        if (widget.type !== "hidden") {
            widget.origType = widget.type;
            widget.origComputeSize = widget.computeSize;
            widget.type = "hidden";
            widget.computeSize = () => [0, -4];
        }
        if (widget.inputEl) {
            widget.inputEl.style.display = "none";
            if (widget.inputEl.parentNode && widget.inputEl.parentNode.classList && widget.inputEl.parentNode.classList.contains("comfy-multiline-input")) {
                widget.inputEl.parentNode.style.display = "none";
            }
        } else if (widget.element) {
            widget.element.style.display = "none";
        }
    }
}

app.registerExtension({
    name: "DeepGen.DynamicImageSockets",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (["Image_deepgen", "LLM_deepgen", "Video_deepgen"].includes(nodeData.name)) {
            // Intercept node configure to rebuild saved JSON inputs synchronously
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (info) {
                if (info && info.inputs) {
                    // Synchronously add image sockets saved in the JSON so ComfyUI links match
                    for (const input of info.inputs) {
                        if ((input.name.startsWith("image_") && input.type === "IMAGE") || (input.name.startsWith("video_") && input.type === "VIDEO") || (input.name.startsWith("element_") && input.type === "IMAGE") || (input.name.startsWith("frame_") && input.type === "IMAGE")) {
                            const exists = this.inputs && this.inputs.find(inp => inp.name === input.name);
                            if (!exists) {
                                this.addInput(input.name, input.type);
                            }
                        }
                    }
                }
                if (onConfigure) {
                    return onConfigure.apply(this, arguments);
                }
            };

            // Intercept node creation
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                this._deepgen_update_sockets = async () => {
                    const node = this;
                    const configs = await fetchModelsConfig();

                    // Find the model widget
                    const modelWidget = node.widgets?.find(w => w.name === "model");
                    if (!modelWidget || !configs.length) return;

                    let selectedModelName = modelWidget.value;
                    if (Array.isArray(selectedModelName) || !selectedModelName) {
                        if (modelWidget.options && modelWidget.options.values && modelWidget.options.values.length > 0) {
                            selectedModelName = modelWidget.options.values[0];
                            modelWidget.value = selectedModelName; // Force initialize
                        }
                    }

                    const modelConfig = configs.find(c => c.name === selectedModelName);
                    const targetImages = modelConfig ? (modelConfig.nb_of_images || 0) : 1;
                    const targetVideos = modelConfig ? (modelConfig.nb_of_videos || 0) : 0;
                    const targetElements = modelConfig ? (modelConfig.nb_of_elements || 0) : 0;
                    const targetFrames = modelConfig ? (modelConfig.nb_of_frames || 0) : 0;
                    const supportedInputs = modelConfig ? (modelConfig.optional_inputs || []) : [];

                    // Handle dynamic choice widgets (aspect_ratio, resolution, pixel_size)
                    // If they are explicitly in the dynamic lists, we update options, but also only show if supported
                    const hasAspectRatios = modelConfig && modelConfig.aspect_ratios && modelConfig.aspect_ratios.length > 0;
                    const hasResolutions = modelConfig && modelConfig.resolutions && modelConfig.resolutions.length > 0;
                    const hasPixelSizes = modelConfig && modelConfig.pixel_sizes && modelConfig.pixel_sizes.length > 0;

                    manageDynamicChoiceWidget(node, "aspect_ratio", supportedInputs.includes("aspect_ratio") ? modelConfig.aspect_ratios : []);
                    manageDynamicChoiceWidget(node, "resolution", supportedInputs.includes("resolution") ? modelConfig.resolutions : []);
                    manageDynamicChoiceWidget(node, "pixel_size", supportedInputs.includes("pixel_size") ? modelConfig.pixel_sizes : []);

                    // General optional inputs handling
                    const allOptionalInputs = [
                        "temperature", "cfg_scale", "steps", "loras", "negative_prompt",
                        "style", "queue", "duration", "generate_audio", "shot_type",
                        "auto_fix", "enable_safety_checker", "safety_tolerance",
                        "transparent_background", "partial_images", "quality", "loop"
                    ];

                    for (const optInput of allOptionalInputs) {
                        manageOptionalWidgetVisually(node, optInput, supportedInputs.includes(optInput));
                    }

                    if (!node.inputs) return;

                    // 1. Remove any image_X or video_X sockets that are beyond the target amount
                    // We iterate backwards to safely remove inputs
                    for (let i = node.inputs.length - 1; i >= 0; i--) {
                        if (node.inputs[i].name.startsWith("image_")) {
                            const match = node.inputs[i].name.match(/image_(\d+)/);
                            if (match) {
                                const idx = parseInt(match[1]);
                                if (idx > targetImages) {
                                    node.removeInput(i);
                                }
                            }
                        } else if (node.inputs[i].name.startsWith("video_")) {
                            const match = node.inputs[i].name.match(/video_(\d+)/);
                            if (match) {
                                const idx = parseInt(match[1]);
                                if (idx > targetVideos) {
                                    node.removeInput(i);
                                }
                            }
                        } else if (node.inputs[i].name.startsWith("element_")) {
                            const match = node.inputs[i].name.match(/element_(\d+)(.*)/);
                            if (match) {
                                const idx = parseInt(match[1]);
                                const suffix = match[2];
                                const validSuffixes = ["_frontal", "_ref_1", "_ref_2", "_ref_3"];
                                if (idx > targetElements || !validSuffixes.includes(suffix)) {
                                    node.removeInput(i);
                                }
                            }
                        } else if (node.inputs[i].name.startsWith("frame_")) {
                            const match = node.inputs[i].name.match(/frame_(\d+)/);
                            if (match) {
                                const idx = parseInt(match[1]);
                                if (idx > targetFrames) {
                                    node.removeInput(i);
                                }
                            }
                        }
                    }

                    // 2. Add any missing image_X sockets up to target amount
                    for (let i = 1; i <= targetImages; i++) {
                        const socketName = `image_${i}`;
                        const exists = node.inputs.find(inp => inp.name === socketName);
                        if (!exists) {
                            node.addInput(socketName, "IMAGE");
                        }
                    }

                    // 3. Add any missing video_X sockets up to target amount
                    for (let i = 1; i <= targetVideos; i++) {
                        const socketName = `video_${i}`;
                        const exists = node.inputs.find(inp => inp.name === socketName);
                        if (!exists) {
                            node.addInput(socketName, "VIDEO");
                        }
                    }

                    // 4. Add any missing element_X sockets up to target amount
                    for (let i = 1; i <= targetElements; i++) {
                        const suffixes = ["frontal", "ref_1", "ref_2", "ref_3"];
                        for (const suffix of suffixes) {
                            const socketName = `element_${i}_${suffix}`;
                            const exists = node.inputs.find(inp => inp.name === socketName);
                            if (!exists) {
                                node.addInput(socketName, "IMAGE");
                            }
                        }
                    }

                    // 5. Add any missing frame_X sockets up to target amount
                    for (let i = 1; i <= targetFrames; i++) {
                        const socketName = `frame_${i}`;
                        const exists = node.inputs.find(inp => inp.name === socketName);
                        if (!exists) {
                            node.addInput(socketName, "IMAGE");
                        }
                    }

                    // Force a UI redraw
                    if (node.computeSize) {
                        const sz = node.computeSize();
                        // ensure min height for DOM elements properly layouting
                        if (sz[1] < 60) sz[1] = 60;
                        node.setSize(sz);
                    }
                    if (app.graph) {
                        app.graph.setDirtyCanvas(true, true);
                    }
                };

                // Add properties to the widget to detect change
                setTimeout(() => {
                    const modelWidget = this.widgets?.find(w => w.name === "model");
                    if (modelWidget) {
                        // Hook the callback when the widget value changes
                        const callback = modelWidget.callback;
                        modelWidget.callback = (value) => {
                            if (callback) {
                                callback.call(modelWidget, value);
                            }
                            this._deepgen_update_sockets();
                        };

                        // Initial updates based on default value
                        this._deepgen_update_sockets();

                        // Fallback delays for asynchronously rendered ComfyUI DOM widgets (e.g. textareas)
                        setTimeout(() => this._deepgen_update_sockets(), 500);
                        setTimeout(() => this._deepgen_update_sockets(), 1000);
                    }
                }, 100);

                return r;
            };

            const onAdded = nodeType.prototype.onAdded;
            nodeType.prototype.onAdded = function () {
                if (onAdded) {
                    onAdded.apply(this, arguments);
                }
                if (this._deepgen_update_sockets) {
                    setTimeout(() => this._deepgen_update_sockets(), 50);
                }
            };
        }
    }
});
