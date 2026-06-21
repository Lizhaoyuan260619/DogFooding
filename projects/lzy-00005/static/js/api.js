const API_BASE = '/api';

class ApiClient {
    static async request(url, options = {}) {
        const defaultHeaders = {
            'Content-Type': 'application/json'
        };
        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        });
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        if (!response.ok) {
            const err = new Error(data?.error || `HTTP error! status: ${response.status}`);
            err.status = response.status;
            err.data = data;
            throw err;
        }
        return data;
    }

    static async listNotes() {
        return this.request(`${API_BASE}/notes`);
    }

    static async getNote(id) {
        return this.request(`${API_BASE}/notes/${id}`);
    }

    static async createNote(data) {
        return this.request(`${API_BASE}/notes`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async updateNote(id, data) {
        return this.request(`${API_BASE}/notes/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async deleteNote(id) {
        return this.request(`${API_BASE}/notes/${id}`, {
            method: 'DELETE'
        });
    }

    static async listTags() {
        return this.request(`${API_BASE}/notes/tags`);
    }

    static async getNotesByTag(tagName) {
        return this.request(`${API_BASE}/notes/tags/${encodeURIComponent(tagName)}`);
    }

    static async getGraph() {
        return this.request(`${API_BASE}/graph`);
    }

    static async searchNotes(query) {
        return this.request(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
    }

    static async exportNote(id) {
        window.location.href = `${API_BASE}/export/${id}`;
    }

    static async exportAll() {
        window.location.href = `${API_BASE}/export`;
    }

    static async getNoteVersions(noteId, limit, offset) {
        let url = `${API_BASE}/notes/${noteId}/versions`;
        const params = new URLSearchParams();
        if (limit) params.set('limit', limit);
        if (offset) params.set('offset', offset);
        const qs = params.toString();
        if (qs) url += '?' + qs;
        return this.request(url);
    }

    static async getVersion(noteId, versionId) {
        return this.request(`${API_BASE}/notes/${noteId}/versions/${versionId}`);
    }

    static async restoreVersion(noteId, versionId, confirm = true) {
        return this.request(`${API_BASE}/notes/${noteId}/versions/${versionId}/restore`, {
            method: 'POST',
            body: JSON.stringify({ confirm })
        });
    }

    static async deleteVersion(noteId, versionId) {
        return this.request(`${API_BASE}/notes/${noteId}/versions/${versionId}`, {
            method: 'DELETE'
        });
    }

    static async listAllShares() {
        return this.request(`${API_BASE}/notes/shares`);
    }

    static async getNoteShares(noteId, includeInactive = false) {
        let url = `${API_BASE}/notes/${noteId}/shares`;
        if (includeInactive) url += '?include_inactive=true';
        return this.request(url);
    }

    static async createShare(noteId, data) {
        return this.request(`${API_BASE}/notes/${noteId}/shares`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async getShare(shareId) {
        return this.request(`${API_BASE}/notes/shares/${shareId}`);
    }

    static async revokeShare(shareId) {
        return this.request(`${API_BASE}/notes/shares/${shareId}/revoke`, {
            method: 'POST'
        });
    }

    static async deleteShare(shareId) {
        return this.request(`${API_BASE}/notes/shares/${shareId}`, {
            method: 'DELETE'
        });
    }

    static async accessSharedNote(shareToken, password) {
        let url = `${API_BASE}/notes/shared/${shareToken}`;
        if (password) {
            url += `?password=${encodeURIComponent(password)}`;
        }
        return this.request(url);
    }

    static async updateSharedNote(shareToken, data) {
        return this.request(`${API_BASE}/notes/shared/${shareToken}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
}

export default ApiClient;
