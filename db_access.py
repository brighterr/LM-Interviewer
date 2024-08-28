import sqlite3
from datetime import datetime
import json


def connect_db():
    conn = sqlite3.connect('interviewer.sqlite')
    c = conn.cursor()
    return conn, c


# ------------------------------------------------------------------------------
# scales
# ------------------------------------------------------------------------------


def create_scales_table():
    conn, c = connect_db()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS scales (
            scale_id TEXT PRIMARY KEY,
            results_id TEXT,
            scale TEXT,
            analysis TEXT,
            UNIQUE(results_id)
        )
        '''
    )
    c.execute('CREATE INDEX IF NOT EXISTS results_index ON scales (results_id)')
    conn.commit()


def insert_scale(scale_id, results_id, scale):
    conn, c = connect_db()
    try:
        c.execute(
            'INSERT INTO scales (scale_id, results_id, scale) VALUES (?, ?, ?)',
            (scale_id, results_id, scale)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print("Error: 数据已存在。")


def get_scale_by_scale_id(scale_id):
    _, c = connect_db()
    c.execute(
        'SELECT scale FROM scales WHERE scale_id = ?',
        (scale_id,)
    )
    return c.fetchone()[0]


def update_analysis(scale_id, analysis):
    conn, c = connect_db()
    analysis = json.dumps(analysis, ensure_ascii=False)
    try:
        c.execute(
            'UPDATE scales SET analysis = ? WHERE scale_id = ?',
            (analysis, scale_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print("Error: 数据已存在。")


def get_analysis_by_scale_id(scale_id):
    _, c = connect_db()
    c.execute(
        'SELECT analysis FROM scales WHERE scale_id = ?',
        (scale_id,)
    )
    analysis = c.fetchone()[0]
    if analysis is not None:
        analysis = json.loads(analysis)
    return analysis


def get_scale_id_by_results_id(results_id):
    _, c = connect_db()
    c.execute(
        'SELECT scale_id FROM scales WHERE results_id = ?',
        (results_id,)    
    )
    result = c.fetchone()
    if result:
        return result[0]
    return None


# ------------------------------------------------------------------------------
# interviews
# ------------------------------------------------------------------------------


def create_interviews_table():
    conn, c = connect_db()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS interviews (
            interview_id TEXT PRIMARY KEY,
            scale_id TEXT,
            msgs TEXT,
            phase TEXT,
            report TEXT DEFAULT NULL,
            time_begin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_end TIMESTAMP DEFAULT NULL,
            last_msg TEXT DEFAULT NULL
        )
        '''
    )
    c.execute('CREATE INDEX IF NOT EXISTS scale_index ON interviews (scale_id)')
    conn.commit()


def insert_interview(interview_id, scale_id, msgs, phase):
    conn, c = connect_db()
    msgs = json.dumps(msgs, ensure_ascii=False)
    print(interview_id + '=' * 10)
    c.execute('''
            INSERT INTO interviews (interview_id, scale_id, msgs, phase)
            VALUES (?, ?, ?, ?)
        ''',
        (interview_id, scale_id, msgs, phase)
    )
    conn.commit()


def get_msgs_and_phase(interview_id):
    _, c = connect_db()
    c.execute(
        'SELECT msgs, phase FROM interviews WHERE interview_id = ?',
        (interview_id,)
    )
    msgs, phase = c.fetchone()
    msgs = json.loads(msgs)
    return msgs, phase


def update_msgs(interview_id, msgs):
    conn, c = connect_db()
    msgs = json.dumps(msgs, ensure_ascii=False)
    c.execute(
        'UPDATE interviews SET msgs = ? WHERE interview_id = ?',
        (msgs, interview_id)
    )
    conn.commit()


def update_phase(interview_id, phase):
    conn, c = connect_db()
    c.execute(
        'UPDATE interviews SET phase = ? WHERE interview_id = ?',
        (phase, interview_id)
    )
    conn.commit()


def update_report(interview_id, report):
    conn, c = connect_db()
    c.execute(
        'UPDATE interviews SET report = ? WHERE interview_id = ?',
        (report, interview_id)
    )
    conn.commit()


def set_time_end(interview_id):
    conn, c = connect_db()
    now = datetime.now()
    c.execute(
        # 'UPDATE interviews SET time_end = ? WHERE interview_id = ?',
        # (now, interview_id)
        'UPDATE interviews SET time_end = CURRENT_TIMESTAMP WHERE interview_id = ?',
        (interview_id,)
    )
    conn.commit()


def get_data_by_scale_id(scale_id):
    
    _, c = connect_db()
    c.execute(
        'SELECT interview_id, msgs, phase, report, time_begin, time_end FROM interviews WHERE scale_id = ? and phase = "finished"',
        (scale_id,)
    )
    results = c.fetchall()

    result_dicts = []
    for i in results:
        try:
            report = json.loads(i[3])
        except:
            report = i[3]
        result_dicts.append({
            'interview_id': i[0],
            'msgs': json.loads(i[1]),
            'phase': i[2],
            'report': report,
            'time_begin': i[4],
            'time_end': i[5],
        })
    
    return result_dicts


def update_last_msg(interview_id, last_msg):
    conn, c = connect_db()
    c.execute(
        'UPDATE interviews SET last_msg = ? WHERE interview_id = ?',
        (last_msg, interview_id)
    )
    conn.commit()


def get_last_msg(interview_id):
    _, c = connect_db()
    c.execute(
        'SELECT last_msg FROM interviews WHERE interview_id = ?',
        (interview_id,)
    )
    return c.fetchone()[0]


create_scales_table()
create_interviews_table()