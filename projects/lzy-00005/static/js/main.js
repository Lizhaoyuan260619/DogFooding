import ApiClient from './api.js';
import GraphRenderer from './graph-renderer.js';

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
            tabContents: document.querySelectorAll('.tab-content')
        };
    }

    bindEvents() {
        this.els.newNoteBtn.addEventListener('click', () => this.createNewNote());
        this.els.saveNoteBtn.addEventListener('click', () => this.saveCurrentNote());
        this.els.deleteNoteBtn.addEventListener('click', () => this.deleteCurrentNote());
        this.els.exportNoteBtn.addEventListener('click', () => this.exportCurrentNote());

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
        } catch (err) {
            console.error('Failed to load note:', err);
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

    async deleteCurrentNote() {
        if (!this.currentNote) {
            this.showEmptyState();
            return;
        }
        if (!confirm(`确定要删除笔记「${this.currentNote.title}」吗？`)) {
            return;
        }
        try {
            await ApiClient.deleteNote(this.currentNote.id);
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
}

document.addEventListener('DOMContentLoaded', () => {
    new App();
});
