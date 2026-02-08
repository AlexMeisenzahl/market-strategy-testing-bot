"""
Leaderboard Routes

API routes for strategy competition leaderboard.
"""

from flask import Blueprint, jsonify, request
import logging

from services.strategy_competition import competition
from services.performance_tracker import performance_tracker
from database.competition_models import Strategy

logger = logging.getLogger(__name__)

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/api/leaderboard')


@leaderboard_bp.route('/', methods=['GET'])
def get_leaderboard():
    """Get strategy leaderboard"""
    try:
        leaderboard = competition.get_leaderboard()
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@leaderboard_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get competition summary"""
    try:
        summary = competition.get_competition_summary()
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@leaderboard_bp.route('/performance/<strategy_name>', methods=['GET'])
def get_strategy_performance(strategy_name):
    """Get historical performance for a strategy"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        history = performance_tracker.get_historical_performance(strategy_name, hours)
        return jsonify({
            'success': True,
            'strategy': strategy_name,
            'history': history
        })
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@leaderboard_bp.route('/stats', methods=['GET'])
def get_realtime_stats():
    """Get real-time statistics"""
    try:
        stats = performance_tracker.get_real_time_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting realtime stats: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
