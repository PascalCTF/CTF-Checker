from flask import Flask, request, render_template, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Checkers, Status
import os, pathlib, json, subprocess, zipfile, tempfile, datetime, csv

DATABASE_URL = f'mysql+mysqlconnector://{os.getenv("MYSQL_USER")}:{os.getenv("MYSQL_PASSWORD")}@db:3306/{os.getenv("MYSQL_DATABASE")}'

scheduler = BackgroundScheduler(daemon=True)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # 32MB

@app.route('/ping')
def ping():
    return 'pong', 200

# TODO: Implement the index.html template
@app.route('/')
def dashboard():
    session = Session()
    checkers = session.query(Checkers).all()
    status = []
    for check in checkers:
        status.append([
            check,
            session.query(Status).filter(
                Status.checker == check.id
            ).order_by(
                Status.date.desc()
            )[:50]
        ])

    return render_template('index.html', status=status)

@app.route('/status/<int:id>')
def status(id):
    #TODO: Implement this
    return 'Not implemented', 501

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    elif request.method == 'POST':
        file = request.files.get('file')
        if file and file.content_type == 'application/zip':
            temp_zip = None
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_zip = pathlib.Path(temp_dir, 'temp.zip')
                file.save(temp_zip)
            
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_extracted = pathlib.Path(temp_dir, 'extracted')
                    zip_ref.extractall(zip_extracted)
                
                for chal_folder in os.listdir(zip_extracted):
                    info_path = pathlib.Path(zip_extracted, chal_folder, 'info.json')
                    checker_path = pathlib.Path(zip_extracted, chal_folder, 'checker.py')

                    if not info_path.exists() or not checker_path.exists():
                        return f'Either info or checker not present in {chal_folder}', 400

                    info = json.loads(info_path.read_text())
                    tags = [
                        ['flag', str], 
                        ['points', int], 
                        ['category', str], 
                        ['description', str], 
                        ['name', str]
                    ]
                    for tag in tags:
                        if not tag[0] in info:
                            return f'No {tag} attribute in info in {chal_folder}', 400
                        if not isinstance(info[tag[0]], tag[1]):
                            return f'{tag} must be of type {tag[1]} in {chal_folder}', 400
                    
                    check = Checkers(
                        name=info['name'],
                        category=info['category'],
                        points=info['points'],
                        description=info['description'],
                        flag=info['flag'],
                        checker=checker_path.read_text().encode()
                    )
                    app.logger.info(f'Adding checker {check}')
                    session = Session()
                    session.add(check)
                    session.commit()
            return 'File uploaded successfully!', 200
        
        return render_template('upload.html')

# TODO: Test this route
@app.route('/export')
def export():
    session = Session()
    status = session.query(Status).all()
    with tempfile.TemporaryFile() as temp_file:
        writer = csv.writer(temp_file)
        writer.writerow(['id', 'checker', 'uptime', 'date'])
        for s in status:
            writer.writerow([s.id, s.checker, s.uptime, s.date])
        temp_file.seek(0)
        return send_file(temp_file, as_attachment=True, download_name='status.csv', mimetype='text/csv')

@scheduler.scheduled_job('interval', minutes=2)
def check_status():
    session = Session()
    for check in session.query(Checkers).all():
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(check.checker)
            result = subprocess.run(['python3'], stdin=temp_file, stdout=subprocess.PIPE)
        flags = result.stdout.decode().strip().split('\n')
        passed = flags.count(check.flag) / len(flags) * 100
        status = Status(checker=check.id, uptime=passed, date=datetime.datetime.now())
        session.add(status)
        session.commit()

if __name__ == '__main__':
    scheduler.start() # Flask debug must be False, otherwise the scheduler will run twice
    Base.metadata.create_all(engine)
    app.run(host='0.0.0.0', port=5000, debug=True)