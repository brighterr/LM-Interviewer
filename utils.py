import json
import random
import string


def read_log(log_name):
    with open('./logs/' + log_name, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def write_log(log_name, data):
    with open('./logs/' + log_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def log_err(err, experiment_id, data=None):
    print(experiment_id, err, data)
    with open('./logs/error.log', 'a', encoding='utf-8') as f:
        f.write(f'{experiment_id}: {err}, {data=}\n')


def generate_random_str():
    chars = string.ascii_letters + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(8))
    # random_str = ''.join(secrets.choice(chars) for _ in range(8))
    return random_str
