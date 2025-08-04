from fastapi import APIRouter, Request
import os
import openai
from dotenv import load_dotenv
import json
import re

load_dotenv()

router = APIRouter(prefix="/api/food", tags=["food_text_analysis"])

@router.post("/analyze/text")
async def analyze_food_text(request: dict):
    """텍스트로 음식 분석 요청"""
    try:
        food_text = request.get("food_name", "")
        if not food_text:
            return {
                "success": False,
                "error": "음식 이름을 입력해주세요",
                "type": "text_analysis"
            }
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OpenAI API 키가 설정되지 않았습니다",
                "type": "config_error"
            }
        client = openai.OpenAI(api_key=api_key)
        messages = [
            {
                "role": "user",
                "content": f"""
You are a food analysis expert. 아래의 음식(또는 음식 설명)을 분석하여 영양성분 정보를 제공하세요.

음식: {food_text}

아래 JSON 형식으로만 응답하세요.
단일 음식이면 객체, 여러 음식이면 배열로 반환하세요.

{{
    "foodName": "음식 이름",
    "quantity": 숫자값,
    "calories": 숫자값,
    "carbohydrate": 숫자값,
    "protein": 숫자값,
    "fat": 숫자값,
    "sodium": 숫자값,
    "fiber": 숫자값,
    "totalAmount": 숫자값,
    "foodCategory": "한식/중식/일식/양식/분식/음료 중 하나"
}}

⚠ IMPORTANT: 
1. 반드시 유효한 JSON만 반환하세요. 설명, 텍스트 추가 금지.
2. 모든 값은 한국어로.
3. 같은 음식이 여러 번 언급되면 하나로 합쳐서 quantity에 총 개수를 표시하고 영양성분을 곱하세요.
4. quantity 필드는 해당 음식의 총 개수를 나타내야 합니다.
"""
            }
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\[.*\]|\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "result": result,
                    "type": "text_analysis"
                }
            except json.JSONDecodeError:
                pass
        return {
            "success": False,
            "error": "AI 응답을 파싱할 수 없습니다",
            "type": "parse_error"
        }
    except openai.OpenAIError as e:
        return {
            "success": False,
            "error": f"AI 분석 중 오류가 발생했습니다: {str(e)}",
            "type": "openai_api_error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"텍스트 분석 중 오류가 발생했습니다: {str(e)}",
            "type": "general_error"
        }