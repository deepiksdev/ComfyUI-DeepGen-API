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
                    const btnWidget = {
                        type: "button_group",
                        name: "Browse Videos",
                        draw: function (ctx, node, widget_width, y, widget_height) {
                            const btnWidth = (widget_width / 2) - 4;
                            
                            const values = videoWidget?.options?.values || [];
                            const index = values.indexOf(videoWidget?.value);
                            const can_prev = index > 0;
                            const can_next = index !== -1 && index < values.length - 1;
                            
                            this.can_prev = can_prev;
                            this.can_next = can_next;
                            
                            // Draw Previous Background
                            ctx.fillStyle = can_prev ? "#3a3a3a" : "#1a1a1a";
                            ctx.beginPath();
                            ctx.roundRect(0, y, btnWidth, widget_height, 4);
                            ctx.fill();
                            
                            // Draw Next Background
                            ctx.fillStyle = can_next ? "#3a3a3a" : "#1a1a1a";
                            ctx.beginPath();
                            ctx.roundRect(widget_width - btnWidth, y, btnWidth, widget_height, 4);
                            ctx.fill();
                            
                            // Draw Text
                            ctx.font = "14px Arial";
                            ctx.textAlign = "center";
                            ctx.textBaseline = "middle";
                            const textY = y + widget_height / 2;
                            
                            ctx.fillStyle = can_prev ? "#ffffff" : "#666666";
                            ctx.fillText("< Prev", btnWidth / 2, textY);
                            
                            ctx.fillStyle = can_next ? "#ffffff" : "#666666";
                            ctx.fillText("Next >", widget_width - btnWidth / 2, textY);
                        },
                        mouse: function (event, pos, node) {
                            if (event.type === "down" || event.type === "mousedown" || event.type === "pointerdown") {
                                const widget_width = node.size[0];
                                // Give buttons a little spacing from the center
                                const btnWidth = (widget_width / 2) - 4;
                                
                                const x = pos[0];
                                
                                const values = videoWidget?.options?.values || [];
                                const index = values.indexOf(videoWidget?.value);
                                
                                // Re-evaluate logic instead of strictly relying on this.can_prev
                                const can_prev = index > 0;
                                const can_next = index !== -1 && index < values.length - 1;
                                
                                if (x < btnWidth && can_prev) {
                                    videoWidget.value = values[index - 1];
                                    if (videoWidget.callback) videoWidget.callback(videoWidget.value, app, node);
                                    app.graph.setDirtyCanvas(true);
                                    return true;
                                } else if (x > widget_width - btnWidth && can_next) {
                                    videoWidget.value = values[index + 1];
                                    if (videoWidget.callback) videoWidget.callback(videoWidget.value, app, node);
                                    app.graph.setDirtyCanvas(true);
                                    return true;
                                }
                            }
                            return false;
                        },
                        computeSize: function (width) {
                            return [width, LiteGraph.NODE_WIDGET_HEIGHT]; // typically 20 or 24
                        }
                    };
                    
                    // ComfyUI / LiteGraph extension: push the widget or use addCustomWidget
                    if (this.addCustomWidget) {
                        this.addCustomWidget(btnWidget);
                    } else {
                        this.widgets.push(btnWidget);
                    }
                }

                return r;
            };
        }
    },
});
