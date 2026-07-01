import os
import time
import subprocess
import tempfile
import requests

HF_TOKEN = os.environ.get('HF_API_KEY', '')

MUSIC_PROMPTS = {
    'morning_coffee': [
        "emotional solo piano, Yiruma River Flows in You style, gentle arpeggios, warm and hopeful, soft touching melody, peaceful morning feeling, cinematic",
        "beautiful piano ballad, morning light, tender and heartfelt, soft arpeggios and flowing melody, Einaudi style, calm and uplifting",
        "peaceful piano music, gentle and warm, touching melody, quiet morning atmosphere, emotional and serene",
    ],
    'meditation': [
        "deep meditative piano, Einaudi Nuvole Bianche style, very slow and peaceful, emotional and introspective, minimal and beautiful, healing music",
        "ambient piano meditation, calm and tranquil, slow gentle melody, serene atmosphere, soft and touching, spiritual",
        "solo piano meditation music, very slow tempo, gentle arpeggios, peaceful and healing, emotional depth, minimal",
    ],
    'sleep': [
        "soft lullaby piano music, gentle and slow, very peaceful and tender, like a mother's embrace, warm and comforting, sleep inducing",
        "slow piano lullaby, very gentle melody, dreamlike and soft, peaceful night music, tender and loving, quiet",
        "soothing piano sleep music, gentle and slow, warm and safe, peaceful night atmosphere, soft and comforting",
    ],
    'study_focus': [
        "lofi piano music for studying, gentle and calm, soft melody, focus and concentration, peaceful background, emotional yet understated",
        "calm study piano music, gentle arpeggios, peaceful and focused, soft emotional melody, quiet concentration, lofi aesthetic",
        "peaceful piano background for focus, gentle and unobtrusive, soft touching melody, calm atmosphere, study music",
    ],
    'rainy_day': [
        "melancholic piano in the rain, deeply emotional, Yiruma style, bittersweet melody, touching and nostalgic, rainy day feeling, cinematic",
        "emotional rainy day piano, sad and beautiful, touching melody, melancholic and nostalgic, soft and gentle, heartfelt",
        "piano music rainy window, bittersweet and emotional, touching melody, melancholic atmosphere, gentle and deep",
    ],
}

MODEL_URL = MODEL_URL = "https://router.huggingface.co/hf-inference/models/facebook/musicgen-medium"
TOKENS_PER_SEGMENT = 1500


def _call_api(prompt, max_tokens, timeout=180):
    if not HF_TOKEN:
        print("[AI] HF_API_KEY not set, skipping AI generation")
        return None

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_tokens},
    }

    for attempt in range(3):
        try:
            print(f"[AI] Calling MusicGen API (attempt {attempt + 1}/3)...")
            resp = requests.post(MODEL_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                print(f"[AI] Success — received {len(resp.content) // 1024}KB audio")
                return resp.content
            elif resp.status_code == 503:
                wait = 20 + attempt * 10
                print(f"[AI] Model loading (503), waiting {wait}s...")
                time.sleep(wait)
            elif resp.status_code == 429:
                wait = 30 + attempt * 15
                print(f"[AI] Rate limited (429), waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"[AI] API error {resp.status_code}: {resp.text[:200]}")
                return None
        except requests.Timeout:
            print(f"[AI] Request timed out (attempt {attempt + 1})")
        except Exception as e:
            print(f"[AI] Request failed: {e}")
            return None
    return None


def _concat_wavs(seg_paths, output_path):
    if len(seg_paths) == 1:
        import shutil
        shutil.copy(seg_paths[0], output_path)
        return True
    try:
        inputs = []
        for p in seg_paths:
            inputs += ['-i', p]
        if len(seg_paths) == 2:
            filter_complex = "[0][1]acrossfade=d=2:c1=tri:c2=tri[out]"
            cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', filter_complex, '-map', '[out]', '-ar', '32000', output_path]
        else:
            filter_complex = "[0][1]acrossfade=d=2:c1=tri:c2=tri[ab];[ab][2]acrossfade=d=2:c1=tri:c2=tri[out]"
            cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', filter_complex, '-map', '[out]', '-ar', '32000', output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"[AI] Concat failed: {e}")
        return False


def _loop_to_duration(input_wav, output_wav, target_seconds=180):
    try:
        cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1',
            '-i', input_wav,
            '-t', str(target_seconds),
            '-af', f'afade=t=out:st={target_seconds - 8}:d=8',
            '-ar', '44100',
            output_wav,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"[AI] Loop failed: {e}")
        return False


def generate_ai_music(category, output_wav_path):
    prompts = MUSIC_PROMPTS.get(category, MUSIC_PROMPTS['morning_coffee'])
    tmpdir = tempfile.mkdtemp(prefix='musicgen_')
    segments = []

    for i, prompt in enumerate(prompts[:3]):
        print(f"[AI] Generating segment {i + 1}/3 for '{category}'...")
        wav_bytes = _call_api(prompt, TOKENS_PER_SEGMENT)
        if wav_bytes:
            seg_path = os.path.join(tmpdir, f'seg_{i}.wav')
            with open(seg_path, 'wb') as f:
                f.write(wav_bytes)
            segments.append(seg_path)
            print(f"[AI] Segment {i + 1} saved")
        else:
            print(f"[AI] Segment {i + 1} failed")
            break

    if not segments:
        print("[AI] No segments generated, falling back to MIDI")
        return False

    concat_path = os.path.join(tmpdir, 'concat.wav')
    if not _concat_wavs(segments, concat_path):
        concat_path = segments[0]

    if not _loop_to_duration(concat_path, output_wav_path, target_seconds=180):
        import shutil
        shutil.copy(concat_path, output_wav_path)

    print(f"[AI] Music generation complete: {output_wav_path}")
    return True