import os
import json

def get_secret_key(filename='secrets.json', key='SECRET_KEY'):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        with open(file_path, 'r') as file:
            secrets = json.load(file)
        return secrets.get(key)
    except FileNotFoundError:
        print(f"ERROR : {filename} 파일을 찾을 수 없음.")
        return None
    except json.JSONDecodeError:
        print(f"ERROR : {filename} 파일은 유효한 JSON 형식이 아님.")
        return None