import re

from query_gpt import query
import prompts


def new_sys_msg(content):
    return {
        'role': 'system',
        'content': content,
    }


def new_usr_msg(content):
    return {
        'role': 'user',
        'content': content,
    }


def new_ast_msg(content):
    return {
        'role': 'assistant',
        'content': content,
    }


def add_user_msg(msgs, user_msg):
    msgs.append(new_usr_msg(user_msg))


def add_model_msg(msgs, model_msg):
    msgs.append(new_ast_msg(model_msg))


def polish(msg):
    # print(f'msg before polish: {msg}')
    # msg = re.sub(r'(?<=？).*', '', msg)
    # print(f'msg after polish: {msg}')
    return msg
    # msgs = [
    #     {
    #         'role': 'system',
    #         'content': '你是一位资深教育学学者，对于访谈有非常深入和独到的经验。现在,请帮助我进行一次访谈.我希望你能改进我对访谈对象的提问，在保持提问内容不变的同时，让提问变得充满鼓励、关切，并且要点突出。请注意，你给出的改写结果最多包括一个问题。下面我将给出我的提问，直接输出你的改进结果即可。'
    #     },
    #     {
    #         'role': 'user',
    #         'content': msg
    #     }
    # ]
    # return query(msgs)

    
class Phase:
    analysis  = 'analysis'
    interview = 'interview'
    summary   = 'summary'
    finished  = 'finished'


# def analyze_scale(scale):
#     # TODO: remove analyze or simplify it
#     msgs = [
#             {'role': 'system', 'content': prompts.system},
#             {'role': 'user', 'content': scale},
#         ]
#     analysis = query(msgs)
#     add_model_msg(msgs, analysis)
#     return msgs


# def analyze_scale_new(scale):
def analyze_scale(scale):
    msgs = [
        new_sys_msg(prompts.system),
        new_usr_msg(scale + '\n' + prompts.analyze_1)
    ]
    add_model_msg(msgs, query(msgs))
    
    for i in (prompts.analyze_2, prompts.analyze_3, prompts.analyze_4):
        add_user_msg(msgs, i)
        add_model_msg(msgs, query(msgs))
    
    return msgs


def conduct_interview(msgs, phase, user_msg):

    if phase == Phase.analysis:
        add_user_msg(msgs, prompts.start_interview)
        model_msg = query(msgs)

        # remove signal
        model_msg = re.search('.*提问状态.*?：(.+)', model_msg, re.S).group(1).strip()
        model_msg = polish(model_msg)
        add_model_msg(msgs, model_msg)

        phase = Phase.interview

    elif phase == Phase.interview:
        add_user_msg(msgs, user_msg)
        model_msg = query(msgs)

        if '转换到总结状态' not in model_msg:
            model_msg = polish(model_msg)
            add_model_msg(msgs, model_msg)
            # db_access.update_msgs(interview_id, msgs)
        else:
            add_model_msg(msgs, model_msg)
            model_msg = '访谈已完成，感谢您的参与！'
            phase = Phase.summary
    else:
        model_msg = '访谈已完成，感谢您的参与！'

    return model_msg, phase


def summarize_interview(msgs):
    add_user_msg(msgs, prompts.summarize)
    return query(msgs)
