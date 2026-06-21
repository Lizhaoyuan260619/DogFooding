from models.note_repository import NoteRepository
from models.tag_repository import TagRepository
from models.link_repository import LinkRepository

class NoteService:
    @staticmethod
    def get_all_notes():
        notes = NoteRepository.get_all()
        for note in notes:
            note['tags'] = TagRepository.get_note_tags(note['id'])
            note['outgoing_links'] = LinkRepository.get_outgoing_links(note['id'])
            note['incoming_links'] = LinkRepository.get_incoming_links(note['id'])
        return notes

    @staticmethod
    def get_note(note_id):
        note = NoteRepository.get_by_id(note_id)
        if not note:
            return None
        note['tags'] = TagRepository.get_note_tags(note_id)
        note['outgoing_links'] = LinkRepository.get_outgoing_links(note_id)
        note['incoming_links'] = LinkRepository.get_incoming_links(note_id)
        return note

    @staticmethod
    def create_note(title, content='', tags=None):
        note = NoteRepository.create(title, content)
        if tags:
            TagRepository.set_note_tags(note['id'], tags)
        LinkRepository.update_links(note['id'], content)
        return NoteService.get_note(note['id'])

    @staticmethod
    def update_note(note_id, title=None, content=None, tags=None):
        note = NoteRepository.update(note_id, title, content)
        if not note:
            return None
        if tags is not None:
            TagRepository.set_note_tags(note_id, tags)
        if content is not None:
            LinkRepository.update_links(note_id, content)
        return NoteService.get_note(note_id)

    @staticmethod
    def delete_note(note_id):
        return NoteRepository.delete(note_id)

    @staticmethod
    def get_all_tags():
        return TagRepository.get_all()

    @staticmethod
    def get_notes_by_tag(tag_name):
        notes = NoteRepository.get_by_tag(tag_name)
        for note in notes:
            note['tags'] = TagRepository.get_note_tags(note['id'])
        return notes
