"""
Daily Suno prompt generator using Claude API.
Generates 6 emotionally rich, varied prompts based on today's date and season.
"""

import os
import datetime
import json
import urllib.request
import urllib.error

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
MODEL = 'claude-haiku-4-5-20251001'


def get_season(month):
    if month in (3, 4, 5):   return '봄 (Spring)'
    if month in (6, 7, 8):   return '여름 (Summer)'
    if month in (9, 10, 11): return '가을 (Autumn)'
    return '겨울 (Winter)'


def get_day_kor(weekday):
    days = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    return days[weekday]


def call_claude(prompt_text):
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        return None

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt_text}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['content'][0]['text']
    except urllib.error.HTTPError as e:
        print(f"[ERROR] API call failed: {e.code} {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def generate_prompts(today):
    season  = get_season(today.month)
    day_kor = get_day_kor(today.weekday())
    date_str = today.strftime('%Y년 %m월 %d일')

    system_prompt = f"""당신은 Suno AI 음악 생성을 위한 전문 프롬프트 작성가입니다.
오늘은 {date_str} {day_kor}이고, 계절은 {season}입니다.

"솜니아 뮤직" 유튜브 채널을 위한 감성적인 피아노/힐링 음악 프롬프트를 6개 만들어주세요.

각 프롬프트는:
- 영어로 작성 (Suno AI는 영어 프롬프트가 더 좋음)
- 50-80 단어 분량
- 구체적인 악기, 감정, 분위기, 레퍼런스 아티스트 포함
- 반드시 instrumental only (가사 없음, 보컬 없음) — 프롬프트 맨 끝에 항상 "instrumental only, no vocals, no lyrics, no singing" 을 포함할 것
- 오늘의 날짜/계절/요일 감성을 반영

6가지 카테고리 (각각 반드시 다른 템포, 악기 구성, 분위기로 만들 것):

1. 아침/카페 무드
   - 템포: 보통~빠름 (100-120 BPM)
   - 악기: 밝고 경쾌한 피아노 + 어쿠스틱 기타 + 가벼운 퍼커션
   - 분위기: 밝고 희망적, 에너지 있음, 햇살 느낌

2. 수면/명상
   - 템포: 매우 느림 (40-60 BPM)
   - 악기: 매우 부드러운 피아노 단음 + 깊은 패드 사운드, 퍼커션 없음
   - 분위기: 극도로 조용하고 몽환적, 거의 소리가 없는 듯한 느낌

3. 감성/힐링 (오늘 계절 반영)
   - 템포: 느림 (60-80 BPM)
   - 악기: 피아노 + 첼로/바이올린 현악기 + 약한 앰비언트
   - 분위기: 뭉클하고 애절함, 눈물 나는 감동, 시네마틱

4. 집중/공부 로파이
