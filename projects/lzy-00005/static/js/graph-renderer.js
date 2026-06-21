class GraphRenderer {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.options = {
            nodeRadius: 18,
            linkColor: '#c7c7cc',
            nodeColors: {
                current: '#0071e3',
                linked: '#34c759',
                normal: '#86868b'
            },
            fontSize: 11,
            damping: 0.85,
            repulsion: 4000,
            attraction: 0.005,
            centerGravity: 0.01,
            ...options
        };

        this.nodes = [];
        this.edges = [];
        this.nodeMap = new Map();
        this.currentNoteId = null;
        this.linkedNoteIds = new Set();

        this.offsetX = 0;
        this.offsetY = 0;
        this.scale = 1;

        this.isDragging = false;
        this.isPanning = false;
        this.dragNode = null;
        this.lastMouseX = 0;
        this.lastMouseY = 0;

        this.animationId = null;
        this.onNodeClick = null;
        this.onZoomChange = null;

        this._init();
    }

    _init() {
        this._resize();
        window.addEventListener('resize', () => this._resize());

        this.canvas.addEventListener('mousedown', (e) => this._onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this._onMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this._onMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this._onWheel(e), { passive: false });
        this.canvas.addEventListener('click', (e) => this._onClick(e));
    }

    _resize() {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        this.width = rect.width;
        this.height = rect.height;
        this.render();
    }

    setData(graphData, currentNoteId = null) {
        this.nodes = graphData.nodes.map(node => ({
            ...node,
            x: this.width / 2 + (Math.random() - 0.5) * 200,
            y: this.height / 2 + (Math.random() - 0.5) * 200,
            vx: 0,
            vy: 0
        }));
        this.edges = graphData.edges;
        this.nodeMap = new Map(this.nodes.map(n => [n.id, n]));
        this.currentNoteId = currentNoteId;
        this._updateLinkedNotes();
        this._startSimulation();
    }

    setCurrentNote(noteId) {
        this.currentNoteId = noteId;
        this._updateLinkedNotes();
        this.render();
    }

    _updateLinkedNotes() {
        this.linkedNoteIds = new Set();
        if (!this.currentNoteId) return;
        for (const edge of this.edges) {
            if (edge.source === this.currentNoteId) {
                this.linkedNoteIds.add(edge.target);
            }
            if (edge.target === this.currentNoteId) {
                this.linkedNoteIds.add(edge.source);
            }
        }
    }

    _startSimulation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        let stableCount = 0;
        const simulate = () => {
            const moved = this._simulateStep();
            this.render();
            if (!moved) {
                stableCount++;
            } else {
                stableCount = 0;
            }
            if (stableCount < 60) {
                this.animationId = requestAnimationFrame(simulate);
            }
        };
        simulate();
    }

    _simulateStep() {
        let moved = false;
        const { repulsion, attraction, centerGravity, damping } = this.options;
        const cx = this.width / 2;
        const cy = this.height / 2;

        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                const a = this.nodes[i];
                const b = this.nodes[j];
                let dx = b.x - a.x;
                let dy = b.y - a.y;
                let distSq = dx * dx + dy * dy;
                if (distSq < 1) distSq = 1;
                const dist = Math.sqrt(distSq);
                const force = repulsion / distSq;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                a.vx -= fx;
                a.vy -= fy;
                b.vx += fx;
                b.vy += fy;
            }
        }

        for (const edge of this.edges) {
            const source = this.nodeMap.get(edge.source);
            const target = this.nodeMap.get(edge.target);
            if (!source || !target) continue;
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const force = attraction;
            source.vx += dx * force;
            source.vy += dy * force;
            target.vx -= dx * force;
            target.vy -= dy * force;
        }

        for (const node of this.nodes) {
            if (node === this.dragNode) continue;
            node.vx += (cx - node.x) * centerGravity;
            node.vy += (cy - node.y) * centerGravity;
            node.vx *= damping;
            node.vy *= damping;
            node.x += node.vx;
            node.y += node.vy;
            if (Math.abs(node.vx) > 0.01 || Math.abs(node.vy) > 0.01) {
                moved = true;
            }
        }

        return moved;
    }

    _screenToWorld(sx, sy) {
        return {
            x: (sx - this.offsetX) / this.scale,
            y: (sy - this.offsetY) / this.scale
        };
    }

    _getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    _findNodeAt(sx, sy) {
        const pos = this._screenToWorld(sx, sy);
        for (let i = this.nodes.length - 1; i >= 0; i--) {
            const node = this.nodes[i];
            const dx = pos.x - node.x;
            const dy = pos.y - node.y;
            if (dx * dx + dy * dy <= this.options.nodeRadius * this.options.nodeRadius) {
                return node;
            }
        }
        return null;
    }

    _onMouseDown(e) {
        const pos = this._getMousePos(e);
        const node = this._findNodeAt(pos.x, pos.y);
        if (node) {
            this.isDragging = true;
            this.dragNode = node;
            node.vx = 0;
            node.vy = 0;
        } else {
            this.isPanning = true;
        }
        this.lastMouseX = pos.x;
        this.lastMouseY = pos.y;
    }

    _onMouseMove(e) {
        const pos = this._getMousePos(e);
        if (this.isDragging && this.dragNode) {
            const world = this._screenToWorld(pos.x, pos.y);
            this.dragNode.x = world.x;
            this.dragNode.y = world.y;
            this.dragNode.vx = 0;
            this.dragNode.vy = 0;
            this.render();
            this._startSimulation();
        } else if (this.isPanning) {
            this.offsetX += pos.x - this.lastMouseX;
            this.offsetY += pos.y - this.lastMouseY;
            this.lastMouseX = pos.x;
            this.lastMouseY = pos.y;
            this.render();
        }
    }

    _onMouseUp(e) {
        this.isDragging = false;
        this.isPanning = false;
        this.dragNode = null;
    }

    _onWheel(e) {
        e.preventDefault();
        const pos = this._getMousePos(e);
        const zoomSpeed = 0.001;
        const delta = -e.deltaY * zoomSpeed;
        const newScale = Math.max(0.3, Math.min(3, this.scale * (1 + delta)));

        const world = this._screenToWorld(pos.x, pos.y);
        this.scale = newScale;
        this.offsetX = pos.x - world.x * this.scale;
        this.offsetY = pos.y - world.y * this.scale;

        if (this.onZoomChange) {
            this.onZoomChange(Math.round(this.scale * 100));
        }
        this.render();
    }

    _onClick(e) {
        if (this.isDragging || this.isPanning) return;
        const pos = this._getMousePos(e);
        const node = this._findNodeAt(pos.x, pos.y);
        if (node && this.onNodeClick) {
            this.onNodeClick(node.id);
        }
    }

    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.width, this.height);
        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);

        ctx.strokeStyle = this.options.linkColor;
        ctx.lineWidth = 1.5;
        for (const edge of this.edges) {
            const source = this.nodeMap.get(edge.source);
            const target = this.nodeMap.get(edge.target);
            if (!source || !target) continue;
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 1) continue;
            const r = this.options.nodeRadius;
            const sx = source.x + (dx / dist) * r;
            const sy = source.y + (dy / dist) * r;
            const ex = target.x - (dx / dist) * (r + 8);
            const ey = target.y - (dy / dist) * (r + 8);

            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(ex, ey);
            ctx.stroke();

            const angle = Math.atan2(dy, dx);
            ctx.beginPath();
            ctx.moveTo(ex, ey);
            ctx.lineTo(ex - 8 * Math.cos(angle - Math.PI / 6), ey - 8 * Math.sin(angle - Math.PI / 6));
            ctx.lineTo(ex - 8 * Math.cos(angle + Math.PI / 6), ey - 8 * Math.sin(angle + Math.PI / 6));
            ctx.closePath();
            ctx.fillStyle = this.options.linkColor;
            ctx.fill();
        }

        ctx.font = `${this.options.fontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        for (const node of this.nodes) {
            let color = this.options.nodeColors.normal;
            if (node.id === this.currentNoteId) {
                color = this.options.nodeColors.current;
            } else if (this.linkedNoteIds.has(node.id)) {
                color = this.options.nodeColors.linked;
            }

            ctx.beginPath();
            ctx.arc(node.x, node.y, this.options.nodeRadius, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.fillStyle = '#1d1d1f';
            ctx.fillText(node.title, node.x, node.y + this.options.nodeRadius + 6);
        }

        ctx.restore();
    }

    resetView() {
        this.offsetX = 0;
        this.offsetY = 0;
        this.scale = 1;
        if (this.onZoomChange) {
            this.onZoomChange(100);
        }
        this.render();
    }
}

export default GraphRenderer;
