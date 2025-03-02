import yaml
import sys
import re
from tqdm import tqdm
import os
import random
import ast

def decimal_to_little_endian_hex(decimal_number, byte_length=4):
    little_endian_bytes = decimal_number.to_bytes(byte_length, byteorder='little', signed=True)
    hex_string = little_endian_bytes.hex()
    return hex_string

def search_hex_positions(file_path, target_hex):

    byte_pattern = bytes.fromhex(target_hex)
    positions = []
    with open(file_path, 'rb') as f:
        data = f.read()
        offset = 0
        while True:
            pos = data.find(byte_pattern, offset)
            if pos == -1:
                break
            positions.append(pos)
            offset = pos + 1
    return positions

def find_closest_positions(positions, target_position):
    closest_positions = []
    for pos in positions:
        closest_positions.append((pos, abs(pos - target_position)))
    
    closest_positions.sort(key=lambda x: x[1])
    return closest_positions[:2]

def find_middle_value(file_path, start_pos, end_pos):

    with open(file_path, 'rb') as f:
        f.seek(start_pos + 4)  
        middle_data = f.read(end_pos - (start_pos + 4))
        return middle_data.hex()

def write_middle_value(file_path, start_pos, end_pos, new_middle_value):

    with open(file_path, 'rb') as f:
        data = bytearray(f.read())

    
    middle_length = end_pos - (start_pos + 4)
    new_middle_bytes = bytes.fromhex(new_middle_value)
    if len(new_middle_bytes) != middle_length:
        raise ValueError("新的中间值长度与原中间值长度不匹配。")

    
    data[start_pos + 4:end_pos] = new_middle_bytes

    
    with open(file_path, 'wb') as f:
        f.write(data)

def load_yaml_config(config_file):

    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_py_config(config_file):

    with open(config_file, 'r', encoding='utf-8') as f:
        py_code = f.read()
        
        local_vars = {}
        exec(py_code, {}, local_vars)
        
        
        config = {
            'source_folder': local_vars.get('source_folder'),
            'output_folder': local_vars.get('output_folder'),
            'target_markers': local_vars.get('target_markers'),
            'search_values': local_vars.get('search_values', [])
        }
        
        
        if not config['output_folder']:
            raise ValueError("Python 配置文件中未找到 'output_folder'。")
        if not config['target_markers']:
            raise ValueError("Python 配置文件中的 'target_markers' 未定义。")
        if not config['search_values']:
            raise ValueError("Python 配置文件中的 'search_values' 未定义。")
        
        return config

def load_config(config_file):

    if config_file.endswith('.yaml'):
        return load_yaml_config(config_file)
    elif config_file.endswith('.py'):
        return load_py_config(config_file)
    else:
        raise ValueError("不支持的配置文件类型。仅支持 .yaml 和 .py 配置文件。")

def swap_middle_values(middle_values):    
    swapped = middle_values[::-1]
    
    
    
    

    return swapped

def find_dat_file_with_target(output_folder, target_hex):
    
    target_byte = bytes.fromhex(target_hex)
    for file_name in os.listdir(output_folder):
        if file_name.endswith(''):
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, 'rb') as f:
                data = f.read()
                if target_byte in data:
                    return file_path
    return None

def process_targets(config):

    search_values = config.get('search_values', [])
    output_folder = config.get('output_folder')
    target_markers = config.get('target_markers', {})

    if not output_folder:
        print("错误: 未在配置文件中找到 'output_folder'。")
        sys.exit(1)

    if not target_markers:
        print("错误: 未在配置文件中找到 'target_markers'。")
        sys.exit(1)

    
    e578 = target_markers.get('特征值1')
    d978 = target_markers.get('特征值2')

    if not e578 or not d978:
        print("错误: '特征值1' 或 '特征值2' 未在 'target_markers' 中定义。")
        sys.exit(1)

    for target_list in search_values:
        middle_values = []
        for decimal_number in target_list:
            byte_length = 4  
            target_hex = decimal_to_little_endian_hex(decimal_number, byte_length)
            print(f"\n转 {decimal_number}，为: {target_hex}")

            
            dat_file_path = find_dat_file_with_target(output_folder, target_hex)
            if not dat_file_path:
                print(f"未找到包含美化值 '{target_hex}' 的 .dat 文件。")
                continue

            print(f"找到包含 '{target_hex}' 的文件: {dat_file_path}")

            
            target_hexes = [e578, d978]
            all_positions = {}
            for hex_str in target_hexes:
                positions = search_hex_positions(dat_file_path, hex_str)
                all_positions[hex_str] = positions
                print(f"找到 {len(positions)} 个 '{hex_str}' 的位置。")

            
            if not all_positions[e578] or not all_positions[d978]:
                print(f"文件 '{dat_file_path}' 中缺少 '{e578}' 或 '{d978}'，跳过。")
                continue

            
            target_positions = search_hex_positions(dat_file_path, target_hex)
            if not target_positions:
                print(f"未找到美化值 '{target_hex}' 的位置。")
                continue

            
            target_position = target_positions[0]
            print(f"美化值 '{target_hex}' 的位置: {target_position}")

            
            closest_positions = {}
            for hex_str in target_hexes:
                positions = all_positions[hex_str]
                closest = find_closest_positions(positions, target_position)
                closest_positions[hex_str] = closest

            
            for hex_str, closest in closest_positions.items():
                for pos, diff in closest:
                    print(f"'{hex_str}' 位置: {pos}, 差值: {diff}")

            
            
            e578_pos, e578_diff = closest_positions[e578][0]
            d978_pos, d978_diff = closest_positions[d978][0]

            
            if e578_pos < d978_pos:
                start_pos = e578_pos
                end_pos = d978_pos
            else:
                start_pos = d978_pos
                end_pos = e578_pos

            
            middle_value = find_middle_value(dat_file_path, start_pos, end_pos)
            print(f"要修改的值 (从位置 {start_pos + 4} 到 {end_pos}):")
            print(middle_value)

            middle_values.append(middle_value)

        
        swapped_middle_values = swap_middle_values(middle_values)

        if swapped_middle_values is None:
            print("错误: 互换中间值时发生错误。跳过互换。")
            continue

        
        if len(swapped_middle_values) != len(target_list):
            print(f"错误: 中间值的数量与目标列表中的数量不匹配。跳过互换。")
            continue

        
        for i, decimal_number in enumerate(target_list):
            byte_length = 4  
            target_hex = decimal_to_little_endian_hex(decimal_number, byte_length)
            print(f"\n修改后 {decimal_number} 的值: {swapped_middle_values[i]}")

            
            dat_file_path = find_dat_file_with_target(output_folder, target_hex)
            if not dat_file_path:
                print(f"未找到包含美化值 '{target_hex}' 的 .dat 文件。")
                continue

            
            target_hexes = [e578, d978]
            all_positions = {}
            for hex_str in target_hexes:
                positions = search_hex_positions(dat_file_path, hex_str)
                all_positions[hex_str] = positions

            
            if not all_positions[e578] or not all_positions[d978]:
                print(f"文件 '{dat_file_path}' 中缺少 '{e578}' 或 'd978'，跳过。")
                continue

            
            target_positions = search_hex_positions(dat_file_path, target_hex)
            if not target_positions:
                print(f"未找到美化值 '{target_hex}' 的位置。")
                continue

            
            target_position = target_positions[0]

            
            closest_positions = {}
            for hex_str in target_hexes:
                positions = all_positions[hex_str]
                closest = find_closest_positions(positions, target_position)
                closest_positions[hex_str] = closest

            
            e578_pos, e578_diff = closest_positions[e578][0]
            d978_pos, d978_diff = closest_positions[d978][0]

            
            if e578_pos < d978_pos:
                start_pos = e578_pos
                end_pos = d978_pos
            else:
                start_pos = d978_pos
                end_pos = e578_pos

            
            write_middle_value(dat_file_path, start_pos, end_pos, swapped_middle_values[i])

def main():
    
    config_files = ['伪实体配置.yaml', '伪实体配置.py']

    
    yaml_exists = os.path.isfile(config_files[0])
    py_exists = os.path.isfile(config_files[1])

    if not yaml_exists and not py_exists:
        print("错误: 未找到配置文件。")
        sys.exit(1)

    if yaml_exists and py_exists:
        print("检测到多个配置文件:")
        print("1. 伪实体配置.yaml")
        print("2. 伪实体配置.py")
        choice = input("请选择要使用的配置文件 (请输入1或2)，输入'exit'退出 :")
        if choice.lower() == 'exit':
            print("已退出。")
            sys.exit(0)
        elif choice == '1':
            config_file = config_files[0]
        elif choice == '2':
            config_file = config_files[1]
        else:
            print("无效的选择。退出程序。")
            sys.exit(1)
    elif yaml_exists:
        config_file = config_files[0]
    else:
        config_file = config_files[1]

    
    try:
        config = load_config(config_file)
    except ValueError as e:
        print(f"配置文件加载错误: {e}")
        sys.exit(1)

    
    output_folder = config.get('output_folder')
    if not output_folder:
        print("错误: 未在配置文件中找到 'output_folder'。")
        sys.exit(1)

    if not os.path.isdir(output_folder):
        print(f"错误: 文件夹 '{output_folder}' 不存在。")
        sys.exit(1)

    
    process_targets(config)

    print("\n成功修改美化。")

if __name__ == "__main__":
    main()
   