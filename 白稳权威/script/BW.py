import yaml
import sys
import re
from tqdm import tqdm
import os
import importlib.util
import argparse
def load_yaml_config(config_path):

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"错误: 配置文件 '{config_path}' 未找到。")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"错误: 解析 YAML 配置文件时出错: {e}")
        sys.exit(1)
def load_py_config(config_path):

    try:
        spec = importlib.util.spec_from_file_location("config_module", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"错误: 导入 Python 配置文件时出错: {e}")
        sys.exit(1)
def get_available_configs():

    configs = {}
    if os.path.exists('美化配置.yaml'):
        configs['yaml'] = '美化配置.yaml'
    if os.path.exists('美化配置.py'):
        configs['py'] = '美化配置.py'
    return configs
def select_config(configs):

    print("检测到多个配置文件:")
    for key, path in configs.items():
        if key == 'yaml':
            print(f"  [1] {path}")
        elif key == 'py':
            print(f"  [2] {path}")
    while True:
        choice = input("请选择要使用的配置文件 (请输入1或2)，输入'exit'退出 :").strip()
        if choice.lower() == 'exit':
            print("已退出。")
            sys.exit(0)
        elif choice == '1' and 'yaml' in configs:
            return 'yaml'
        elif choice == '2' and 'py' in configs:
            return 'py'
        else:
            print("无效的选择，请重新输入。")
def parse_arguments():
    parser = argparse.ArgumentParser(description="美化文件脚本")
    parser.add_argument('--config', type=str, help='配置文件路径', default=None)
    parser.add_argument('--type', type=str, choices=['yaml', 'py'], help='配置文件类型', default=None)
    return parser.parse_args()
def decimal_to_hex_little_endian(number):

    hex_str = number.to_bytes(4, byteorder='little').hex()
    return hex_str
def swap_hex_bytes(content, hex1, hex2):

    bytes1 = bytes.fromhex(hex1)
    bytes2 = bytes.fromhex(hex2)
    indices1 = [m.start() for m in re.finditer(re.escape(bytes1), content)]
    indices2 = [m.start() for m in re.finditer(re.escape(bytes2), content)]
    if len(indices1) == 0 or len(indices2) == 0:
        return content, False  # 返回 False 表示未互换成功
    swap_count = min(len(indices1), len(indices2))
    new_content = bytearray(content)
    for i in range(swap_count):
        index1 = indices1[i]
        index2 = indices2[i]
        len1 = len(bytes1)
        len2 = len(bytes2)
        if len1 != len2:
            print(f"错误: 十六进制值 '{hex1}' 和 '{hex2}' 的字节长度不同，无法互换。")
            return content, False  # 返回 False 表示未互换成功
        new_content[index1:index1 + len1] = bytes2
        new_content[index2:index2 + len2] = bytes1
    return new_content, True  # 返回 True 表示互换成功
def main():
    args = parse_arguments()
    if args.config and args.type:
        config_path = args.config
        config_type = args.type
    else:
        configs = get_available_configs()
        if not configs:
            print("错误: 没有找到任何配置文件（美化配置.yaml 或 美化配置.py）。")
            sys.exit(1)
        elif len(configs) == 1:
            config_type = list(configs.keys())[0]
            config_path = configs[config_type]
        else:
            config_type = select_config(configs)
            config_path = configs[config_type]
    if config_type == 'py':
        config = load_py_config(config_path)
        if config is None:
            config_type = 'yaml'
            config_path = '美化配置.yaml'
            config = load_yaml_config(config_path)
    else:
        config = load_yaml_config(config_path)
    if config_type == 'yaml':
        file_path = config.get('file_path')
        swap_pairs = config.get('swap_pairs', [])
    else:
        file_path = config.file_path
        swap_pairs = config.swap_pairs
    if not swap_pairs:
        print("错误: 没有定义任何十进制数对进行转换和互换。")
        sys.exit(1)
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        failed_pairs = []
        for dec1, dec2 in tqdm(swap_pairs, desc="美化进度", unit="对", 
                               bar_format="{l_bar}{bar} {n_fmt}/{total_fmt} [{elapsed}]", 
                               colour="green"):
            hex1 = decimal_to_hex_little_endian(dec1)
            hex2 = decimal_to_hex_little_endian(dec2)
            content, swapped = swap_hex_bytes(content, hex1, hex2)
            if not swapped:
                failed_pairs.append((dec1, dec2))
        with open(file_path, 'wb') as file:
            file.write(content)
        print(f"成功修改美化文件 '{file_path}' ")
        if failed_pairs:
            print("\n以下值未修改完成请查看配置是否错误：")
            for dec1, dec2 in failed_pairs:
                print(f"{dec1} ☞ {dec2}")
        else:
            print("\n所有美化值均已成功修改。")
    except FileNotFoundError:
        print(f"错误: 文件 '{file_path}' 未找到。")
    except Exception as e:
        print(f"发生错误: {e}")
if __name__ == "__main__":
    main()