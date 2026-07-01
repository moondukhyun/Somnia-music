import argparse
import os
import sys
import datetime
import subprocess

from composer.presets import PRESETS
from video.assembler import create_video

OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'output')
SOUNDFONT   = os.environ.get('SOUNDFONT_PATH', '/usr/share/sounds/sf2/FluidR3_GM.sf2')

CATEGORIES = list(PRESETS.keys())
TITLES = {
    'morning_coffee': '모닝 커피 피아노 ☕ | 감성 피아노 음악',
    'meditation':     '명상 피아노 🌿 | 마음이 편안해지는 음악',
    'sleep':          '숙면 피아노 🌙 | 깊은 잠을 위한 음악',
    'study_focus':    '집중 피아노 📚 | 공부할 때 듣는 음악',
    'rainy_day':      '비 오는 날 피아노 🌧️ | 감성 멜로디',
}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def wav_to_mp3(wav_path, mp3_path):
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', wav_path, '-codec:a', 'libmp3lame', '-qscale:a', '2', mp3_path],
        capture_output=True, text=True
    )
    return os.path.exists(mp3_path)


def midi_to_wav(midi_path, wav_path, soundfont):
    result = subprocess.run(
        ['fluidsynth', '-ni', soundfont, midi_path, '-F', wav_path, '-r', '44100'],
        capture_output=True, text=True
    )
    return os.path.exists(wav_path)


def generate_midi_fallback(category, base_path):
    print("[MIDI] Using MIDI-based engine as fallback...")
    from composer.engine import generate_song
    midi = generate_song(category, PRESETS)
    midi_path = base_path + '.mid'
    wav_path  = base_path + '_midi.wav'
    with open(midi_path, 'wb') as f:
        midi.writeFile(f)
    if not midi_to_wav(midi_path, wav_path, SOUNDFONT):
        print("[ERROR] FluidSynth failed")
        sys.exit(1)
    return wav_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', choices=CATEGORIES,
                        default=CATEGORIES[datetime.date.today().weekday() % len(CATEGORIES)])
    parser.add_argument('--no-upload', action='store_true')
    args = parser.parse_args()

    category = args.category
    preset   = PRESETS[category]
    today    = datetime.date.today().strftime('%Y%m%d')
    base     = os.path.join(OUTPUT_DIR, f'{today}_{category}')
    ensure_dir(OUTPUT_DIR)

    print(f"[INFO] Category : {category}")
    print(f"[INFO] Title    : {TITLES.get(category, category)}")

    wav_path = base + '.wav'
    mp3_path = base + '.mp3'

    ai_success = False
    hf_key = os.environ.get('HF_API_KEY', '')

    if hf_key:
        print("[INFO] HF_API_KEY found — trying MusicGen AI...")
        try:
            from composer.ai_composer import generate_ai_music
            ai_success = generate_ai_music(category, wav_path)
        except Exception as e:
            print(f"[WARN] AI generation error: {e}")
            ai_success = False
    else:
        print("[INFO] HF_API_KEY not set — using MIDI engine")

    if not ai_success:
        wav_path = generate_midi_fallback(category, base)

    if not wav_to_mp3(wav_path, mp3_path):
        print("[ERROR] MP3 conversion failed")
        sys.exit(1)
    print(f"[INFO] MP3 ready: {mp3_path}")

    video_path = base + '.mp4'
    bg_key     = preset.get('background', 'morning')
    create_video(mp3_path, bg_key, video_path)
    print(f"[INFO] Video ready: {video_path}")

    if not args.no_upload:
        print("[INFO] Upload step (not implemented yet)")

    print("[DONE] Generation complete.")


if __name__ == '__main__':
    main()