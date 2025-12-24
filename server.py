from flask import Flask, render_template_string, jsonify
import subprocess
import os
import signal

app = Flask(__name__)

bot_process = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord Bot Controller</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            margin-bottom: 10px;
            font-size: 2em;
        }
        .status {
            margin: 20px 0;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
        }
        .status.online {
            background: rgba(40, 167, 69, 0.3);
            border: 2px solid #28a745;
            color: #28a745;
        }
        .status.offline {
            background: rgba(220, 53, 69, 0.3);
            border: 2px solid #dc3545;
            color: #dc3545;
        }
        .buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 30px;
        }
        button {
            padding: 15px 40px;
            font-size: 1.1em;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            transform: scale(1.05);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .start-btn {
            background: #28a745;
            color: white;
        }
        .start-btn:hover:not(:disabled) {
            background: #218838;
            box-shadow: 0 0 20px rgba(40, 167, 69, 0.5);
        }
        .stop-btn {
            background: #dc3545;
            color: white;
        }
        .stop-btn:hover:not(:disabled) {
            background: #c82333;
            box-shadow: 0 0 20px rgba(220, 53, 69, 0.5);
        }
        .loading {
            display: none;
            margin-top: 20px;
        }
        .loading.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Discord Bot Controller</h1>
        <p>hia Bot</p>
        
        <div id="status" class="status offline">
            Offline
        </div>
        
        <div class="buttons">
            <button class="start-btn" onclick="startBot()">Start</button>
            <button class="stop-btn" onclick="stopBot()">Stop</button>
        </div>
        
        <div id="loading" class="loading">Bitte warten...</div>
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(res => res.json())
                .then(data => {
                    const statusEl = document.getElementById('status');
                    if (data.running) {
                        statusEl.textContent = 'Online';
                        statusEl.className = 'status online';
                    } else {
                        statusEl.textContent = 'Offline';
                        statusEl.className = 'status offline';
                    }
                });
        }

        function startBot() {
            document.getElementById('loading').classList.add('show');
            fetch('/start', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('loading').classList.remove('show');
                    updateStatus();
                });
        }

        function stopBot() {
            document.getElementById('loading').classList.add('show');
            fetch('/stop', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('loading').classList.remove('show');
                    updateStatus();
                });
        }

        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    global bot_process
    running = bot_process is not None and bot_process.poll() is None
    return jsonify({'running': running})

@app.route('/start', methods=['POST'])
def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        bot_process = subprocess.Popen(['python', 'bot.py'])
        return jsonify({'success': True, 'message': 'Bot gestartet'})
    return jsonify({'success': False, 'message': 'Bot läuft bereits'})

@app.route('/stop', methods=['POST'])
def stop_bot():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:
        bot_process.terminate()
        bot_process.wait()
        bot_process = None
        return jsonify({'success': True, 'message': 'Bot gestoppt'})
    return jsonify({'success': False, 'message': 'Bot läuft nicht'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
