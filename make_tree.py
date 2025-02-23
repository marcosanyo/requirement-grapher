import os
import pathlib
from pathlib import Path
import fnmatch
from typing import List, Set

def parse_gitignore(gitignore_path: Path) -> Set[str]:
    """
    .gitignoreファイルを解析し、除外パターンのセットを返す
    """
    if not gitignore_path.exists():
        return set()
    
    patterns = set()
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # パターンを正規化
                if line.startswith('/'):
                    line = line[1:]
                if line.endswith('/'):
                    line = line[:-1]
                patterns.add(line)
    return patterns

def should_ignore(path: Path, ignore_patterns: Set[str]) -> bool:
    """
    パスが除外対象かどうかをチェック
    """
    # ドットファイル/ディレクトリを除外
    if path.name.startswith('.'):
        return True
        
    # 一般的な設定ファイルを除外
    config_patterns = {
        'dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        'package.json', 'package-lock.json', 'yarn.lock',
        'requirements.txt', 'Pipfile', 'Pipfile.lock',
        'config.json', 'settings.json', '*.conf', '*.config',
        'makefile', 'Makefile', '*.mk',
        'tsconfig.json', 'webpack.config.js', 'babel.config.js',
        'jest.config.js', '*.toml', '*.yaml', '*.yml'
    }
    
    # ファイル名を小文字に変換して比較
    name_lower = path.name.lower()
    for pattern in config_patterns:
        if fnmatch.fnmatch(name_lower, pattern):
            return True
    
    # .gitignoreパターンをチェック
    rel_path = str(path.relative_to(path.parent)).replace('\\', '/')
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(rel_path, pattern) or \
           fnmatch.fnmatch(path.name, pattern):
            return True
            
    return False

def print_tree(directory: Path, prefix: str = '', ignore_patterns: Set[str] = set()) -> None:
    """
    ディレクトリ構造をツリー形式で表示
    設定ファイルとドットファイルは除外
    """
    try:
        # ディレクトリ内のアイテムを取得しソート
        contents = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name))
    except PermissionError:
        return
    
    # 各アイテムを処理
    for i, path in enumerate(contents):
        is_last = i == len(contents) - 1
        
        # 除外対象はスキップ
        if should_ignore(path, ignore_patterns):
            continue
            
        # ツリー構造の線を作成
        connector = '└── ' if is_last else '├── '
        print(f'{prefix}{connector}{path.name}')
        
        # ディレクトリの場合は再帰的に処理
        if path.is_dir():
            next_prefix = prefix + ('    ' if is_last else '│   ')
            print_tree(path, next_prefix, ignore_patterns)

def main():
    # カレントディレクトリをルートとして使用
    root_dir = Path('.')
    gitignore_path = root_dir / '.gitignore'
    
    # .gitignoreパターンを解析
    ignore_patterns = parse_gitignore(gitignore_path)
    
    # ルートディレクトリ名を表示（ドットで始まる場合は除外）
    root_name = root_dir.absolute().name
    if not root_name.startswith('.'):
        print(root_name)
        print_tree(root_dir, '', ignore_patterns)

if __name__ == '__main__':
    main()