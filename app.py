import re
import os
from flask import Flask, render_template, request, session, Response
from flask_socketio import SocketIO, emit
import subprocess
import io
import threading

from dialogue_policy import conduct_interview, add_model_msg, Phase, summarize_interview, analyze_scale
from utils import *
from query_gpt import query
import db_access
import audio_service
import prompts
from asr import asr
from config import Config


app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(SECRET_KEY='DEV')
socketio = SocketIO(app)


@app.route('/interview')
def index():
    interview_id = generate_random_str()
    session['interview-id'] = interview_id
    scale_id = request.args['scale']
    phase = 'analysis'

    msgs = db_access.get_analysis_by_scale_id(scale_id)
    if msgs is None:  # scales created before database alteration

        scale = db_access.get_scale_by_scale_id(scale_id)
        scale = [i for i in scale.split() if i]
        scale = f'访谈量表：\n' + '\n'.join(f'\t"{i}",' for i in scale) + '\n接下来，进入分析状态。'
        msgs = [
            {'role': 'system', 'content': prompts.system},
            {'role': 'user', 'content': scale},
        ]
        analysis = query(msgs)
        add_model_msg(msgs, analysis)
        db_access.update_analysis(scale_id, msgs)

    db_access.insert_interview(interview_id, scale_id, msgs, phase)

    return render_template('chat.html', experiment_id=interview_id[:4].lower())


@app.route('/get', methods=['GET', 'POST'])
def chat():
    interview_id = session.get('interview-id')
    msgs, phase = db_access.get_msgs_and_phase(interview_id)
    user_msg = request.form['msg']

    model_msg, new_phase = conduct_interview(msgs, phase, user_msg)
    db_access.update_last_msg(interview_id, model_msg)

    db_access.update_msgs(interview_id, msgs)
    if new_phase != phase:
        db_access.update_phase(interview_id, new_phase)
    
    if new_phase == Phase.summary:
        report = summarize_interview(msgs)

        # try to load report with json
        db_access.update_report(interview_id, report)
        try:
            if re_match := re.match('```json(.+)```', report, re.S):
                report = re_match.group(1)
        except:
            pass
        db_access.update_report(interview_id, report)

        db_access.set_time_end(interview_id)
        phase = Phase.finished
        db_access.update_phase(interview_id, phase)
        
    return Response(audio_service.text_to_speech(model_msg), mimetype="audio/mp3")


@app.route('/create', methods=['GET', 'POST'])
def create():

    if request.method == 'GET':
        return render_template('create.html')
    
    elif request.method == 'POST':
        data = request.json
        scale = data['scale']
        scale_id = generate_random_str()
        results_id = generate_random_str()
        db_access.insert_scale(scale_id, results_id, scale)

        msgs = analyze_scale(scale)
        db_access.update_analysis(scale_id, msgs)
        
        response = {
            'interview_link': scale_id,
            'results_link': results_id,
            'analysis': msgs,
        }
        return response


@app.route('/model-response')
def get_latest_text_response():
    interview_id = session.get('interview-id')
    # msgs, _ = db_access.get_msgs_and_phase(interview_id)
    # model_msg = msgs[-1]['content']
    last_msg = db_access.get_last_msg(interview_id)

    return {
        'modelMsg': last_msg,
    }


@app.route('/recover')
def recover():
    interview_id = request.args['interview']
    session['interview-id'] = interview_id
    msgs, phase = db_access.get_msgs_and_phase(interview_id)
    if msgs[-1]['role'] == 'user':
        msgs.pop()
    return render_template('recover.html', experiment_id=interview_id[:4].lower(), messages=msgs[10:])


@app.route('/results')
def results():
    results_id = request.args['id']
    scale_id = db_access.get_scale_id_by_results_id(results_id)
    data = db_access.get_data_by_scale_id(scale_id)
    return render_template('results.html', results=data)


# @app.route('/asr', methods=['POST'])
# def get_text_from_speech():
#     if 'audio' in request.files:
#         audio_file = request.files['audio']
#         audio_file.save('asr.webm')
#         return 'Audio saved successfully'
#     return 'No audio file found in request'


@socketio.on('audio_data')
def handle_audio_data(data):
    print('audio_data received, ', len(data))

    process = subprocess.Popen(
        ['ffmpeg', '-i', '-', '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1', '-f', 'wav', 'pipe:1', '-loglevel', 'error'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    memory_buffer = io.BytesIO()

    def read_from_stdout():
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            memory_buffer.write(chunk)
        memory_buffer.seek(0)
    threading.Thread(target=read_from_stdout).start()

    process.stdin.write(data)
    process.stdin.close()

    process.wait()

    wav_data = memory_buffer.read()
    print(len(wav_data))
    print(type(wav_data))

    # keep_drain_stderr = False
    if error := process.stderr.read():
        print('ffmpeg error:', error.decode())
    

    text = asr(wav_data)
    print(text)
    emit('response', {'data': text})


@app.route('/interview_test')
def interview_test():
    return render_template('chat.html', experiment_id=0)


def main():
    env = os.getenv('INTERVIEWER_ENV', 'development')
    port = int(os.getenv('INTERVIEWER_PORT', Config.default_port))
    
    if env == 'development':
        socketio.run(app, debug=True)
    elif env == 'production':
        socketio.run(app, host='0.0.0.0', port=port, ssl_context=('./ssl/cert.pem', './ssl/key.pem'))


if __name__ == '__main__':
    main()
