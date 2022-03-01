import yaml


def read_config(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        result = yaml.load(f.read(), Loader=yaml.FullLoader)
    f.close()
    return result
