class Layer {
    constructor(id, name, width, height) {
        this.id = id;
        this.name = name;
        this.visible = true;
        this.canvas = document.createElement('canvas');
        this.canvas.width = width;
        this.canvas.height = height;
        this.ctx = this.canvas.getContext('2d');
    }

    resize(width, height) {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        this.canvas.width = width;
        this.canvas.height = height;
        this.ctx.putImageData(imageData, 0, 0);
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    getImageData(x, y, width, height) {
        return this.ctx.getImageData(x, y, width, height);
    }

    putImageData(imageData, x, y) {
        this.ctx.putImageData(imageData, x, y);
    }

    getContext() {
        return this.ctx;
    }
}

class LayerManager {
    constructor(maxLayers = 5, width = 1920, height = 1080) {
        this.maxLayers = maxLayers;
        this.width = width;
        this.height = height;
        this.layers = [];
        this.currentLayerId = null;
        this.layerCounter = 0;
        this.onChangeCallback = null;

        this.addLayer('背景');
    }

    setOnChangeCallback(callback) {
        this.onChangeCallback = callback;
    }

    generateId() {
        return `layer_${Date.now()}_${++this.layerCounter}`;
    }

    addLayer(name) {
        if (this.layers.length >= this.maxLayers) {
            throw new Error(`最多只能创建 ${this.maxLayers} 个图层`);
        }

        const id = this.generateId();
        const layerName = name || `图层 ${this.layers.length + 1}`;
        const layer = new Layer(id, layerName, this.width, this.height);
        this.layers.push(layer);
        this.currentLayerId = id;
        this.notifyChange();
        return layer;
    }

    removeLayer(layerId) {
        if (this.layers.length <= 1) {
            throw new Error('至少需要保留一个图层');
        }

        const index = this.layers.findIndex(l => l.id === layerId);
        if (index === -1) return false;

        const layer = this.layers[index];
        layer.clear();
        this.layers.splice(index, 1);

        if (this.currentLayerId === layerId) {
            this.currentLayerId = this.layers[Math.max(0, index - 1)].id;
        }

        this.notifyChange();
        return true;
    }

    setCurrentLayer(layerId) {
        const exists = this.layers.some(l => l.id === layerId);
        if (exists) {
            this.currentLayerId = layerId;
            this.notifyChange();
        }
    }

    getCurrentLayer() {
        return this.layers.find(l => l.id === this.currentLayerId) || null;
    }

    setLayerVisibility(layerId, visible) {
        const layer = this.layers.find(l => l.id === layerId);
        if (layer) {
            layer.visible = visible;
            this.notifyChange();
        }
    }

    getLayers() {
        return [...this.layers];
    }

    getLayerById(layerId) {
        return this.layers.find(l => l.id === layerId) || null;
    }

    resize(width, height) {
        this.width = width;
        this.height = height;
        this.layers.forEach(layer => layer.resize(width, height));
    }

    clearAll() {
        this.layers.forEach(layer => layer.clear());
        this.notifyChange();
    }

    notifyChange() {
        if (this.onChangeCallback) {
            this.onChangeCallback(this.layers, this.currentLayerId);
        }
    }

    reorderLayer(fromIndex, toIndex) {
        if (fromIndex < 0 || fromIndex >= this.layers.length) return;
        if (toIndex < 0 || toIndex >= this.layers.length) return;
        
        const [removed] = this.layers.splice(fromIndex, 1);
        this.layers.splice(toIndex, 0, removed);
        this.notifyChange();
    }
}

window.LayerManager = LayerManager;
window.Layer = Layer;
