#!/usr/bin/env python3
"""
유튜브 OAuth 인증 최초 설정 스크립트.
실행 전: pip install google-auth-oauthlib

Usage: python setup_youtube_auth.py
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def main():
    print('유튜브 OAuth 인증 설정')
    print('=' * 40)
    print()
    print('1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 만드세요.')
    print('   https://console.cloud.google.com/apis/credentials')
    print('   유형: 데스크톱 앱  →  client_secrets.json 다운로드')
    print()

    secrets_path = input('client_secrets.json 경로: ').strip()
    if not os.path.exists(secrets_path):
        print(f'파일 없음: {secrets_path}')
        return

    flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
    creds = flow.run_local_server(port=0)

    data = {
        'token':         creds.token,
        'refresh_token': creds.refresh_token,
        'client_id':     creds.client_id,
        'client_secret': creds.client_secret,
    }

    out = json.dumps(data, indent=2)
    print()
    print('아래 JSON을 GitHub Secret "YOUTUBE_CREDENTIALS" 값으로 저장하세요:')
    print()
    print(out)

    with open('youtube_credentials.json', 'w') as f:
        f.write(out)
    print()
    print('로컬 테스트용으로 youtube_credentials.json에도 저장 완료.')


if __name__ == '__main__':
    main()
