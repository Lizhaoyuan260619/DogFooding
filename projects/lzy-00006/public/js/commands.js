class BaseCommand {
    constructor(type, layerId, userId, userName) {
        this.type = type;
        this.layerId = layerId;
        this.userId = userId;
        this.userName = userName;
        this.id = null;
        this.sequence = null;
        this._imageData = null;
    }

    getType() {
        return this.type;
    }

    getUserId() {
        return this.userId;
    }

    getLayerId() {
        return this.layerId;
    }

    _saveImageData(ctx, x, y, width, height) {
        this._imageData = ctx.getImageData(x, y, width, height);
        this._savedX = x;
        this._savedY = y;
    }

    _restoreImageData(ctx) {
        if (this._imageData) {
            ctx.putImageData(this._imageData, this._savedX, this._savedY);
        }
    }

    execute(layerManager) {
        throw new Error('execute() must be implemented');
    }

    undo(layerManager) {
        throw new Error('undo() must be implemented');
    }

    serialize() {
        return {
            type: this.type,
            layerId: this.layerId,
            userId: this.userId,
            userName: this.userName,
            id: this.id,
            sequence: this.sequence
        };
    }

    static fromData(data, layerManager) {
        switch (data.type) {
            case 'path':
                return DrawPathCommand.fromData(data);
            case 'line':
                return DrawLineCommand.fromData(data);
            case 'rect':
                return DrawRectCommand.fromData(data);
            case 'circle':
                return DrawCircleCommand.fromData(data);
            case 'text':
                return DrawTextCommand.fromData(data);
            case 'erase':
                return EraseCommand.fromData(data);
            default:
                throw new Error(`Unknown command type: ${data.type}`);
        }
    }
}

class DrawPathCommand extends BaseCommand {
    constructor(layerId, userId, userName, points, color, lineWidth) {
        super('path', layerId, userId, userName);
        this.points = points;
        this.color = color;
        this.lineWidth = lineWidth;
    }

    _getBounds() {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const p of this.points) {
            minX = Math.min(minX, p.x);
            minY = Math.min(minY, p.y);
            maxX = Math.max(maxX, p.x);
            maxY = Math.max(maxY, p.y);
        }
        const padding = this.lineWidth + 5;
        return {
            x: Math.floor(minX - padding),
            y: Math.floor(minY - padding),
            width: Math.ceil(maxX - minX + padding * 2),
            height: Math.ceil(maxY - minY + padding * 2)
        };
    }

    execute(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        
        const bounds = this._getBounds();
        this._saveImageData(ctx, bounds.x, bounds.y, bounds.width, bounds.height);
        
        ctx.save();
        ctx.strokeStyle = this.color;
        ctx.lineWidth = this.lineWidth;
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

    undo(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        this._restoreImageData(ctx);
    }

    serialize() {
        return {
            ...super.serialize(),
            points: this.points,
            color: this.color,
            lineWidth: this.lineWidth
        };
    }

    static fromData(data) {
        const cmd = new DrawPathCommand(
            data.layerId,
            data.userId,
            data.userName,
            data.points,
            data.color,
            data.lineWidth
        );
        cmd.id = data.id;
        cmd.sequence = data.sequence;
        return cmd;
    }
}

class DrawLineCommand extends BaseCommand {
    constructor(layerId, userId, userName, startX, startY, endX, endY, color, lineWidth) {
        super('line', layerId, userId, userName);
        this.startX = startX;
        this.startY = startY;
        this.endX = endX;
        this.endY = endY;
        this.color = color;
        this.lineWidth = lineWidth;
    }

    _getBounds() {
        const padding = this.lineWidth + 5;
        return {
            x: Math.floor(Math.min(this.startX, this.endX) - padding),
            y: Math.floor(Math.min(this.startY, this.endY) - padding),
            width: Math.ceil(Math.abs(this.endX - this.startX) + padding * 2),
            height: Math.ceil(Math.abs(this.endY - this.startY) + padding * 2)
        };
    }

    execute(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        
        const bounds = this._getBounds();
        this._saveImageData(ctx, bounds.x, bounds.y, bounds.width, bounds.height);
        
        ctx.save();
        ctx.strokeStyle = this.color;
        ctx.lineWidth = this.lineWidth;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(this.startX, this.startY);
        ctx.lineTo(this.endX, this.endY);
        ctx.stroke();
        ctx.restore();
    }

    undo(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        this._restoreImageData(ctx);
    }

    serialize() {
        return {
            ...super.serialize(),
            startX: this.startX,
            startY: this.startY,
            endX: this.endX,
            endY: this.endY,
            color: this.color,
            lineWidth: this.lineWidth
        };
    }

    static fromData(data) {
        const cmd = new DrawLineCommand(
            data.layerId,
            data.userId,
            data.userName,
            data.startX,
            data.startY,
            data.endX,
            data.endY,
            data.color,
            data.lineWidth
        );
        cmd.id = data.id;
        cmd.sequence = data.sequence;
        return cmd;
    }
}

class DrawRectCommand extends BaseCommand {
    constructor(layerId, userId, userName, x, y, width, height, color, lineWidth, fillColor) {
        super('rect', layerId, userId, userName);
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
        this.lineWidth = lineWidth;
        this.fillColor = fillColor;
    }

    _getBounds() {
        const padding = this.lineWidth + 5;
        return {
            x: Math.floor(this.x - padding),
            y: Math.floor(this.y - padding),
            width: Math.ceil(this.width + padding * 2),
            height: Math.ceil(this.height + padding * 2)
        };
    }

    execute(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        
        const bounds = this._getBounds();
        this._saveImageData(ctx, bounds.x, bounds.y, bounds.width, bounds.height);
        
        ctx.save();
        if (this.fillColor) {
            ctx.fillStyle = this.fillColor;
            ctx.fillRect(this.x, this.y, this.width, this.height);
        }
        if (this.lineWidth > 0) {
            ctx.strokeStyle = this.color;
            ctx.lineWidth = this.lineWidth;
            ctx.strokeRect(this.x, this.y, this.width, this.height);
        }
        ctx.restore();
    }

    undo(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        this._restoreImageData(ctx);
    }

    serialize() {
        return {
            ...super.serialize(),
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height,
            color: this.color,
            lineWidth: this.lineWidth,
            fillColor: this.fillColor
        };
    }

    static fromData(data) {
        const cmd = new DrawRectCommand(
            data.layerId,
            data.userId,
            data.userName,
            data.x,
            data.y,
            data.width,
            data.height,
            data.color,
            data.lineWidth,
            data.fillColor
        );
        cmd.id = data.id;
        cmd.sequence = data.sequence;
        return cmd;
    }
}

class DrawCircleCommand extends BaseCommand {
    constructor(layerId, userId, userName, centerX, centerY, radiusX, radiusY, color, lineWidth, fillColor) {
        super('circle', layerId, userId, userName);
        this.centerX = centerX;
        this.centerY = centerY;
        this.radiusX = radiusX;
        this.radiusY = radiusY;
        this.color = color;
        this.lineWidth = lineWidth;
        this.fillColor = fillColor;
    }

    _getBounds() {
        const padding = this.lineWidth + 5;
        return {
            x: Math.floor(this.centerX - this.radiusX - padding),
            y: Math.floor(this.centerY - this.radiusY - padding),
            width: Math.ceil(this.radiusX * 2 + padding * 2),
            height: Math.ceil(this.radiusY * 2 + padding * 2)
        };
    }

    execute(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        
        const bounds = this._getBounds();
        this._saveImageData(ctx, bounds.x, bounds.y, bounds.width, bounds.height);
        
        ctx.save();
        ctx.beginPath();
        ctx.ellipse(this.centerX, this.centerY, this.radiusX, this.radiusY, 0, 0, Math.PI * 2);
        if (this.fillColor) {
            ctx.fillStyle = this.fillColor;
            ctx.fill();
        }
        if (this.lineWidth > 0) {
            ctx.strokeStyle = this.color;
            ctx.lineWidth = this.lineWidth;
            ctx.stroke();
        }
        ctx.restore();
    }

    undo(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        this._restoreImageData(ctx);
    }

    serialize() {
        return {
            ...super.serialize(),
            centerX: this.centerX,
            centerY: this.centerY,
            radiusX: this.radiusX,
            radiusY: this.radiusY,
            color: this.color,
            lineWidth: this.lineWidth,
            fillColor: this.fillColor
        };
    }

    static fromData(data) {
        const cmd = new DrawCircleCommand(
            data.layerId,
            data.userId,
            data.userName,
            data.centerX,
            data.centerY,
            data.radiusX,
            data.radiusY,
            data.color,
            data.lineWidth,
            data.fillColor
        );
        cmd.id = data.id;
        cmd.sequence = data.sequence;
        return cmd;
    }
}

class DrawTextCommand extends BaseCommand {
    constructor(layerId, userId, userName, x, y, text, color, fontSize, fontFamily) {
        super('text', layerId, userId, userName);
        this.x = x;
        this.y = y;
        this.text = text;
        this.color = color;
        this.fontSize = fontSize || 24;
        this.fontFamily = fontFamily || 'Inter, sans-serif';
    }

    _getBounds(ctx) {
        ctx.save();
        ctx.font = `${this.fontSize}px ${this.fontFamily}`;
        const metrics = ctx.measureText(this.text);
        ctx.restore();
        const padding = 10;
        return {
            x: Math.floor(this.x - padding),
            y: Math.floor(this.y - this.fontSize - padding),
            width: Math.ceil(metrics.width + padding * 2),
            height: Math.ceil(this.fontSize * 1.5 + padding * 2)
        };
    }

    execute(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        
        const bounds = this._getBounds(ctx);
        this._saveImageData(ctx, bounds.x, bounds.y, bounds.width, bounds.height);
        
        ctx.save();
        ctx.fillStyle = this.color;
        ctx.font = `${this.fontSize}px ${this.fontFamily}`;
        ctx.textBaseline = 'top';
        ctx.fillText(this.text, this.x, this.y);
        ctx.restore();
    }

    undo(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        this._restoreImageData(ctx);
    }

    serialize() {
        return {
            ...super.serialize(),
            x: this.x,
            y: this.y,
            text: this.text,
            color: this.color,
            fontSize: this.fontSize,
            fontFamily: this.fontFamily
        };
    }

    static fromData(data) {
        const cmd = new DrawTextCommand(
            data.layerId,
            data.userId,
            data.userName,
            data.x,
            data.y,
            data.text,
            data.color,
            data.fontSize,
            data.fontFamily
        );
        cmd.id = data.id;
        cmd.sequence = data.sequence;
        return cmd;
    }
}

class EraseCommand extends BaseCommand {
    constructor(layerId, userId, userName, points, lineWidth) {
        super('erase', layerId, userId, userName);
        this.points = points;
        this.lineWidth = lineWidth;
    }

    _getBounds() {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const p of this.points) {
            minX = Math.min(minX, p.x);
            minY = Math.min(minY, p.y);
            maxX = Math.max(maxX, p.x);
            maxY = Math.max(maxY, p.y);
        }
        const padding = this.lineWidth + 5;
        return {
            x: Math.floor(minX - padding),
            y: Math.floor(minY - padding),
            width: Math.ceil(maxX - minX + padding * 2),
            height: Math.ceil(maxY - minY + padding * 2)
        };
    }

    execute(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        
        const bounds = this._getBounds();
        this._saveImageData(ctx, bounds.x, bounds.y, bounds.width, bounds.height);
        
        ctx.save();
        ctx.globalCompositeOperation = 'destination-out';
        ctx.lineWidth = this.lineWidth;
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

    undo(layerManager) {
        const layer = layerManager.getLayerById(this.layerId);
        if (!layer) return;
        const ctx = layer.getContext();
        this._restoreImageData(ctx);
    }

    serialize() {
        return {
            ...super.serialize(),
            points: this.points,
            lineWidth: this.lineWidth
        };
    }

    static fromData(data) {
        const cmd = new EraseCommand(
            data.layerId,
            data.userId,
            data.userName,
            data.points,
            data.lineWidth
        );
        cmd.id = data.id;
        cmd.sequence = data.sequence;
        return cmd;
    }
}

class CommandHistory {
    constructor() {
        this.undoStack = [];
        this.redoStack = [];
        this.currentSequence = 0;
        this.onChangeCallback = null;
    }

    setOnChangeCallback(callback) {
        this.onChangeCallback = callback;
    }

    execute(command, layerManager) {
        command.execute(layerManager);
        this.undoStack.push(command);
        this.redoStack = [];
        this.currentSequence = this.undoStack.length;
        this.notifyChange();
    }

    executeRemote(command, layerManager) {
        command.execute(layerManager);
        this.undoStack.push(command);
        this.redoStack = [];
        this.currentSequence = this.undoStack.length;
        this.notifyChange();
    }

    undo(layerManager) {
        if (this.undoStack.length === 0) return null;
        
        const command = this.undoStack.pop();
        command.undo(layerManager);
        this.redoStack.push(command);
        this.currentSequence = this.undoStack.length;
        this.notifyChange();
        return command;
    }

    redo(layerManager) {
        if (this.redoStack.length === 0) return null;
        
        const command = this.redoStack.pop();
        command.execute(layerManager);
        this.undoStack.push(command);
        this.currentSequence = this.undoStack.length;
        this.notifyChange();
        return command;
    }

    undoToSequence(sequence, layerManager) {
        while (this.undoStack.length > sequence && this.undoStack.length > 0) {
            const command = this.undoStack.pop();
            command.undo(layerManager);
            this.redoStack.push(command);
        }
        this.currentSequence = this.undoStack.length;
        this.notifyChange();
    }

    canUndo() {
        return this.undoStack.length > 0;
    }

    canRedo() {
        return this.redoStack.length > 0;
    }

    clear() {
        this.undoStack = [];
        this.redoStack = [];
        this.currentSequence = 0;
        this.notifyChange();
    }

    notifyChange() {
        if (this.onChangeCallback) {
            this.onChangeCallback({
                canUndo: this.canUndo(),
                canRedo: this.canRedo(),
                undoCount: this.undoStack.length,
                redoCount: this.redoStack.length
            });
        }
    }

    getCommands() {
        return [...this.undoStack];
    }

    loadCommands(commandsData, layerManager) {
        this.clear();
        for (const data of commandsData) {
            const command = BaseCommand.fromData(data.payload || data, layerManager);
            command.execute(layerManager);
            this.undoStack.push(command);
        }
        this.currentSequence = this.undoStack.length;
        this.notifyChange();
    }
}

window.BaseCommand = BaseCommand;
window.DrawPathCommand = DrawPathCommand;
window.DrawLineCommand = DrawLineCommand;
window.DrawRectCommand = DrawRectCommand;
window.DrawCircleCommand = DrawCircleCommand;
window.DrawTextCommand = DrawTextCommand;
window.EraseCommand = EraseCommand;
window.CommandHistory = CommandHistory;
