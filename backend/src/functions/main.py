# backend/src/functions/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from google import genai
import json
from datetime import datetime
import os

app = FastAPI()

# 環境変数から設定を読み込む想定
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class RequirementNode(BaseModel):
    id: str
    type: str
    text: str
    metadata: Optional[Dict] = {}
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class RequirementLink(BaseModel):
    source: str
    target: str
    label: str

class RequirementGraph(BaseModel):
    nodes: List[RequirementNode]
    links: List[RequirementLink]

class TextInput(BaseModel):
    text: str

def extract_requirements_prompt(text: str) -> str:
    return f"""
入力されたテキストから要件と制約を抽出し、それらの関係性を分析してください。
以下の形式でJSONを出力してください：

{{
    "nodes": [
        {{"id": "R1", "type": "requirement", "text": "抽出された要件1"}},
        {{"id": "C1", "type": "constraint", "text": "抽出された制約1"}},
        {{"id": "I1", "type": "implicit", "text": "暗黙の前提1"}}
    ],
    "links": [
        {{"source": "R1", "target": "C1", "label": "制約"}},
        {{"source": "I1", "target": "R1", "label": "関連"}}
    ]
}}

入力テキスト：
{text}
"""

async def analyze_with_gemini(text: str) -> Dict:
    model = genai.GenerativeModel('gemini-pro')
    prompt = extract_requirements_prompt(text)
    
    try:
        response = model.generate_content(prompt)
        # レスポンスからJSONを抽出
        json_str = response.text
        # JSON文字列をパースしてチェック
        result = json.loads(json_str)
        
        # 必要なキーの存在確認
        if "nodes" not in result or "links" not in result:
            raise ValueError("Invalid response format")
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

@app.post("/api/analyze", response_model=RequirementGraph)
async def analyze_requirements(input_data: TextInput) -> RequirementGraph:
    """
    テキストから要件を抽出し、関係グラフを生成するエンドポイント
    """
    try:
        result = await analyze_with_gemini(input_data.text)
        
        # レスポンスを適切な形式に変換
        graph = RequirementGraph(
            nodes=[RequirementNode(**node) for node in result["nodes"]],
            links=[RequirementLink(**link) for link in result["links"]]
        )
        
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)