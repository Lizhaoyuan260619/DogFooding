import ApiClient from './api.js';
import GraphRenderer from './graph-renderer.js';
import linkPreviewCard, { previewCache } from './link-preview.js';

class MarkdownRenderer {
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static render(text) {
        if (!text) return '';
        let html = this.escapeHtml(text);

        html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
            return `<pre><code>${this.escapeHtml(code.trim())}</code></pre>`;
        });

        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>');
        html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>');
        html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');

        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>');

        html = html.replace(/\[\[([a-f0-9]{12})\]\]/g, (match, id) => {
            return `<span class="wikilink" data-note-id="${id}">[[${id}]]</span>`;
        });

        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
        html = html.replace(/^(\d+)\. (.*)$/gm, '<li>$2</li>');

        html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
            return `<ul>${match}</ul>`;
        });

        html = html.replace(/---/g, '<hr>');

        html = html.split('\n\n').map(para => {
            if (para.startsWith('<') && !para.startsWith('<li>')) return para;
            if (para.trim() === '') return '';
            return `<p>${para.replace(/\n/g, '<br>')}</p>`;
        }).join('\n');

        return html;
    }
}

class App {
    constructor() {
        this.currentNote = null;
        this.currentTags = [];
        this.notes = [];
        this.tags = [];
        this.graphRenderer = null;
        this.activeTab = 'notes';
        this.filterMode = null;
        this.filterValue = null;

        this.initElements();
        this.bindEvents();
        this.init();
    }

    initElements() {
        this.els = {
            sidebar: document.querySelector('.sidebar'),
            resizer: document.getElementById('resizer'),
            newNoteBtn: document.getElementById('newNoteBtn'),
            saveNoteBtn: document.getElementById('saveNoteBtn'),
            deleteNoteBtn: document.getElementById('deleteNoteBtn'),
            exportNoteBtn: document.getElementById('exportNoteBtn'),
            historyBtn: document.getElementById('historyBtn'),
            shareBtn: document.getElementById('shareBtn'),
            searchInput: document.getElementById('searchInput'),
            notesList: document.getElementById('notesList'),
            tagsList: document.getElementById('tagsList'),
            noteTitle: document.getElementById('noteTitle'),
            noteContent: document.getElementById('noteContent'),
            notePreview: document.getElementById('notePreview'),
            noteMeta: document.getElementById('noteMeta'),
            tagsContainer: document.getElementById('tagsContainer'),
            tagInput: document.getElementById('tagInput'),
            backlinksList: document.getElementById('backlinksList'),
            editorPanel: document.getElementById('editorPanel'),
            emptyState: document.getElementById('emptyState'),
            zoomLevel: document.getElementById('zoomLevel'),
            refreshGraphBtn: document.getElementById('refreshGraphBtn'),
            tabBtns: document.querySelectorAll('.tab-btn'),
            tabContents: document.querySelectorAll('.tab-content'),
            modalOverlay: document.getElementById('modalOverlay'),
            historyModal: document.getElementById('historyModal'),
            shareModal: document.getElementById('shareModal'),
            versionPreviewModal: document.getElementById('versionPreviewModal'),
            historyList: document.getElementById('historyList'),
            shareList: document.getElementById('shareList'),
            sharePermission: document.getElementById('sharePermission'),
            shareExpiresDays: document.getElementById('shareExpiresDays'),
            sharePassword: document.getElementById('sharePassword'),
            createShareBtn: document.getElementById('createShareBtn'),
            versionPreviewTitle: document.getElementById('versionPreviewTitle'),
            versionPreviewMeta: document.getElementById('versionPreviewMeta'),
            versionPreviewTitleContent: document.getElementById('versionPreviewTitleContent'),
            versionPreviewBodyContent: document.getElementById('versionPreviewBodyContent'),
            restoreVersionBtn: document.getElementById('restoreVersionBtn')
        };
        this.currentPreviewVersion = null;
    }

    bindEvents() {
        this.els.newNoteBtn.addEventListener('click', () => this.createNewNote());
        this.els.saveNoteBtn.addEventListener('click', () => this.saveCurrentNote());
        this.els.deleteNoteBtn.addEventListener('click', () => this.deleteCurrentNote());
        this.els.exportNoteBtn.addEventListener('click', () => this.exportCurrentNote());
        this.els.historyBtn.addEventListener('click', () => this.openHistoryModal());
        this.els.shareBtn.addEventListener('click', () => this.openShareModal());

        this.els.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.els.modalOverlay) this.closeAllModals();
        });
        document.querySelectorAll('[data-close-modal]').forEach(btn => {
            btn.addEventListener('click', () => this.closeAllModals());
        });

        this.els.createShareBtn.addEventListener('click', () => this.createShare());
        this.els.restoreVersionBtn.addEventListener('click', () => this.restoreCurrentVersion());

        this.els.noteTitle.addEventListener('input', () => this.updatePreview());
        this.els.noteContent.addEventListener('input', () => this.updatePreview());

        this.els.tagInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTag();
            } else if (e.key === 'Backspace' && this.els.tagInput.value === '' && this.currentTags.length > 0) {
                e.preventDefault();
                this.currentTags.pop();
                this.renderTags();
            }
        });

        this.els.notePreview.addEventListener('click', (e) => {
            const wikilink = e.target.closest('.wikilink');
            if (wikilink) {
                const noteId = wikilink.dataset.noteId;
                this.loadNote(noteId);
            }
        });

        this.initLinkPreviewEvents();

        let searchTimer;
        this.els.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimer);
            const query = e.target.value.trim();
            searchTimer = setTimeout(() => {
                if (query) {
                    this.searchNotes(query);
                } else {
                    this.filterMode = null;
                    this.filterValue = null;
                    this.loadNotes();
                }
            }, 200);
        });

        this.els.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });

        this.els.refreshGraphBtn.addEventListener('click', () => this.loadGraph());

        this.initResizer();
    }

    initLinkPreviewEvents() {
        this.bindPreviewHover(this.els.notePreview, '.wikilink');
        this.bindPreviewHover(this.els.backlinksList, '.link-chip');

        document.addEventListener('link-preview-click', (e) => {
            if (e.detail?.noteId) {
                this.loadNote(e.detail.noteId);
            }
        });
    }

    bindPreviewHover(container, selector) {
        if (!container) return;

        container.addEventListener('mouseover', (e) => {
            const target = e.target.closest(selector);
            if (!target || !container.contains(target)) return;

            const related = e.relatedTarget;
            if (related && (target.contains(related) || related === target)) return;

            const noteId = target.dataset.noteId;
            if (noteId) {
                linkPreviewCard.show(noteId, target);
            }
        });

        container.addEventListener('mouseout', (e) => {
            const target = e.target.closest(selector);
            if (!target || !container.contains(target)) return;

            const related = e.relatedTarget;
            if (related && (target.contains(related) || related === target)) return;
            if (related && related.closest('.link-preview-card')) return;

            linkPreviewCard.leaveTrigger(target);
        });
    }

    initResizer() {
        const resizer = this.els.resizer;
        const sidebar = this.els.sidebar;
        if (!resizer || !sidebar) return;

        const minWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sidebar-min-width')) || 180;
        const maxWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sidebar-max-width')) || 600;
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;

        const onMouseDown = (e) => {
            if (window.innerWidth <= 560) return;
            isResizing = true;
            startX = e.clientX;
            startWidth = sidebar.getBoundingClientRect().width;
            resizer.classList.add('dragging');
            document.body.classList.add('resizing');
            e.preventDefault();
        };

        const onMouseMove = (e) => {
            if (!isResizing) return;
            const delta = e.clientX - startX;
            let newWidth = startWidth + delta;
            newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
            document.documentElement.style.setProperty('--sidebar-width', newWidth + 'px');
        };

        const onMouseUp = () => {
            if (!isResizing) return;
            isResizing = false;
            resizer.classList.remove('dragging');
            document.body.classList.remove('resizing');
            if (this.graphRenderer) {
                setTimeout(() => this.graphRenderer.render(), 50);
            }
        };

        resizer.addEventListener('mousedown', onMouseDown);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    async init() {
        const canvas = document.getElementById('graphCanvas');
        this.graphRenderer = new GraphRenderer(canvas);
        this.graphRenderer.onNodeClick = (noteId) => this.loadNote(noteId);
        this.graphRenderer.onZoomChange = (level) => {
            this.els.zoomLevel.textContent = level + '%';
        };

        await Promise.all([
            this.loadNotes(),
            this.loadTags(),
            this.loadGraph()
        ]);
    }

    switchTab(tab) {
        this.activeTab = tab;
        this.els.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        this.els.tabContents.forEach(content => {
            content.classList.toggle('hidden', content.id !== tab + '-tab');
        });
        if (tab === 'graph') {
            setTimeout(() => this.loadGraph(), 50);
        }
    }

    async loadNotes() {
        try {
            let notes;
            if (this.filterMode === 'tag') {
                notes = await ApiClient.getNotesByTag(this.filterValue);
            } else {
                notes = await ApiClient.listNotes();
            }
            this.notes = notes;
            this.renderNotesList();
        } catch (err) {
            console.error('Failed to load notes:', err);
        }
    }

    async loadTags() {
        try {
            this.tags = await ApiClient.listTags();
            this.renderTagsList();
        } catch (err) {
            console.error('Failed to load tags:', err);
        }
    }

    async loadGraph() {
        try {
            const graphData = await ApiClient.getGraph();
            this.graphRenderer.setData(graphData, this.currentNote?.id);
        } catch (err) {
            console.error('Failed to load graph:', err);
        }
    }

    async searchNotes(query) {
        try {
            this.notes = await ApiClient.searchNotes(query);
            this.renderNotesList();
        } catch (err) {
            console.error('Search failed:', err);
        }
    }

    renderNotesList() {
        this.els.notesList.innerHTML = '';
        if (this.notes.length === 0) {
            this.els.notesList.innerHTML = '<div style="padding: 20px; text-align: center; color: #86868b; font-size: 13px;">暂无笔记</div>';
            return;
        }
        this.notes.forEach(note => {
            const item = document.createElement('div');
            item.className = 'note-item';
            if (this.currentNote?.id === note.id) {
                item.classList.add('active');
            }
            const tagsHtml = note.tags && note.tags.length > 0
                ? `<div class="note-item-tags">${note.tags.map(t => `<span class="note-item-tag">${t.name}</span>`).join('')}</div>`
                : '';
            item.innerHTML = `
                <div class="note-item-title">${note.title || '（无标题）'}</div>
                <div class="note-item-meta">ID: ${note.id}</div>
                ${tagsHtml}
            `;
            item.addEventListener('click', () => this.loadNote(note.id));
            this.els.notesList.appendChild(item);
        });
    }

    renderTagsList() {
        this.els.tagsList.innerHTML = '';
        if (this.tags.length === 0) {
            this.els.tagsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #86868b; font-size: 13px;">暂无标签</div>';
            return;
        }
        this.tags.forEach(tag => {
            const item = document.createElement('div');
            item.className = 'tag-item';
            if (this.filterMode === 'tag' && this.filterValue === tag.name) {
                item.classList.add('active');
            }
            item.innerHTML = `
                <span class="tag-item-name">#${tag.name}</span>
                <span class="tag-item-count">${tag.note_count}</span>
            `;
            item.addEventListener('click', () => {
                if (this.filterMode === 'tag' && this.filterValue === tag.name) {
                    this.filterMode = null;
                    this.filterValue = null;
                } else {
                    this.filterMode = 'tag';
                    this.filterValue = tag.name;
                }
                this.renderTagsList();
                this.loadNotes();
            });
            this.els.tagsList.appendChild(item);
        });
    }

    renderTags() {
        this.els.tagsContainer.innerHTML = '';
        this.currentTags.forEach((tag, index) => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip';
            chip.innerHTML = `
                <span>${tag}</span>
                <span class="tag-chip-remove" data-index="${index}">&times;</span>
            `;
            chip.querySelector('.tag-chip-remove').addEventListener('click', () => {
                this.currentTags.splice(index, 1);
                this.renderTags();
            });
            this.els.tagsContainer.appendChild(chip);
        });
    }

    addTag() {
        const value = this.els.tagInput.value.trim();
        if (value && !this.currentTags.includes(value)) {
            this.currentTags.push(value);
            this.renderTags();
        }
        this.els.tagInput.value = '';
    }

    async loadNote(noteId) {
        try {
            const note = await ApiClient.getNote(noteId);
            if (!note) return;
            this.currentNote = note;
            this.currentTags = note.tags ? note.tags.map(t => t.name) : [];
            this.els.noteTitle.value = note.title;
            this.els.noteContent.value = note.content;
            this.renderTags();
            this.updatePreview();
            this.renderBacklinks(note);
            this.showEditor();
            this.els.noteMeta.textContent = `ID: ${note.id} | 创建: ${this.formatDate(note.created_at)} | 修改: ${this.formatDate(note.updated_at)}`;
            this.renderNotesList();
            this.graphRenderer.setCurrentNote(noteId);
            this.preloadLinkedNotes(note);
        } catch (err) {
            console.error('Failed to load note:', err);
        }
    }

    preloadLinkedNotes(note) {
        const linkedIds = [];
        if (note.outgoing_links) {
            linkedIds.push(...note.outgoing_links.map(l => l.id));
        }
        if (note.incoming_links) {
            linkedIds.push(...note.incoming_links.map(l => l.id));
        }
        if (linkedIds.length > 0) {
            setTimeout(() => {
                previewCache.preload(linkedIds);
            }, 500);
        }
    }

    renderBacklinks(note) {
        const backlinks = note.incoming_links || [];
        this.els.backlinksList.innerHTML = '';
        if (backlinks.length === 0) {
            this.els.backlinksList.innerHTML = '<span style="color: #86868b; font-size: 13px;">暂无反向链接</span>';
            return;
        }
        backlinks.forEach(link => {
            const chip = document.createElement('span');
            chip.className = 'link-chip';
            chip.dataset.noteId = link.id;
            chip.innerHTML = `
                <span>${link.title || '（无标题）'}</span>
                <span class="link-chip-id">${link.id}</span>
            `;
            chip.addEventListener('click', () => this.loadNote(link.id));
            this.els.backlinksList.appendChild(chip);
        });
    }

    createNewNote() {
        this.currentNote = null;
        this.currentTags = [];
        this.els.noteTitle.value = '';
        this.els.noteContent.value = '';
        this.els.noteMeta.textContent = '新建笔记';
        this.renderTags();
        this.updatePreview();
        this.renderBacklinks({ incoming_links: [] });
        this.showEditor();
        this.els.noteTitle.focus();
    }

    async saveCurrentNote() {
        const title = this.els.noteTitle.value.trim();
        if (!title) {
            alert('请输入笔记标题');
            return;
        }
        const content = this.els.noteContent.value;
        const tags = [...this.currentTags];
        try {
            if (this.currentNote) {
                this.currentNote = await ApiClient.updateNote(this.currentNote.id, {
                    title, content, tags
                });
                previewCache.invalidate(this.currentNote.id);
                this.invalidateLinkedNotesCache(this.currentNote);
            } else {
                this.currentNote = await ApiClient.createNote({
                    title, content, tags
                });
            }
            this.els.noteMeta.textContent = `ID: ${this.currentNote.id} | 创建: ${this.formatDate(this.currentNote.created_at)} | 修改: ${this.formatDate(this.currentNote.updated_at)}`;
            this.renderBacklinks(this.currentNote);
            await Promise.all([
                this.loadNotes(),
                this.loadTags(),
                this.loadGraph()
            ]);
        } catch (err) {
            console.error('Failed to save note:', err);
            alert('保存失败');
        }
    }

    invalidateLinkedNotesCache(note) {
        const linkedIds = [];
        if (note.outgoing_links) {
            linkedIds.push(...note.outgoing_links.map(l => l.id));
        }
        if (note.incoming_links) {
            linkedIds.push(...note.incoming_links.map(l => l.id));
        }
        linkedIds.forEach(id => previewCache.invalidate(id));
    }

    async deleteCurrentNote() {
        if (!this.currentNote) {
            this.showEmptyState();
            return;
        }
        if (!confirm(`确定要删除笔记「${this.currentNote.title}」吗？`)) {
            return;
        }
        try {
            const noteId = this.currentNote.id;
            const linkedNote = { ...this.currentNote };
            await ApiClient.deleteNote(noteId);
            previewCache.invalidate(noteId);
            this.invalidateLinkedNotesCache(linkedNote);
            this.currentNote = null;
            this.showEmptyState();
            await Promise.all([
                this.loadNotes(),
                this.loadTags(),
                this.loadGraph()
            ]);
        } catch (err) {
            console.error('Failed to delete note:', err);
            alert('删除失败');
        }
    }

    exportCurrentNote() {
        if (this.currentNote) {
            ApiClient.exportNote(this.currentNote.id);
        } else {
            ApiClient.exportAll();
        }
    }

    updatePreview() {
        const title = this.els.noteTitle.value || '（无标题）';
        const content = this.els.noteContent.value;
        const html = `<h1>${MarkdownRenderer.escapeHtml(title)}</h1>\n\n${MarkdownRenderer.render(content)}`;
        this.els.notePreview.innerHTML = html;
    }

    showEditor() {
        this.els.editorPanel.classList.remove('hidden');
        this.els.emptyState.classList.add('hidden');
    }

    showEmptyState() {
        this.els.editorPanel.classList.add('hidden');
        this.els.emptyState.classList.remove('hidden');
        this.graphRenderer.setCurrentNote(null);
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            const d = new Date(dateStr);
            return d.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }

    openModal(modalEl) {
        this.els.modalOverlay.classList.remove('hidden');
        [this.els.historyModal, this.els.shareModal, this.els.versionPreviewModal].forEach(m => {
            if (m) m.classList.add('hidden');
        });
        if (modalEl) modalEl.classList.remove('hidden');
    }

    closeAllModals() {
        this.els.modalOverlay.classList.add('hidden');
        [this.els.historyModal, this.els.shareModal, this.els.versionPreviewModal].forEach(m => {
            if (m) m.classList.add('hidden');
        });
    }

    async openHistoryModal() {
        if (!this.currentNote) {
            this.showToast('请先选择一个笔记', 'error');
            return;
        }
        this.openModal(this.els.historyModal);
        await this.loadVersions();
    }

    async loadVersions() {
        if (!this.currentNote) return;
        try {
            const result = await ApiClient.getNoteVersions(this.currentNote.id);
            const versions = result.versions || [];
            if (versions.length === 0) {
                this.els.historyList.innerHTML = '<div class="history-empty">暂无历史版本</div>';
                return;
            }
            this.els.historyList.innerHTML = versions.map(v => `
                <div class="history-item" data-version-id="${v.id}">
                    <div class="history-item-header">
                        <span class="history-item-time">${this.formatDate(v.created_at)}</span>
                        <span class="history-item-author">${v.modified_by || '未知用户'}</span>
                    </div>
                    <div class="history-item-summary">${v.change_summary || '无变更说明'}</div>
                    <div class="history-item-title">${v.title || '（无标题）'}</div>
                </div>
            `).join('');
            this.els.historyList.querySelectorAll('.history-item').forEach(el => {
                el.addEventListener('click', () => {
                    const vid = parseInt(el.dataset.versionId);
                    this.previewVersion(vid);
                });
            });
        } catch (err) {
            console.error('Failed to load versions:', err);
            this.els.historyList.innerHTML = '<div class="history-empty">加载失败，请重试</div>';
        }
    }

    async previewVersion(versionId) {
        if (!this.currentNote) return;
        try {
            const result = await ApiClient.getVersion(this.currentNote.id, versionId);
            const v = result.version;
            this.currentPreviewVersion = v;
            this.els.versionPreviewTitle.textContent = `版本 #${v.id} - ${this.formatDate(v.created_at)}`;
            this.els.versionPreviewMeta.innerHTML = `
                <div><strong>修改时间:</strong> ${this.formatDate(v.created_at)}</div>
                <div><strong>修改者:</strong> ${v.modified_by || '未知用户'}</div>
                <div><strong>变更摘要:</strong> ${v.change_summary || '无变更说明'}</div>
            `;
            this.els.versionPreviewTitleContent.textContent = v.title || '（无标题）';
            this.els.versionPreviewBodyContent.textContent = v.content || '（无内容）';
            this.openModal(this.els.versionPreviewModal);
        } catch (err) {
            console.error('Failed to load version:', err);
            this.showToast('加载版本详情失败', 'error');
        }
    }

    async restoreCurrentVersion() {
        if (!this.currentPreviewVersion || !this.currentNote) return;
        const v = this.currentPreviewVersion;
        const msg = `确定要将笔记恢复到 ${this.formatDate(v.created_at)} 的版本吗？\n当前未保存的修改将丢失，此操作不可撤销。`;
        if (!confirm(msg)) return;

        try {
            const result = await ApiClient.restoreVersion(this.currentNote.id, v.id, true);
            this.showToast('版本回退成功', 'success');
            this.closeAllModals();
            await this.loadNote(this.currentNote.id);
            await Promise.all([
                this.loadNotes(),
                this.loadTags(),
                this.loadGraph()
            ]);
        } catch (err) {
            console.error('Failed to restore version:', err);
            this.showToast('版本回退失败: ' + (err.message || '未知错误'), 'error');
        }
    }

    async openShareModal() {
        if (!this.currentNote) {
            this.showToast('请先选择一个笔记', 'error');
            return;
        }
        this.els.sharePermission.value = 'read';
        this.els.shareExpiresDays.value = '';
        this.els.sharePassword.value = '';
        this.openModal(this.els.shareModal);
        await this.loadShares();
    }

    async loadShares() {
        if (!this.currentNote) return;
        try {
            const result = await ApiClient.getNoteShares(this.currentNote.id, true);
            const shares = result.shares || [];
            if (shares.length === 0) {
                this.els.shareList.innerHTML = '<div class="share-empty">暂无分享链接</div>';
                return;
            }
            this.els.shareList.innerHTML = shares.map(s => this.renderShareItem(s)).join('');
            this.bindShareItemEvents();
        } catch (err) {
            console.error('Failed to load shares:', err);
            this.els.shareList.innerHTML = '<div class="share-empty">加载失败</div>';
        }
    }

    renderShareItem(s) {
        const shareUrl = `${window.location.origin}/share/${s.share_token}`;
        const isValid = s.is_valid && s.is_active;
        const badges = [];
        badges.push(`<span class="share-badge ${s.permission}">${s.permission === 'read' ? '👁️ 只读' : '✏️ 可编辑'}</span>`);
        if (s.has_password) badges.push('<span class="share-badge protected">🔒 密码保护</span>');
        if (s.expires_at) badges.push(`<span class="share-badge expires">⏰ 有效期至 ${this.formatDate(s.expires_at)}</span>`);
        if (!isValid) badges.push('<span class="share-badge invalid">❌ 已失效</span>');

        return `
            <div class="share-item" data-share-id="${s.id}">
                <div class="share-item-header">
                    <div>
                        <div class="share-item-title">分享链接 #${s.id}</div>
                        <div class="share-item-token">Token: ${s.share_token.substring(0, 20)}...</div>
                    </div>
                    <div class="share-item-actions">
                        ${isValid ? `<button class="btn btn-small btn-danger" data-action="revoke">撤销</button>` : ''}
                        <button class="btn btn-small" data-action="delete">删除</button>
                    </div>
                </div>
                <div class="share-item-info">${badges.join('')}</div>
                <div class="share-item-info" style="font-size:12px;color:#86868b;">
                    创建于 ${this.formatDate(s.created_at)}
                </div>
                <div class="share-item-url">
                    <input type="text" class="share-url-input" value="${shareUrl}" readonly>
                    <button class="btn btn-small" data-action="copy">复制</button>
                    <button class="btn btn-small" data-action="open">打开</button>
                </div>
            </div>
        `;
    }

    bindShareItemEvents() {
        this.els.shareList.querySelectorAll('.share-item').forEach(item => {
            const shareId = item.dataset.shareId;
            item.querySelector('[data-action="copy"]')?.addEventListener('click', async () => {
                const input = item.querySelector('.share-url-input');
                try {
                    await navigator.clipboard.writeText(input.value);
                    this.showToast('链接已复制到剪贴板', 'success');
                } catch {
                    input.select();
                    document.execCommand('copy');
                    this.showToast('链接已复制', 'success');
                }
            });
            item.querySelector('[data-action="open"]')?.addEventListener('click', () => {
                const input = item.querySelector('.share-url-input');
                window.open(input.value, '_blank');
            });
            item.querySelector('[data-action="revoke"]')?.addEventListener('click', async () => {
                if (!confirm('确定要撤销此分享链接吗？撤销后链接将立即失效。')) return;
                try {
                    await ApiClient.revokeShare(shareId);
                    this.showToast('分享已撤销', 'success');
                    await this.loadShares();
                } catch (err) {
                    this.showToast('撤销失败', 'error');
                }
            });
            item.querySelector('[data-action="delete"]')?.addEventListener('click', async () => {
                if (!confirm('确定要删除此分享记录吗？')) return;
                try {
                    await ApiClient.deleteShare(shareId);
                    this.showToast('分享已删除', 'success');
                    await this.loadShares();
                } catch (err) {
                    this.showToast('删除失败', 'error');
                }
            });
        });
    }

    async createShare() {
        if (!this.currentNote) return;
        const permission = this.els.sharePermission.value;
        const expiresDaysRaw = this.els.shareExpiresDays.value.trim();
        const password = this.els.sharePassword.value.trim() || null;
        const expires_days = expiresDaysRaw ? parseInt(expiresDaysRaw, 10) : null;

        if (expiresDaysRaw && (isNaN(expires_days) || expires_days < 1 || expires_days > 365)) {
            this.showToast('有效期必须是 1-365 天之间的数字', 'error');
            return;
        }

        try {
            const share = await ApiClient.createShare(this.currentNote.id, {
                permission,
                password,
                expires_days
            });
            this.showToast('分享链接已创建', 'success');
            this.els.shareExpiresDays.value = '';
            this.els.sharePassword.value = '';
            await this.loadShares();
        } catch (err) {
            console.error('Failed to create share:', err);
            this.showToast('创建分享失败: ' + (err.message || '未知错误'), 'error');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new App();
});
