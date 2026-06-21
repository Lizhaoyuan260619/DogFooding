from flask import Blueprint, request, jsonify
from blueprints.search.services import SearchService

search_bp = Blueprint('search', __name__)

@search_bp.route('', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = SearchService.search_notes(query)
    for result in results:
        result['title'] = SearchService.highlight(result['title'], query)
        snippet = result['content'][:500]
        result['content'] = SearchService.highlight(snippet, query)
    return jsonify(results)
