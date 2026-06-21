class CanvasRenderer {
    constructor(container, layerManager, commandHistory) {
        this.container = container;
        this.layerManager = layerManager;
        this.commandHistory = commandHistory;
        
        this.width = layerManager.width;
        this.height = layerManager.height;
        
        this.displayCanvas = document.createElement('canvas');
        this.displayCanvas.width = this.width;
        this.displayCanvas.height = this.height;
        this.displayCtx = this.displayCanvas.getContext('2d');
        
        this.previewCanvas = document.createElement('canvas');
        this.previewCanvas.width = this.width;
        this.previewCanvas.height = this.height;
        this.previewCtx = this.previewCanvas.getContext('2d');
        
        const existingCursorLayer = this.container.querySelector('#cursorLayer');
        this.container.innerHTML = '';
        this.container.appendChild(this.displayCanvas);
        this.container.appendChild(this.previewCanvas);
        if (existingCursorLayer) {
            this.container.appendChild(existingCursorLayer);
        }
        
        this.currentTool = 'pen';
        this.color = '#000000';
        this.lineWidth = 3;
        this.fillColor = null;
        this.fontSize = 24;
        
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.points = [];
        
        this.onCommandCallback = null;
        this.onCursorMoveCallback = null;
        
        this.userId = null;
        this.userName = null;
        
        this.currentTemplate = null;
        
        this._bindStyle();
        this._bindEvents();
        this._setupLayerListener();
        this.render();
    }
    
    _bindStyle() {
        this.displayCanvas.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            cursor: crosshair;
        `;
        this.previewCanvas.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
        `;
        this.container.style.cssText = `
            position: relative;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        `;
    }
    
    applyTemplate(template) {
        if (!template) return;
        this.currentTemplate = template;
        const config = template.config;
        
        this._applyTemplateBackground(template);
        
        if (template.type === 'mindmap') {
            this._applyMindmapNodes(config);
        }
    }
    
    _applyTemplateBackground(template) {
        const config = template.config;
        const bgColor = config.backgroundColor || '#ffffff';
        
        switch (template.type) {
            case 'whiteboard':
                this.container.style.backgroundColor = bgColor;
                this.container.style.backgroundImage = 'none';
                break;
                
            case 'grid':
                const gridColor = config.gridColor || '#e2e8f0';
                const gridSize = config.gridSize || 20;
                this.container.style.backgroundColor = bgColor;
                this.container.style.backgroundImage = `
                    linear-gradient(${gridColor} 1px, transparent 1px),
                    linear-gradient(90deg, ${gridColor} 1px, transparent 1px)
                `;
                this.container.style.backgroundSize = `${gridSize}px ${gridSize}px`;
                this.container.style.backgroundPosition = '0 0';
                break;
                
            case 'mindmap':
                this.container.style.backgroundColor = bgColor;
                this.container.style.backgroundImage = 'none';
                break;
                
            default:
                this.container.style.backgroundColor = bgColor;
                this.container.style.backgroundImage = 'none';
        }
    }
    
    _applyMindmapNodes(config) {
        const currentLayer = this.layerManager.getCurrentLayer();
        if (!currentLayer) return;
        
        const ctx = currentLayer.canvas.getContext('2d');
        
        if (config.centerNode) {
            const node = config.centerNode;
            this._drawMindmapNode(ctx, node.x, node.y, node.width, node.height, 
                node.text, node.fillColor, node.textColor, node.fontSize, true);
        }
        
        if (config.branches && config.centerNode) {
            const centerX = config.centerNode.x;
            const centerY = config.centerNode.y;
            
            config.branches.forEach(branch => {
                const bx = centerX + Math.cos(branch.angle) * branch.distance;
                const by = centerY + Math.sin(branch.angle) * branch.distance;
                const bw = 140;
                const bh = 50;
                
                ctx.strokeStyle = '#94a3b8';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.lineTo(bx, by);
                ctx.stroke();
                
                this._drawMindmapNode(ctx, bx, by, bw, bh,
                    branch.text, branch.fillColor, branch.textColor, branch.fontSize, false);
            });
        }
        
        this.render();
    }
    
    _drawMindmapNode(ctx, x, y, width, height, text, fillColor, textColor, fontSize, isCenter) {
        const radius = isCenter ? 16 : 10;
        ctx.fillStyle = fillColor || '#3b82f6';
        this._roundRect(ctx, x - width / 2, y - height / 2, width, height, radius);
        ctx.fill();
        
        ctx.fillStyle = textColor || '#ffffff';
        ctx.font = `bold ${fontSize || 18}px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text || '', x, y);
    }
    
    _roundRect(ctx, x, y, width, height, radius) {
        if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(x, y, width, height, radius);
            return;
        }
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }
    
    _bindEvents() {
        const canvas = this.displayCanvas;
        
        canvas.addEventListener('mousedown', (e) => this._handleMouseDown(e));
        canvas.addEventListener('mousemove', (e) => this._handleMouseMove(e));
        canvas.addEventListener('mouseup', (e) => this._handleMouseUp(e));
        canvas.addEventListener('mouseleave', (e) => this._handleMouseUp(e));
        
        canvas.addEventListener('touchstart', (e) => this._handleTouchStart(e), { passive: false });
        canvas.addEventListener('touchmove', (e) => this._handleTouchMove(e), { passive: false });
        canvas.addEventListener('touchend', (e) => this._handleTouchEnd(e), { passive: false });
        
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'z') {
                    e.preventDefault();
                    if (e.shiftKey) {
                        this.redo();
                    } else {
                        this.undo();
                    }
                } else if (e.key === 'y') {
                    e.preventDefault();
                    this.redo();
                }
            }
        });
        
        this.layerManager.setOnChangeCallback(() => {
            this.render();
        });
    }
    
    _setupLayerListener() {
        this.layerManager.setOnChangeCallback(() => {
            this.render();
        });
    }
    
    _getMousePos(e) {
        const rect = this.displayCanvas.getBoundingClientRect();
        const scaleX = this.displayCanvas.width / rect.width;
        const scaleY = this.displayCanvas.height / rect.height;
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    }
    
    _handleMouseDown(e) {
        const pos = this._getMousePos(e);
        this._startDrawing(pos.x, pos.y);
    }
    
    _handleMouseMove(e) {
        const pos = this._getMousePos(e);
        
        if (this.onCursorMoveCallback) {
            this.onCursorMoveCallback(pos.x, pos.y);
        }
        
        if (this.isDrawing) {
            this._continueDrawing(pos.x, pos.y);
        }
    }
    
    _handleMouseUp(e) {
        const pos = this._getMousePos(e);
        this._endDrawing(pos.x, pos.y);
    }
    
    _handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const pos = this._getMousePos(touch);
        this._startDrawing(pos.x, pos.y);
    }
    
    _handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const pos = this._getMousePos(touch);
        
        if (this.onCursorMoveCallback) {
            this.onCursorMoveCallback(pos.x, pos.y);
        }
        
        if (this.isDrawing) {
            this._continueDrawing(pos.x, pos.y);
        }
    }
    
    _handleTouchEnd(e) {
        e.preventDefault();
        if (e.changedTouches.length > 0) {
            const touch = e.changedTouches[0];
            const pos = this._getMousePos(touch);
            this._endDrawing(pos.x, pos.y);
        }
    }
    
    _startDrawing(x, y) {
        if (this.currentTool === 'text') {
            const text = prompt('请输入文字：');
            if (text) {
                this._executeTextCommand(x, y, text);
            }
            return;
        }
        
        this.isDrawing = true;
        this.startX = x;
        this.startY = y;
        this.currentX = x;
        this.currentY = y;
        this.points = [{ x, y }];
        
        if (this.currentTool === 'pen' || this.currentTool === 'erase') {
            this._drawPreview();
        }
    }
    
    _continueDrawing(x, y) {
        if (!this.isDrawing) return;
        
        this.currentX = x;
        this.currentY = y;
        this.points.push({ x, y });
        
        if (this.currentTool === 'pen' || this.currentTool === 'erase') {
            this._drawPreview();
        } else {
            this._drawShapePreview();
        }
    }
    
    _endDrawing(x, y) {
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        this.currentX = x;
        this.currentY = y;
        
        if (this.points.length > 0) {
            this.points.push({ x, y });
        }
        
        this._clearPreview();
        
        const command = this._createCommand();
        if (command) {
            this.executeCommand(command);
        }
        
        this.points = [];
    }
    
    _createCommand() {
        const currentLayer = this.layerManager.getCurrentLayer();
        if (!currentLayer) return null;
        
        const layerId = currentLayer.id;
        
        switch (this.currentTool) {
            case 'pen':
                if (this.points.length < 2) return null;
                return new DrawPathCommand(
                    layerId, this.userId, this.userName,
                    [...this.points], this.color, this.lineWidth
                );
            
            case 'erase':
                if (this.points.length < 2) return null;
                return new EraseCommand(
                    layerId, this.userId, this.userName,
                    [...this.points], this.lineWidth * 2
                );
            
            case 'line':
                return new DrawLineCommand(
                    layerId, this.userId, this.userName,
                    this.startX, this.startY, this.currentX, this.currentY,
                    this.color, this.lineWidth
                );
            
            case 'rect':
                return new DrawRectCommand(
                    layerId, this.userId, this.userName,
                    Math.min(this.startX, this.currentX),
                    Math.min(this.startY, this.currentY),
                    Math.abs(this.currentX - this.startX),
                    Math.abs(this.currentY - this.startY),
                    this.color, this.lineWidth, this.fillColor
                );
            
            case 'circle':
                const centerX = (this.startX + this.currentX) / 2;
                const centerY = (this.startY + this.currentY) / 2;
                const radiusX = Math.abs(this.currentX - this.startX) / 2;
                const radiusY = Math.abs(this.currentY - this.startY) / 2;
                return new DrawCircleCommand(
                    layerId, this.userId, this.userName,
                    centerX, centerY, radiusX, radiusY,
                    this.color, this.lineWidth, this.fillColor
                );
            
            default:
                return null;
        }
    }
    
    _executeTextCommand(x, y, text) {
        const currentLayer = this.layerManager.getCurrentLayer();
        if (!currentLayer) return;
        
        const command = new DrawTextCommand(
            currentLayer.id, this.userId, this.userName,
            x, y, text, this.color, this.fontSize
        );
        
        this.executeCommand(command);
    }
    
    _drawPreview() {
        this._clearPreview();
        const ctx = this.previewCtx;
        
        ctx.save();
        if (this.currentTool === 'erase') {
            ctx.globalCompositeOperation = 'destination-out';
        }
        ctx.strokeStyle = this.color;
        ctx.lineWidth = this.currentTool === 'erase' ? this.lineWidth * 2 : this.lineWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        if (this.points.length > 0) {
            ctx.moveTo(this.points[0].x, this.points[0].y);
            for (let i = 1; i < this.points.length; i++) {
                ctx.lineTo(this.points[i].x, this.points[i].y);
            }
        }
        ctx.stroke();
        ctx.restore();
    }
    
    _drawShapePreview() {
        this._clearPreview();
        const ctx = this.previewCtx;
        
        ctx.save();
        ctx.strokeStyle = this.color;
        ctx.lineWidth = this.lineWidth;
        ctx.setLineDash([5, 5]);
        
        switch (this.currentTool) {
            case 'line':
                ctx.beginPath();
                ctx.moveTo(this.startX, this.startY);
                ctx.lineTo(this.currentX, this.currentY);
                ctx.stroke();
                break;
            
            case 'rect':
                const rx = Math.min(this.startX, this.currentX);
                const ry = Math.min(this.startY, this.currentY);
                const rw = Math.abs(this.currentX - this.startX);
                const rh = Math.abs(this.currentY - this.startY);
                if (this.fillColor) {
                    ctx.fillStyle = this.fillColor;
                    ctx.fillRect(rx, ry, rw, rh);
                }
                ctx.strokeRect(rx, ry, rw, rh);
                break;
            
            case 'circle':
                const cx = (this.startX + this.currentX) / 2;
                const cy = (this.startY + this.currentY) / 2;
                const rdx = Math.abs(this.currentX - this.startX) / 2;
                const rdy = Math.abs(this.currentY - this.startY) / 2;
                ctx.beginPath();
                ctx.ellipse(cx, cy, rdx, rdy, 0, 0, Math.PI * 2);
                if (this.fillColor) {
                    ctx.fillStyle = this.fillColor;
                    ctx.fill();
                }
                ctx.stroke();
                break;
        }
        ctx.restore();
    }
    
    _clearPreview() {
        this.previewCtx.clearRect(0, 0, this.width, this.height);
    }
    
    render() {
        this.displayCtx.clearRect(0, 0, this.width, this.height);
        
        this.displayCtx.fillStyle = '#ffffff';
        this.displayCtx.fillRect(0, 0, this.width, this.height);
        
        const layers = this.layerManager.getLayers();
        for (const layer of layers) {
            if (layer.visible) {
                this.displayCtx.drawImage(layer.canvas, 0, 0);
            }
        }
    }
    
    executeCommand(command) {
        this.commandHistory.execute(command, this.layerManager);
        this.render();
        
        if (this.onCommandCallback) {
            this.onCommandCallback(command);
        }
    }
    
    executeRemoteCommand(commandData) {
        const command = BaseCommand.fromData(commandData, this.layerManager);
        this.commandHistory.executeRemote(command, this.layerManager);
        this.render();
    }
    
    undo() {
        if (!this.commandHistory.canUndo()) return null;
        const command = this.commandHistory.undo(this.layerManager);
        this.render();
        return command;
    }
    
    redo() {
        if (!this.commandHistory.canRedo()) return null;
        const command = this.commandHistory.redo(this.layerManager);
        this.render();
        return command;
    }
    
    undoToSequence(sequence) {
        this.commandHistory.undoToSequence(sequence, this.layerManager);
        this.render();
    }
    
    redoRemote(commandData) {
        const command = BaseCommand.fromData(commandData, this.layerManager);
        this.commandHistory.redo(this.layerManager);
        this.render();
    }
    
    exportToPNG() {
        const exportCanvas = document.createElement('canvas');
        exportCanvas.width = this.width;
        exportCanvas.height = this.height;
        const ctx = exportCanvas.getContext('2d');
        
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, this.width, this.height);
        
        const layers = this.layerManager.getLayers();
        for (const layer of layers) {
            if (layer.visible) {
                ctx.drawImage(layer.canvas, 0, 0);
            }
        }
        
        return exportCanvas.toDataURL('image/png');
    }
    
    setTool(tool) {
        this.currentTool = tool;
    }
    
    setColor(color) {
        this.color = color;
    }
    
    setLineWidth(width) {
        this.lineWidth = width;
    }
    
    setFillColor(color) {
        this.fillColor = color;
    }
    
    setFontSize(size) {
        this.fontSize = size;
    }
    
    setUser(userId, userName) {
        this.userId = userId;
        this.userName = userName;
    }
    
    setOnCommandCallback(callback) {
        this.onCommandCallback = callback;
    }
    
    setOnCursorMoveCallback(callback) {
        this.onCursorMoveCallback = callback;
    }
    
    resize(width, height) {
        this.width = width;
        this.height = height;
        this.displayCanvas.width = width;
        this.displayCanvas.height = height;
        this.previewCanvas.width = width;
        this.previewCanvas.height = height;
        this.layerManager.resize(width, height);
        this.render();
    }
    
    loadCommands(commandsData) {
        this.commandHistory.loadCommands(commandsData, this.layerManager);
        this.render();
    }
    
    clearAll() {
        this.layerManager.clearAll();
        this.commandHistory.clear();
        this.render();
    }
}

window.CanvasRenderer = CanvasRenderer;
