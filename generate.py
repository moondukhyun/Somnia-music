#!/usr/bin/env python3
"""
Somnia Music Generator

Usage:
    python generate.py --category morning_coffee --no-upload
    python generate.py --list
"""

import argparse
import datetime
import os

from composer.engine import generate_song
from composer.presets import PRESETS
from composer.renderer import render_song
from video.assembler import create_video

OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'output')


def run(category, upload):
    preset = PRESETS[category]
    today = datetime.date.today().strftime('%Y%m%d')
    base = f'{category}_{today}'

    print(f'\n[Somnia Music] {preset["name"]} ({today})')

    print('[1/4] 작곡 중...')
    midi = generate_song(category, PRESETS)

    print('[2/4] 오디오 렌더링 중...')
    paths = render_song(midi, OUTPUT_DIR, base)
    print(f'      {paths["mp3"]}')

    print('[3/4] 영상 제작 중...')
    video_path = os.path.join(OUTPUT_DIR, f'{base}.mp4')
    create_video(paths['mp3'], preset.get('background', 'morning'), video_path)
    print(f'      {video_path}')

    if upload:
        print('[4/4] 유튜브 업로드 중...')
        try:
            from uploader.youtube import upload_video
            upload_video(video_path, preset, category)
        except Exception as exc:
            print(f'      업로드 실패: {exc}')
    else:
        print('[4/4] 업로드 건너뜀 (--no-upload)')

    print('\n완료!')
    return video_path


def main():
    ap = argparse.ArgumentParser(description='Somnia Music Generator')
    ap.add_argument('--category', '-c', default='morning_coffee',
                    choices=list(PRESETS.keys()))
    ap.add_argument('--no-upload', action='store_true')
    ap.add_argument('--list', action='store_true', help='카테고리 목록 보기')
    args = ap.parse_args()

    if args.list:
        print('\n카테고리 목록:')
        for k, v in PRESETS.items():
            print(f'  {k:<20} {v["name"]} — {v["description"]}')
        print()
        return

    run(args.category, upload=not args.no_upload)


if __name__ == '__main__':
    main()
