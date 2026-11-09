import configparser
import sys
import os
from collections import deque

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
    required_keys = ['package_name', 'repo_url', 'test_mode', 'version', 'output_file', 'max_depth', 'filter_substring', 'ascii_tree']
    
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
    ascii_tree = settings.getboolean('ascii_tree')

    return {
        'package_name': settings['package_name'],
        'repo_url': settings['repo_url'],
        'test_mode': test_mode,
        'version': settings['version'],
        'output_file': settings['output_file'],
        'max_depth': max_depth,
        'filter_substring': settings['filter_substring'],
        'ascii_tree': ascii_tree
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

def build_graph_bfs(start_package, repo_path, max_depth, filter_substring):
    data = load_test_repo(repo_path)
    if not data:
        return {}

    graph = {}
    queue = deque()
    
    queue.append((start_package, 0))
    visited = set()
    
    while queue:
        current_pkg, current_depth = queue.popleft()
        
        if current_pkg in visited:
            continue
            
        visited.add(current_pkg)
        graph[current_pkg] = []
        
        if current_depth >= max_depth:
            continue

        if current_pkg not in data:
            continue
            
        for dep in data[current_pkg]:
            if filter_substring and filter_substring in dep:
                continue
                
            graph[current_pkg].append(dep)
            if dep not in visited:
                queue.append((dep, current_depth + 1))
                
    return graph

def get_load_order(graph, start_package):
    visited = set()
    order = []
    
    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for dep in graph.get(node, []):
            dfs(dep)
        order.append(node)
        
    dfs(start_package)
    return order

def generate_mermaid(graph):
    lines = ["graph TD"]
    for pkg, deps in graph.items():
        if not deps:
            lines.append(f"    {pkg}")
        else:
            for dep in deps:
                lines.append(f"    {pkg} --> {dep}")
    return "\n".join(lines)

def save_svg(filename, mermaid_text):
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
  <text x="10" y="20" font-family="Arial" font-size="14">Граф зависимостей (Mermaid):</text>
  <text x="10" y="40" font-family="Arial" font-size="12">{mermaid_text.replace(chr(10), ' | ')}</text>
</svg>'''
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"SVG-файл сохранен: {filename}")
    except Exception as e:
        print(f"Ошибка сохранения SVG: {e}")

def print_ascii_tree(graph, start_node, prefix="", is_last=True):
    print(prefix + ("└── " if is_last else "├── ") + start_node)
    children = graph.get(start_node, [])
    for i, child in enumerate(children):
        print_ascii_tree(graph, child, prefix + ("    " if is_last else "│   "), i == len(children) - 1)

def main():
    config_path = 'config.ini'
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    params = parse_config(config_path)

    print("--- Параметры конфигурации ---")
    for key, value in params.items():
        print(f"{key} = {value}")
        
    if params['test_mode']:
        print("\n--- Построение графа (BFS) ---")
        graph = build_graph_bfs(
            params['package_name'], 
            params['repo_url'], 
            params['max_depth'], 
            params['filter_substring']
        )
        
        if not graph:
            print("Граф пуст или пакет не найден.")
            return

        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "нет"
            print(f"{pkg} -> [{deps_str}]")
            
        print("\n--- Порядок загрузки зависимостей ---")
        load_order = get_load_order(graph, params['package_name'])
        print(" -> ".join(load_order))

        print("\n--- Визуализация ---")
        mermaid_code = generate_mermaid(graph)
        print("Mermaid-код:")
        print(mermaid_code)
        
        save_svg(params['output_file'], mermaid_code)

        if params['ascii_tree']:
            print("\n--- ASCII-дерево ---")
            print_ascii_tree(graph, params['package_name'])

if __name__ == "__main__":
    main()