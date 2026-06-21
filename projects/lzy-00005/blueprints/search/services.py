from models.note_repository import NoteRepository
import re

class SearchService:
    @staticmethod
    def search_notes(query):
        if not query or not query.strip():
            return []
        results = NoteRepository.search(query.strip())
        return results

    @staticmethod
    def highlight(text, query):
        if not query:
            return text
        escaped = re.escape(query)
        pattern = re.compile(f'({escaped})', re.IGNORECASE)
        return pattern.sub(r'<mark>\1</mark>', text)
