# backend/src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from google import genai
import os
from dotenv import load_dotenv
import yaml
import logging
import json
import re
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数のロード
load_dotenv()

# パスの設定
BASE_DIR = Path(__file__).parent.parent.parent.parent  # プロジェクトのルートディレクトリ
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
logger.info(f"Frontend directory: {FRONTEND_DIR}")

# FastAPIアプリケーションの作成
app = FastAPI(title="要件・制約分析支援システム", description="テキストから要件と制約を抽出・視覚化するシステム")

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルのマウント（本番ビルド環境用）
if FRONTEND_DIR.exists():
    logger.info(f"Mounting frontend build from {FRONTEND_DIR}")
    
    # ディレクトリごとにマウント
    static_dirs = ["css", "js", "assets", "img", "fonts"]
    for dir_name in static_dirs:
        dir_path = FRONTEND_DIR / dir_name
        if dir_path.exists():
            app.mount(f"/{dir_name}", StaticFiles(directory=str(dir_path)), name=dir_name)
            logger.info(f"Mounted static directory: /{dir_name}")
    
    # 個別の静的ファイル（ルートにあるもの）を処理するためのエンドポイント
    @app.get("/favicon.ico")
    async def get_favicon():
        favicon_path = FRONTEND_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        logger.warning("Favicon not found")
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    # その他のルート静的ファイル（必要に応じて追加）
    @app.get("/robots.txt")
    async def get_robots():
        robots_path = FRONTEND_DIR / "robots.txt"
        if robots_path.exists():
            return FileResponse(str(robots_path))
        raise HTTPException(status_code=404, detail="Robots.txt not found")

# Gemini APIクライアントの初期化
try:
    genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    logger.info("Gemini API client initialized successfully")
except Exception as e:
    logger.error(f"Gemini APIの初期化に失敗: {e}")
    genai_client = None

# データモデル
class RequirementNode(BaseModel):
    id: str
    type: str  # requirement/constraint/implicit
    text: str
    description: Optional[str] = None  # 詳細説明

class RequirementLink(BaseModel):
    source: str
    target: str
    label: str

class RequirementGraph(BaseModel):
    nodes: List[RequirementNode]
    links: List[RequirementLink]

class RequirementInput(BaseModel):
    text: str

class YamlOutput(BaseModel):
    yaml: str
    
class RequirementWithYaml(BaseModel):
    yaml: str
    graph: RequirementGraph

# プロンプト関数
def extract_yaml_prompt(text: str) -> str:
    return f"""あなたは要件分析の専門家です。
以下のテキストから要件(R)、制約(C)、暗黙知/前提(I)を抽出し、それらの関係性を分析してください。

最初にYAML形式で構造化して出力してください。以下のような形式です：

```yaml
requirements:
  - id: "R1"
    text: "ユーザー認証機能を実装する"
    description: "ユーザーがシステムにログインできるようにする"
    related_to:
      - id: "I1"
        relation: "depends_on"
      - id: "C2"
        relation: "constrained_by"

constraints:
  - id: "C1"
    text: "レスポンス時間は1秒以内"
    description: "システムは全ての操作に対して1秒以内に応答する必要がある"
    
implicit_knowledge:
  - id: "I1"
    text: "ユーザーは技術に精通していない"
    description: "エンドユーザーは技術的な知識が限られているため、直感的なインターフェースが必要"
```

入力テキスト:
{text}"""

# ユーティリティ関数
def extract_yaml_from_text(text: str) -> str:
    try:
        # YAMLブロックを探す (```yaml と ``` の間)
        yaml_pattern = re.compile(r'```yaml\s*([\s\S]*?)\s*```', re.DOTALL)
        match = yaml_pattern.search(text)
        
        if match:
            return match.group(1).strip()
        
        # バックティックなしのケースも考慮
        yaml_start = text.find('requirements:')
        if yaml_start != -1:
            return text[yaml_start:].strip()
            
        raise ValueError("YAML not found in response")
    except Exception as e:
        logger.error(f"YAML extraction failed: {text}")
        raise ValueError(f"Failed to extract YAML: {str(e)}")

def yaml_to_graph(yaml_text: str) -> dict:
    """YAMLテキストをグラフ構造に変換する"""
    try:
        yaml_data = yaml.safe_load(yaml_text)
        nodes = []
        links = []
        
        # 要件ノードの処理
        if 'requirements' in yaml_data:
            for req in yaml_data['requirements']:
                nodes.append({
                    "id": req["id"],
                    "type": "requirement",
                    "text": req["text"],
                    "description": req.get("description", req["text"])
                })
                
                # 関連要素の処理
                if "related_to" in req:
                    for rel in req["related_to"]:
                        links.append({
                            "source": req["id"],
                            "target": rel["id"],
                            "label": rel["relation"]
                        })
        
        # 制約ノードの処理
        if 'constraints' in yaml_data:
            for const in yaml_data['constraints']:
                nodes.append({
                    "id": const["id"],
                    "type": "constraint",
                    "text": const["text"],
                    "description": const.get("description", const["text"])
                })
                
                # 関連要素の処理
                if "related_to" in const:
                    for rel in const["related_to"]:
                        links.append({
                            "source": const["id"],
                            "target": rel["id"],
                            "label": rel["relation"]
                        })
        
        # 暗黙知ノードの処理
        if 'implicit_knowledge' in yaml_data:
            for impl in yaml_data['implicit_knowledge']:
                nodes.append({
                    "id": impl["id"],
                    "type": "implicit",
                    "text": impl["text"],
                    "description": impl.get("description", impl["text"])
                })
                
                # 関連要素の処理
                if "related_to" in impl:
                    for rel in impl["related_to"]:
                        links.append({
                            "source": impl["id"],
                            "target": rel["id"],
                            "label": rel["relation"]
                        })
        
        return {
            "nodes": nodes,
            "links": links
        }
    except Exception as e:
        logger.error(f"YAML変換エラー: {str(e)}")
        raise ValueError(f"YAMLからグラフへの変換に失敗しました: {str(e)}")

# APIエンドポイント
@app.post("/api/requirements/extract_yaml", response_model=YamlOutput)
async def extract_requirements_yaml(input: RequirementInput):
    """テキスト入力からYAML形式で要件を構造化して出力するエンドポイント"""
    try:
        # Gemini APIを使用してYAML形式で要件を抽出
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-001",  
            contents=extract_yaml_prompt(input.text)
        )
        
        if not response or not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate YAML response")

        logger.info(f"Raw YAML response: {response.text}")
        
        # レスポンスからYAMLを抽出
        yaml_text = extract_yaml_from_text(response.text)
        
        return YamlOutput(yaml=yaml_text)
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"YAML extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail="YAML形式での要件抽出に失敗しました")

@app.post("/api/requirements/yaml_to_graph", response_model=RequirementGraph)
async def convert_yaml_to_graph(yaml_input: YamlOutput):
    """YAML形式の入力からグラフ構造に変換するエンドポイント"""
    try:
        graph_data = yaml_to_graph(yaml_input.yaml)
        return RequirementGraph(**graph_data)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"YAML to graph conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail="YAMLからグラフへの変換に失敗しました")

@app.post("/api/requirements/extract_with_yaml", response_model=RequirementWithYaml)
async def extract_with_yaml(input: RequirementInput):
    """テキストからYAML中間形式を経由してグラフを生成する統合エンドポイント"""
    try:
        # まずYAML形式で抽出
        yaml_response = await extract_requirements_yaml(input)
        yaml_text = yaml_response.yaml
        
        # YAMLからグラフに変換
        graph_data = yaml_to_graph(yaml_text)
        graph = RequirementGraph(**graph_data)
        
        # 両方の結果を返す
        return RequirementWithYaml(yaml=yaml_text, graph=graph)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Integrated extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail="要件の統合抽出に失敗しました")

# SPAルートハンドラ - 必ずAPIエンドポイントの後に定義する
if FRONTEND_DIR.exists():
    @app.get("/", include_in_schema=False)
    async def serve_spa_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # APIエンドポイントは除外
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # 静的ファイルが存在する場合はそれを提供
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # それ以外の場合はindex.htmlを提供
        logger.debug(f"Serving index.html for SPA route: {full_path}")
        return FileResponse(str(FRONTEND_DIR / "index.html"))

# アプリケーションの起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)