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
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        return await response.text();
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
}

export default ApiClient;
