# backend/src/functions/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from google import genai
import os
from dotenv import load_dotenv
import json
import logging
import re

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数のロード
load_dotenv()

# FastAPIアプリケーションの作成
app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini APIクライアントの初期化
genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# データモデル
class RequirementNode(BaseModel):
    id: str
    type: str  # requirement/constraint/implicit
    text: str
    description: Optional[str] = None  # 詳細説明を追加

class RequirementLink(BaseModel):
    source: str
    target: str
    label: str

class RequirementGraph(BaseModel):
    nodes: List[RequirementNode]
    links: List[RequirementLink]

class RequirementInput(BaseModel):
    text: str

def extract_requirements_prompt(text: str) -> str:
    return f"""あなたは要件分析の専門家です。
以下のテキストから要件(R)、制約(C)、暗黙知/前提(I)を抽出し、それらの関係性を分析してください。

要件は簡潔に端的な表現で表し、詳細は補足情報として含めてください。
R,C,Iのノード同士を接続するlinksは、基本的にはそれぞれ作成するようにし、linkの無い単一のノードは存在しないようにしてください。

下記の形式のJSONのみを出力してください。
説明文などは一切不要です。

{{
    "nodes": [
        {{"id": "R1", "type": "requirement", "text": "抽出された要件", "description": "要件の詳細説明"}},
        {{"id": "C1", "type": "constraint", "text": "抽出された制約", "description": "制約の詳細説明"}},
        {{"id": "I1", "type": "implicit", "text": "抽出された暗黙知", "description": "暗黙知の詳細説明"}}
    ],
    "links": [
        {{"source": "C1", "target": "R1", "label": "制約"}},
        {{"source": "I1", "target": "R1", "label": "知見"}}
    ]
}}

入力テキスト:
{text}"""

def extract_json_from_text(text: str) -> dict:
    try:
        # 最初の{から最後の}までを抽出
        json_pattern = re.compile(r'\{.*\}', re.DOTALL)
        match = json_pattern.search(text)
        if not match:
            raise ValueError("JSON not found in response")
        
        json_str = match.group()
        # JSONパース
        data = json.loads(json_str)
        return data
    except Exception as e:
        logger.error(f"JSON extraction failed: {text}")
        raise ValueError(f"Failed to extract JSON: {str(e)}")

@app.post("/api/requirements/extract", response_model=RequirementGraph)
async def extract_requirements(input: RequirementInput):
    try:
        # Gemini APIを使用して要件を抽出
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=extract_requirements_prompt(input.text)
        )
        
        if not response or not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response")

        logger.info(f"Raw response: {response.text}")
        
        # レスポンスからJSONを抽出してパース
        result = extract_json_from_text(response.text)
        
        # 結果の検証
        if not isinstance(result, dict) or 'nodes' not in result or 'links' not in result:
            raise ValueError("Invalid response format")
        
        return RequirementGraph(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="要件の抽出に失敗しました")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)