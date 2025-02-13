import re
import os
from flask import Flask, render_template, request, session, Response, redirect, url_for
from flask_socketio import SocketIO, emit
import threading

from dialogue_policy import conduct_interview, add_model_msg, Phase, summarize_interview, analyze_scale
from utils import *
from query_gpt import query
import db_access
import prompts
from config import Config

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(SECRET_KEY='DEV')
socketio = SocketIO(app)


@app.route('/')
def home():
    scale_id = 0  # 你可以设置为某个预定义的默认量表ID
    interview_id = generate_random_str()
    session['interview-id'] = interview_id
    phase = 'analysis'

    # 获取分析信息，假设这里的 scale_id 是默认的
    msgs = db_access.get_analysis_by_scale_id(scale_id)
    
    if msgs is None:  # 如果数据库查询返回 None
        # 没有找到分析数据，进行一些默认处理，比如从数据库获取量表信息并生成消息
        scale = db_access.get_scale_by_scale_id(scale_id)
        if scale is None:
            scale = "默认访谈量表内容"  # 如果也没有找到量表，使用默认的内容
        
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

    # 跳转到访谈页面并传递访谈ID
    return redirect(url_for('index', scale=scale_id))


@app.route('/interview')
def index():
    # 获取 interview_id，若没有则生成默认值
    interview_id = session.get('interview-id', generate_random_str())
    
    # 获取 scale_id 参数，若没有传递则设置默认值
    scale_id = request.args.get('scale', 'default_scale')  # 设置 'default_scale' 作为默认值
    
    if not scale_id:
        return "Missing 'scale' parameter", 400  # 如果没有传递 scale 参数，返回错误

    phase = 'analysis'
    
    # 获取分析信息
    msgs = db_access.get_analysis_by_scale_id(scale_id)
    
    if msgs is None:  # scales created before database alteration
        scale = db_access.get_scale_by_scale_id(scale_id)
        if scale is None:
            scale = "默认访谈量表内容"  # 如果也没有找到量表，使用默认的内容
        
        scale = [i for i in scale.split() if i]
        scale = f'访谈量表：\n' + '\n'.join(f'\t"{i}",' for i in scale) + '\n接下来，进入分析状态。'
        
        msgs = [
            {'role': 'system', 'content': prompts.system},
            {'role': 'user', 'content': scale},
        ]
        
        # 生成分析内容并更新数据库
        analysis = query(msgs)
        add_model_msg(msgs, analysis)
        db_access.update_analysis(scale_id, msgs)

    db_access.insert_interview(interview_id, scale_id, msgs, phase)

    return render_template('chat.html', experiment_id=interview_id[:4].lower())



@app.route('/get', methods=['GET', 'POST'])
def chat():
    interview_id = session.get('interview-id')
    msgs, phase = db_access.get_msgs_and_phase(interview_id)
    user_msg = request.form.get('msg')  # 使用 get() 获取参数，避免 KeyError

    if user_msg:
        model_msg, new_phase = conduct_interview(msgs, phase, user_msg)
        db_access.update_last_msg(interview_id, model_msg)

        db_access.update_msgs(interview_id, msgs)
        if new_phase != phase:
            db_access.update_phase(interview_id, new_phase)
        
        if new_phase == Phase.summary:
            report = summarize_interview(msgs)
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
    else:
        return "Missing 'msg' parameter", 400  # 如果没有传递 msg 参数，返回错误


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return render_template('create.html')
    
    elif request.method == 'POST':
        data = request.json
        scale = data.get('scale')  # 使用 get() 来获取参数，避免 KeyError
        if not scale:
            return "Missing 'scale' in request", 400  # 如果没有传递 'scale' 参数，返回错误

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
    last_msg = db_access.get_last_msg(interview_id)

    return {
        'modelMsg': last_msg,
    }


@app.route('/recover')
def recover():
    interview_id = request.args.get('interview')  # 使用 get() 获取参数，避免 KeyError
    if not interview_id:
        return "Missing 'interview' parameter", 400  # 如果没有传递 'interview' 参数，返回错误

    session['interview-id'] = interview_id
    msgs, phase = db_access.get_msgs_and_phase(interview_id)
    if msgs[-1]['role'] == 'user':
        msgs.pop()
    return render_template('recover.html', experiment_id=interview_id[:4].lower(), messages=msgs[10:])


@app.route('/results')
def results():
    results_id = request.args.get('id')  # 使用 get() 获取参数，避免 KeyError
    if not results_id:
        return "Missing 'id' parameter", 400  # 如果没有传递 'id' 参数，返回错误

    scale_id = db_access.get_scale_id_by_results_id(results_id)
    data = db_access.get_data_by_scale_id(scale_id)
    return render_template('results.html', results=data)


def main():
    env = os.getenv('INTERVIEWER_ENV', 'development')
    port = int(os.getenv('INTERVIEWER_PORT', Config.default_port))
    
    if env == 'development':
        socketio.run(app, debug=True)
    elif env == 'production':
        socketio.run(app, host='0.0.0.0', port=port, ssl_context=('./ssl/cert.pem', './ssl/key.pem'))


if __name__ == '__main__':
    main()
