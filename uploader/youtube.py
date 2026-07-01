import datetime
import json
import os

import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.http


def _client():
    raw = os.environ.get('YOUTUBE_CREDENTIALS')
    if not raw:
        raise EnvironmentError(
            'YOUTUBE_CREDENTIALS 환경변수가 없습니다.\n'
            'setup_youtube_auth.py를 실행해서 인증 정보를 얻으세요.'
        )
    d = json.loads(raw)
    creds = google.oauth2.credentials.Credentials(
        token=d.get('token'),
        refresh_token=d['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=d['client_id'],
        client_secret=d['client_secret'],
    )
    return googleapiclient.discovery.build('youtube', 'v3', credentials=creds)


def upload_video(video_path, preset, category_key):
    youtube = _client()
    today = datetime.date.today().strftime('%Y.%m.%d')

    body = {
        'snippet': {
            'title': f"{preset['name']} | {today} | 잔잔한 음악",
            'description': (
                f"{preset['description']}\n\n"
                f"AI가 매일 직접 작곡한 감미로운 음악입니다.\n"
                f"카테고리: {preset['name']}\n\n"
                f"좋아요와 구독으로 매일 새로운 음악을 받아보세요!\n\n"
                f"#힐링음악 #{category_key} #잔잔한음악 #ambient"
            ),
            'tags': preset.get('youtube_tags', []) + ['힐링', '잔잔한음악', 'ambient'],
            'categoryId': '10',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        },
    }

    media = googleapiclient.http.MediaFileUpload(
        video_path, mimetype='video/mp4', resumable=True, chunksize=10 * 1024 * 1024,
    )
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    vid_id = response['id']
    print(f'업로드 완료: https://www.youtube.com/watch?v={vid_id}')
    return vid_id
