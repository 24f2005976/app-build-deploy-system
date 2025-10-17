from flask import Flask, request, jsonify
import os
import sys
from datetime import datetime

# Add the database directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
from database import DatabaseManager

app = Flask(__name__)

# Initialize database
db = DatabaseManager(os.path.join(os.path.dirname(__file__), '..', 'database', 'evaluation.db'))

@app.route('/api/notify', methods=['POST'])
def receive_notification():
    """Receive repo submission notifications from students"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'task', 'round', 'nonce', 'repo_url', 'commit_sha', 'pages_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if matching task exists
        tasks = db.get_tasks(email=data['email'], round_num=data['round'])
        matching_task = None
        
        for task in tasks:
            if (task['task'] == data['task'] and 
                task['nonce'] == data['nonce']):
                matching_task = task
                break
        
        if not matching_task:
            return jsonify({
                'error': 'No matching task found for the provided email, task, round, and nonce'
            }), 400
        
        # Insert repo submission
        repo_data = {
            'email': data['email'],
            'task': data['task'],
            'round': data['round'],
            'nonce': data['nonce'],
            'repo_url': data['repo_url'],
            'commit_sha': data['commit_sha'],
            'pages_url': data['pages_url']
        }
        
        success = db.insert_repo(repo_data)
        
        if success:
            print(f"Received repo submission from {data['email']} for task {data['task']} round {data['round']}")
            return jsonify({'status': 'success', 'message': 'Repo submission received'}), 200
        else:
            return jsonify({'error': 'Failed to store repo submission'}), 500
            
    except Exception as e:
        print(f"Error in receive_notification: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get evaluation results"""
    try:
        email = request.args.get('email')
        task = request.args.get('task')
        
        results = db.get_results(email=email, task=task)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        print(f"Error in get_results: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get tasks"""
    try:
        email = request.args.get('email')
        round_num = request.args.get('round', type=int)
        
        tasks = db.get_tasks(email=email, round_num=round_num)
        
        return jsonify({
            'status': 'success',
            'tasks': tasks,
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        print(f"Error in get_tasks: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/repos', methods=['GET'])
def get_repos():
    """Get repo submissions"""
    try:
        email = request.args.get('email')
        round_num = request.args.get('round', type=int)
        
        repos = db.get_repos(email=email, round_num=round_num)
        
        return jsonify({
            'status': 'success',
            'repos': repos,
            'count': len(repos)
        }), 200
        
    except Exception as e:
        print(f"Error in get_repos: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected'
    }), 200

if __name__ == '__main__':
    print("Starting evaluation API server...")
    print("Database location:", os.path.join(os.path.dirname(__file__), '..', 'database', 'evaluation.db'))
    app.run(debug=True, host='0.0.0.0', port=5001)