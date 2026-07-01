import os
import subprocess
import tempfile

SOUNDFONT = os.environ.get(
    'SOUNDFONT_PATH',
    '/usr/share/sounds/sf2/FluidR3_GM.sf2',
)


def midi_to_wav(midi, wav_path):
    with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
        midi.writeFile(tmp)
        mid_path = tmp.name
    try:
        result = subprocess.run(
            ['fluidsynth', '-ni', '-g', '1.0', '-F', wav_path, '-r', '44100', SOUNDFONT, mid_path],
            capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0:
            raise RuntimeError(f'FluidSynth: {result.stderr[-500:]}')
    finally:
        os.unlink(mid_path)
    return wav_path


def wav_to_mp3(wav_path, mp3_path):
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', wav_path, '-codec:a', 'libmp3lame', '-b:a', '192k', mp3_path],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f'ffmpeg: {result.stderr[-500:]}')
    return mp3_path


def render_song(midi, output_dir, base):
    os.makedirs(output_dir, exist_ok=True)
    wav = os.path.join(output_dir, f'{base}.wav')
    mp3 = os.path.join(output_dir, f'{base}.mp3')
    midi_to_wav(midi, wav)
    wav_to_mp3(wav, mp3)
    os.unlink(wav)
    return {'mp3': mp3}
