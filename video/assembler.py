import os
import subprocess

BACKGROUNDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'backgrounds')

BG_FILES = {
    'morning': 'morning.jpg',
    'nature':  'nature.jpg',
    'night':   'night.jpg',
    'study':   'study.jpg',
    'rain':    'rain.jpg',
}

BG_COLORS = {
    'morning': 'FF9966',
    'nature':  '134E5E',
    'night':   '0F2027',
    'study':   '2C3E50',
    'rain':    '373B44',
}


def _gradient_bg(key, out_path):
    color = BG_COLORS.get(key, '1a1a2e')
    subprocess.run(
        ['ffmpeg', '-y', '-f', 'lavfi',
         '-i', f'color=c=0x{color}:s=1920x1080',
         '-frames:v', '1', out_path],
        capture_output=True, timeout=30,
    )
    return out_path


def create_video(audio_path, bg_key, output_path):
    bg_image = os.path.join(BACKGROUNDS_DIR, BG_FILES.get(bg_key, 'morning.jpg'))
    if not os.path.exists(bg_image):
        bg_image = _gradient_bg(bg_key, output_path + '_bg.png')

    result = subprocess.run(
        [
            'ffmpeg', '-y',
            '-loop', '1', '-i', bg_image,
            '-i', audio_path,
            '-c:v', 'libx264', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path,
        ],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f'ffmpeg video: {result.stderr[-500:]}')

    tmp_bg = output_path + '_bg.png'
    if os.path.exists(tmp_bg):
        os.unlink(tmp_bg)

    return output_path
