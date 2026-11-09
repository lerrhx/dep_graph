import configparser
import sys
import os

def parse_config(file_path):
    config = configparser.ConfigParser()
    
    if not os.path.exists(file_path):
        print(f"Ошибка: Конфигурационный файл не найден: {file_path}")
        sys.exit(1)
        
    try:
        config.read(file_path, encoding='utf-8')
    except Exception as e:
        print(f"Ошибка чтения конфигурационного файла: {e}")
        sys.exit(1)

    if 'Settings' not in config:
        print("Ошибка: В файле отсутствует секция [Settings]")
        sys.exit(1)

    settings = config['Settings']
    required_keys = ['package_name', 'repo_url', 'test_mode', 'version', 'output_file', 'max_depth', 'filter_substring']
    
    for key in required_keys:
        if key not in settings:
            print(f"Ошибка: В конфигурационном файле отсутствует ключ '{key}'")
            sys.exit(1)

    try:
        max_depth = int(settings['max_depth'])
        if max_depth <= 0:
            raise ValueError
    except ValueError:
        print("Ошибка: Параметр max_depth должен быть целым числом больше 0")
        sys.exit(1)

    test_mode = settings.getboolean('test_mode')

    return {
        'package_name': settings['package_name'],
        'repo_url': settings['repo_url'],
        'test_mode': test_mode,
        'version': settings['version'],
        'output_file': settings['output_file'],
        'max_depth': max_depth,
        'filter_substring': settings['filter_substring']
    }

def load_test_repo(file_path):
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл тестового репозитория не найден: {file_path}")
        return None
    
    dependencies = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" depends_on ")
                if len(parts) != 2:
                    continue
                pkg = parts[0].strip()
                deps_str = parts[1].strip()
                deps = [d.strip() for d in deps_str.split(",") if d.strip()]
                dependencies[pkg] = deps
    except Exception as e:
        print(f"Ошибка чтения тестового репозитория: {e}")
        return None
        
    return dependencies

def get_direct_dependencies(package_name, repo_path):
    data = load_test_repo(repo_path)
    if not data:
        return []
        
    if package_name in data:
        return data[package_name]
    else:
        return None

def main():
    config_path = 'config.ini'
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    params = parse_config(config_path)

    print("--- Параметры конфигурации ---")
    for key, value in params.items():
        print(f"{key} = {value}")
        
    if params['test_mode']:
        print("\n--- Режим тестирования ---")
        deps = get_direct_dependencies(params['package_name'], params['repo_url'])
        
        if deps is None:
            print(f"Ошибка: Пакет '{params['package_name']}' не найден в тестовом репозитории.")
        else:
            print(f"Прямые зависимости для пакета '{params['package_name']}':")
            for dep in deps:
                print(f" - {dep}")

if __name__ == "__main__":
    main()