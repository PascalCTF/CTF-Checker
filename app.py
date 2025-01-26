from flask import Flask, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import os, pathlib, json, subprocess

scheduler = BackgroundScheduler(daemon=True)

app = Flask(__name__)

@app.route('/ping')
def ping():
    return 'pong', 200

@app.route('/')
def dashboard():
    return render_template('index.html')

@scheduler.scheduled_job('interval', seconds=5)
def check_status():
    print('Checking status...')

    for chal_folder in os.listdir('chals'):
        info_path = pathlib.Path('chals', chal_folder, 'info.json')
        checker_path = pathlib.Path('chals', chal_folder, 'checker.py')
        
        info = json.loads(info_path.read_text())
        result = subprocess.run(['python3', checker_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.stdout.decode().strip() == info['flag']:
            print(f'Flag for {chal_folder} is correct!')
        else:
            print(f'Flag for {chal_folder} is incorrect!\nExprected: {info["flag"]}\nGot: {result.stdout.decode().strip()}')

if __name__ == '__main__':
    scheduler.start() # Flask debug must be False, otherwise the scheduler will run twice
    app.run(host='0.0.0.0', port=5000, debug=True)