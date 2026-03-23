import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "deepgen.LoadVideoControls",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DeepGen_LVID") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const videoWidget = this.widgets.find((w) => w.name === "video");
                
                if (videoWidget) {
                    this.addWidget("button", "< Previous", "previous", () => {
                        if (videoWidget.options && videoWidget.options.values) {
                            const values = videoWidget.options.values;
                            let index = values.indexOf(videoWidget.value);
                            if (index > 0) {
                                videoWidget.value = values[index - 1];
                                if (videoWidget.callback) {
                                    videoWidget.callback(videoWidget.value);
                                }
                                app.graph.setDirtyCanvas(true);
                            }
                        }
                    });

                    this.addWidget("button", "Next >", "next", () => {
                        if (videoWidget.options && videoWidget.options.values) {
                            const values = videoWidget.options.values;
                            let index = values.indexOf(videoWidget.value);
                            if (index !== -1 && index < values.length - 1) {
                                videoWidget.value = values[index + 1];
                                if (videoWidget.callback) {
                                    videoWidget.callback(videoWidget.value);
                                }
                                app.graph.setDirtyCanvas(true);
                            }
                        }
                    });
                }

                return r;
            };
        }
    },
});
