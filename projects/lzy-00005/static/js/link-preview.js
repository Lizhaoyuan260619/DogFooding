import ApiClient from './api.js';

class LinkPreviewCache {
    constructor() {
        this.cache = new Map();
        this.maxSize = 50;
        this.ttl = 5 * 60 * 1000;
    }

    get(noteId) {
        const entry = this.cache.get(noteId);
        if (!entry) return null;
        if (Date.now() - entry.timestamp > this.ttl) {
            this.cache.delete(noteId);
            return null;
        }
        return entry.data;
    }

    set(noteId, data) {
        if (this.cache.size >= this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        this.cache.set(noteId, {
            data,
            timestamp: Date.now()
        });
    }

    invalidate(noteId) {
        this.cache.delete(noteId);
    }

    clear() {
        this.cache.clear();
    }

    has(noteId) {
        return this.get(noteId) !== null;
    }

    async preload(noteIds) {
        const toLoad = noteIds.filter(id => !this.has(id));
        if (toLoad.length === 0) return;

        const batchSize = 3;
        const batch = toLoad.slice(0, batchSize);

        try {
            const promises = batch.map(id =>
                ApiClient.getNote(id).then(note => {
                    if (note) {
                        this.set(id, note);
                    }
                }).catch(() => {})
            );
            await Promise.all(promises);
        } catch (e) {
            console.warn('Preload failed', e);
        }
    }
}

const previewCache = new LinkPreviewCache();

class LinkPreviewCard {
    constructor() {
        this.card = null;
        this.showTimer = null;
        this.hideTimer = null;
        this.currentNoteId = null;
        this.currentTriggerEl = null;
        this.isHoveringCard = false;
        this.isHoveringTrigger = false;
        this.showDelay = 400;
        this.hideDelay = 200;
        this.fadeDuration = 150;
        this.cardWidth = 320;
        this.cardMaxHeight = 240;
        this.isVisible = false;
        this.isAnimating = false;

        this.initCard();
        this.bindCardEvents();
    }

    initCard() {
        this.card = document.createElement('div');
        this.card.className = 'link-preview-card';
        this.card.innerHTML = `
            <div class="link-preview-loading">
                <div class="link-preview-spinner"></div>
                <span>加载中...</span>
            </div>
        `;
        this.card.style.display = 'none';
        this.card.style.opacity = '0';
        this.card.style.pointerEvents = 'none';
        document.body.appendChild(this.card);
    }

    bindCardEvents() {
        this.card.addEventListener('mouseenter', () => {
            this.isHoveringCard = true;
            this.cancelHide();
        });

        this.card.addEventListener('mouseleave', () => {
            this.isHoveringCard = false;
            this.tryHide();
        });

        document.addEventListener('mousedown', (e) => {
            if (this.isVisible &&
                !this.card.contains(e.target) &&
                !e.target.closest('.wikilink') &&
                !e.target.closest('.link-chip')) {
                this.forceHide();
            }
        }, true);

        let scrollTimeout;
        document.addEventListener('scroll', () => {
            if (!this.isVisible) return;
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (this.isVisible && !this.isHoveringCard && !this.isHoveringTrigger) {
                    this.forceHide();
                }
            }, 100);
        }, true);

        window.addEventListener('resize', () => {
            if (this.isVisible) {
                this.forceHide();
            }
        });
    }

    show(noteId, triggerEl) {
        this.currentNoteId = noteId;
        this.currentTriggerEl = triggerEl;
        this.isHoveringTrigger = true;

        this.cancelHide();
        this.cancelShow();

        if (this.isVisible) {
            this.renderCard(noteId, triggerEl);
            return;
        }

        this.showTimer = setTimeout(() => {
            this.showTimer = null;
            this.renderCard(noteId, triggerEl);
        }, this.showDelay);
    }

    leaveTrigger(triggerEl) {
        if (this.currentTriggerEl !== triggerEl) return;
        this.isHoveringTrigger = false;
        this.tryHide();
    }

    tryHide() {
        if (this.isHoveringCard || this.isHoveringTrigger) {
            return;
        }
        this.hide();
    }

    hide() {
        this.cancelShow();
        this.cancelHide();

        if (!this.isVisible && !this.isAnimating) {
            return;
        }

        this.hideTimer = setTimeout(() => {
            this.hideTimer = null;
            if (this.isHoveringCard || this.isHoveringTrigger) {
                return;
            }
            this.performHide();
        }, this.hideDelay);
    }

    forceHide() {
        this.cancelShow();
        this.cancelHide();
        this.isHoveringCard = false;
        this.isHoveringTrigger = false;
        this.performHide();
    }

    performHide() {
        if (!this.isVisible) {
            this.currentNoteId = null;
            this.currentTriggerEl = null;
            return;
        }

        this.isAnimating = true;
        this.card.style.pointerEvents = 'none';
        this.card.style.opacity = '0';
        this.card.style.transform = 'translateY(4px)';

        setTimeout(() => {
            this.card.style.display = 'none';
            this.isVisible = false;
            this.isAnimating = false;
            this.currentNoteId = null;
            this.currentTriggerEl = null;
        }, this.fadeDuration);
    }

    cancelShow() {
        if (this.showTimer) {
            clearTimeout(this.showTimer);
            this.showTimer = null;
        }
    }

    cancelHide() {
        if (this.hideTimer) {
            clearTimeout(this.hideTimer);
            this.hideTimer = null;
        }
    }

    async renderCard(noteId, triggerEl) {
        this.card.innerHTML = `
            <div class="link-preview-loading">
                <div class="link-preview-spinner"></div>
                <span>加载中...</span>
            </div>
        `;

        this.card.style.display = 'flex';
        this.card.style.width = this.cardWidth + 'px';
        this.card.style.maxHeight = this.cardMaxHeight + 'px';
        this.card.style.pointerEvents = 'none';

        this.positionCard(triggerEl);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.card.style.opacity = '1';
                this.card.style.transform = 'translateY(0)';
                this.card.style.pointerEvents = 'auto';
                this.isVisible = true;
                this.isAnimating = false;
            });
        });

        const cached = previewCache.get(noteId);
        if (cached) {
            this.renderContent(cached);
            this.positionCard(triggerEl);
            return;
        }

        try {
            const note = await ApiClient.getNote(noteId);
            if (note && this.currentNoteId === noteId) {
                previewCache.set(noteId, note);
                this.renderContent(note);
                this.positionCard(triggerEl);
            }
        } catch (err) {
            if (this.currentNoteId === noteId) {
                this.renderError();
                this.positionCard(triggerEl);
            }
        }
    }

    renderContent(note) {
        const summary = this.extractSummary(note.content, 150);
        const updatedAt = this.formatDate(note.updated_at);

        const existingClickHandler = this.card._clickHandler;
        if (existingClickHandler) {
            this.card.removeEventListener('click', existingClickHandler);
        }

        this.card.innerHTML = `
            <div class="link-preview-header">
                <div class="link-preview-title">${this.escapeHtml(note.title || '（无标题）')}</div>
                <div class="link-preview-meta">更新于 ${updatedAt}</div>
            </div>
            <div class="link-preview-body">
                <div class="link-preview-summary">${this.escapeHtml(summary)}</div>
            </div>
            <div class="link-preview-footer">
                <span class="link-preview-id">ID: ${note.id}</span>
                <span class="link-preview-hint">点击打开笔记</span>
            </div>
        `;

        this.card._clickHandler = () => {
            const event = new CustomEvent('link-preview-click', {
                detail: { noteId: note.id }
            });
            document.dispatchEvent(event);
            this.forceHide();
        };
        this.card.addEventListener('click', this.card._clickHandler);
    }

    renderError() {
        this.card.innerHTML = `
            <div class="link-preview-error">
                <span>⚠️ 加载失败</span>
            </div>
        `;
    }

    positionCard(triggerEl) {
        if (!triggerEl) return;

        const rect = triggerEl.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const margin = 12;
        const gap = 8;

        const cardRect = this.card.getBoundingClientRect();
        const actualWidth = cardRect.width || this.cardWidth;
        const actualHeight = cardRect.height || this.cardMaxHeight;

        let left = rect.left;
        let top = rect.bottom + gap;

        if (left + actualWidth > viewportWidth - margin) {
            left = viewportWidth - actualWidth - margin;
        }
        if (left < margin) {
            left = margin;
        }

        const spaceBelow = viewportHeight - rect.bottom;
        const spaceAbove = rect.top;

        if (spaceBelow < actualHeight + gap && spaceAbove > spaceBelow) {
            top = rect.top - actualHeight - gap;
        }

        if (top + actualHeight > viewportHeight - margin) {
            top = viewportHeight - actualHeight - margin;
        }
        if (top < margin) {
            top = margin;
        }

        this.card.style.left = left + 'px';
        this.card.style.top = top + 'px';
    }

    extractSummary(content, maxLength) {
        if (!content) return '';
        const plainText = content
            .replace(/```[\s\S]*?```/g, '')
            .replace(/`[^`]*`/g, '')
            .replace(/#{1,6}\s/g, '')
            .replace(/\*\*(.+?)\*\*/g, '$1')
            .replace(/\*(.+?)\*/g, '$1')
            .replace(/\[\[([^\]]+)\]\([^)]*\)/g, '$1')
            .replace(/\[\[([a-f0-9]{12})\]\]/g, '$1')
            .replace(/>\s/g, '')
            .replace(/[-*+]\s/g, '')
            .replace(/\d+\.\s/g, '')
            .replace(/---/g, '')
            .replace(/\n+/g, ' ')
            .trim();

        if (plainText.length <= maxLength) {
            return plainText;
        }
        return plainText.substring(0, maxLength) + '...';
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            const d = new Date(dateStr);
            const now = new Date();
            const diff = now - d;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);

            if (minutes < 1) return '刚刚';
            if (minutes < 60) return `${minutes} 分钟前`;
            if (hours < 24) return `${hours} 小时前`;
            if (days < 7) return `${days} 天前`;

            return d.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        } catch {
            return dateStr;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    destroy() {
        this.cancelShow();
        this.cancelHide();
        if (this.card && this.card.parentNode) {
            this.card.parentNode.removeChild(this.card);
        }
    }
}

const linkPreviewCard = new LinkPreviewCard();

export default linkPreviewCard;
export { previewCache };
