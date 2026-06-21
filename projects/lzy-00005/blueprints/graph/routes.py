from flask import Blueprint, jsonify
from blueprints.graph.services import GraphService

graph_bp = Blueprint('graph', __name__)

@graph_bp.route('', methods=['GET'])
def get_graph():
    data = GraphService.get_graph_data()
    return jsonify(data)
