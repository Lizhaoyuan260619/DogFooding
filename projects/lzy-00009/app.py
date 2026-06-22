"""
Flask Web应用 - 实体识别与情感分析可视化界面
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any

from flask import Flask, render_template, request, jsonify, send_from_directory

from text_analyzer.analyzer.entity_recognizer import EntityRecognizer
from text_analyzer.analyzer.sentiment_analyzer import SentimentAnalyzer
from text_analyzer.config import OUTPUT_DIR, BASE_DIR


app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

entity_recognizer = EntityRecognizer()
sentiment_analyzer = SentimentAnalyzer()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html',
                         entity_types=entity_recognizer.get_entity_type_info())


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """文本分析API - 实体识别 + 情感分析"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({
                'success': False,
                'error': '请输入要分析的文本内容'
            }), 400

        entity_result = entity_recognizer.recognize(text)
        sentiment_result = sentiment_analyzer.analyze(text)

        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'text': text,
            'entity_recognition': entity_result,
            'sentiment_analysis': sentiment_result
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'分析失败: {str(e)}'
        }), 500


@app.route('/api/entity', methods=['POST'])
def recognize_entity():
    """实体识别API"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({
                'success': False,
                'error': '请输入要分析的文本内容'
            }), 400

        result = entity_recognizer.recognize(text)
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            **result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'实体识别失败: {str(e)}'
        }), 500


@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
    """情感分析API"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({
                'success': False,
                'error': '请输入要分析的文本内容'
            }), 400

        result = sentiment_analyzer.analyze(text)
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            **result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'情感分析失败: {str(e)}'
        }), 500


@app.route('/api/entity-types')
def get_entity_types():
    """获取实体类型信息"""
    return jsonify(entity_recognizer.get_entity_type_info())


@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """批量文本分析"""
    try:
        data = request.get_json()
        texts = data.get('texts', [])

        if not texts or not isinstance(texts, list):
            return jsonify({
                'success': False,
                'error': '请提供文本列表'
            }), 400

        results = []
        for text in texts:
            if text and text.strip():
                entity_result = entity_recognizer.recognize(text)
                sentiment_result = sentiment_analyzer.analyze(text)
                results.append({
                    'text': text,
                    'entity_recognition': entity_result,
                    'sentiment_analysis': sentiment_result
                })

        sentiment_dist = sentiment_analyzer.get_sentiment_distribution(texts)

        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(results),
            'results': results,
            'sentiment_distribution': sentiment_dist
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'批量分析失败: {str(e)}'
        }), 500


@app.route('/output/<path:filename>')
def serve_output(filename):
    """提供输出文件访问"""
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'services': {
            'entity_recognition': 'ready',
            'sentiment_analysis': 'ready'
        }
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API端点不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("  实体识别与情感分析系统")
    print("  Entity Recognition & Sentiment Analysis System")
    print("=" * 60)
    print(f"  服务地址: http://localhost:5000")
    print(f"  API文档: http://localhost:5000/api/health")
    print("=" * 60)
    print("  按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
