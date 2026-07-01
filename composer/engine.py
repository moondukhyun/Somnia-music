import random
from midiutil import MIDIFile

NOTE_MIDI = {
    'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
    'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
    'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71,
}

SCALE_INTERVALS = {
    'pentatonic': [0, 2, 4, 7, 9],
    'major':      [0, 2, 4, 5, 7, 9, 11],
    'minor':      [0, 2, 3, 5, 7, 8, 10],
    'dorian':     [0, 2, 3, 5, 7, 9, 10],
}

CHORD_INTERVALS = {
    'maj':  [0, 4, 7],
    'min':  [0, 3, 7],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
}

# Section definitions: (start_bar, end_bar)
SECTIONS = [
    ('intro',       0,  4),   # bars 0-3:   sparse, melody only
    ('a_section',   4, 16),   # bars 4-15:  theme established
    ('b_section',  16, 24),   # bars 16-23: higher register, fuller
    ('a_prime',    24, 36),   # bars 24-35: return with variation
    ('development',36, 44),   # bars 36-43: most active, climax
    ('outro',      44, 48),   # bars 44-47: fade out, sparse
]


def _jt(beat, spread=0.04):
    return beat + random.uniform(-spread, spread)


def _jv(vel, spread=8):
    return max(20, min(127, vel + random.randint(-spread, spread)))


def _get_section(bar):
    for name, start, end in SECTIONS:
        if start <= bar < end:
            return name
    return 'outro'


class Composer:
    BEATS = 4
    TOTAL_BARS = 48

    def __init__(self, preset):
        self.tempo = preset['tempo']
        key = preset.get('key', 'C')
        self.root = NOTE_MIDI.get(key, 60)
        self.scale_name = preset.get('scale', 'pentatonic')
        self.progression = preset.get('chord_progression', [
            ('C', 'maj7'), ('G', 'maj'), ('A', 'min7'), ('F', 'maj7')
        ])
        self.base_vel = preset.get('piano_velocity', 70)
        self.bass_vel  = preset.get('bass_velocity', 60)
        self.pad_vel   = preset.get('pad_velocity', 50)

    # ------------------------------------------------------------------ helpers

    def _scale(self, root_offset=0, low=48, high=88):
        intervals = SCALE_INTERVALS.get(self.scale_name, [0, 2, 4, 7, 9])
        notes = []
        for oct_n in range(-2, 4):
            for iv in intervals:
                n = self.root + root_offset + oct_n * 12 + iv
                if low <= n <= high:
                    notes.append(n)
        return sorted(set(notes))

    def _chord_notes(self, root_name, chord_type, octave=4):
        base = NOTE_MIDI.get(root_name, 60) + (octave - 5) * 12
        return [base + i for i in CHORD_INTERVALS.get(chord_type, [0, 4, 7])]

    def _step(self, scale, prev, leap_prob=0.15):
        if not scale:
            return prev
        if prev not in scale:
            idx = min(range(len(scale)), key=lambda i: abs(scale[i] - prev))
        else:
            idx = scale.index(prev)
        if random.random() < leap_prob:
            step = random.choice([-3, -2, 2, 3])
        else:
            step = random.choice([-1, -1, 0, 1, 1])
        return scale[max(0, min(len(scale) - 1, idx + step))]

    # ------------------------------------------------------------------ melody

    def _melody(self, midi):
        # Normal scale (mid range) and high scale for B section
        scale_mid  = self._scale(low=52, high=80)
        scale_high = self._scale(low=64, high=88)
        scale_all  = self._scale(low=48, high=88)

        prev = scale_mid[len(scale_mid) // 2]

        for bar in range(self.TOTAL_BARS):
            section = _get_section(bar)
            base    = bar * self.BEATS

            if section == 'intro':
                # One long note every 2 bars — total silence on odd bars
                if bar % 2 == 0:
                    prev = self._step(scale_mid, prev, leap_prob=0.05)
                    midi.addNote(0, 0, prev, _jt(base), 1.8,
                                 _jv(self.base_vel - 20, 5))

            elif section == 'a_section':
                # 3-4 notes per bar, mostly stepwise
                n = random.randint(3, 4)
                offsets = sorted(random.sample(range(8), n))
                for off in offsets:
                    prev = self._step(scale_mid, prev, leap_prob=0.12)
                    dur  = random.choice([0.45, 0.9, 0.9])
                    midi.addNote(0, 0, prev, _jt(base + off * 0.5), dur,
                                 _jv(self.base_vel, 8))

            elif section == 'b_section':
                # 4-5 notes per bar, higher register
                n = random.randint(4, 5)
                offsets = sorted(random.sample(range(8), n))
                for off in offsets:
                    prev = self._step(scale_high, prev, leap_prob=0.2)
                    dur  = random.choice([0.45, 0.45, 0.9])
                    midi.addNote(0, 0, prev, _jt(base + off * 0.5), dur,
                                 _jv(self.base_vel + 5, 7))

            elif section == 'a_prime':
                # Back to mid range but with occasional ornament (quick passing note)
                n = random.randint(4, 5)
                offsets = sorted(random.sample(range(8), n))
                for i, off in enumerate(offsets):
                    old_prev = prev
                    prev = self._step(scale_mid, prev, leap_prob=0.15)
                    # ~20% chance of grace note just before
                    if i > 0 and random.random() < 0.2:
                        grace = old_prev + random.choice([-1, 1])
                        if grace in scale_mid:
                            midi.addNote(0, 0, grace,
                                         _jt(base + off * 0.5 - 0.18), 0.16,
                                         _jv(self.base_vel - 15, 4))
                    midi.addNote(0, 0, prev, _jt(base + off * 0.5),
                                 random.choice([0.45, 0.9]),
                                 _jv(self.base_vel + 3, 7))

            elif section == 'development':
                # 6-8 notes per bar, full range, highest energy
                n = random.randint(6, 8)
                offsets = sorted(random.sample(range(8), min(n, 8)))
                for off in offsets:
                    prev = self._step(scale_all, prev, leap_prob=0.28)
                    midi.addNote(0, 0, prev, _jt(base + off * 0.5), 0.45,
                                 _jv(self.base_vel + 12, 6))

            else:  # outro
                # One long note every 2 bars, velocity fades
                if bar % 2 == 0:
                    prev = self._step(scale_mid, prev, leap_prob=0.05)
                    fade = (bar - 44) / 4.0          # 0.0 → 1.0
                    vel  = int(self.base_vel * (1.0 - fade * 0.55))
                    midi.addNote(0, 0, prev, _jt(base), 1.8, _jv(vel, 4))

    # ------------------------------------------------------------------ chords

    def _chords(self, midi):
        for bar in range(self.TOTAL_BARS):
            section = _get_section(bar)
            base    = bar * self.BEATS

            if section == 'intro':
                continue                          # no chords in intro
            if section == 'outro' and bar >= 46:
                continue                          # fade chords out early

            prog_idx = (bar // 2) % len(self.progression)
            root_name, chord_type = self.progression[prog_idx]

            if section == 'outro':
                fade = (bar - 44) / 4.0
                vel  = _jv(int(self.pad_vel * (1.0 - fade * 0.6)), 4)
            elif section == 'development':
                vel  = _jv(self.pad_vel + 15, 5)
            elif section == 'b_section':
                vel  = _jv(self.pad_vel + 8, 6)
            else:
                vel  = _jv(self.pad_vel, 7)

            if section == 'development':
                # Chord every bar (not every 2 bars) for more drive
                oct_  = 4
                notes = self._chord_notes(root_name, chord_type, oct_)
                dur   = self.BEATS * 0.92
                for i, note in enumerate(notes):
                    midi.addNote(1, 1, note, _jt(base + i * 0.06), dur, vel)

            elif section == 'b_section':
                # Chord every bar, slightly higher voicing
                notes = self._chord_notes(root_name, chord_type, octave=5)
                dur   = self.BEATS * 0.92
                for i, note in enumerate(notes):
                    midi.addNote(1, 1, note, _jt(base + i * 0.07), dur, vel)

            else:
                # Default: chord every 2 bars, arpeggiated softly
                if bar % 2 == 0:
                    notes = self._chord_notes(root_name, chord_type, octave=4)
                    dur   = self.BEATS * 2 * 0.92
                    for i, note in enumerate(notes):
                        midi.addNote(1, 1, note,
                                     _jt(base + i * 0.06), dur, vel)

    # ------------------------------------------------------------------- bass

    def _bass(self, midi):
        for bar in range(self.TOTAL_BARS):
            section = _get_section(bar)
            base    = bar * self.BEATS

            if section in ('intro', 'outro'):
                continue

            prog_idx  = (bar // 2) % len(self.progression)
            root_name, _ = self.progression[prog_idx]
            root  = NOTE_MIDI.get(root_name, 60) - 24   # two octaves down
            fifth = root + 7

            if section == 'a_section':
                # Root on beat 1 only, every 2 bars
                if bar % 2 == 0:
                    midi.addNote(2, 2, root, _jt(base, 0.02), 1.85,
                                 _jv(self.bass_vel, 5))

            elif section == 'b_section':
                # Root + fifth each bar
                midi.addNote(2, 2, root,  _jt(base,     0.02), 1.85,
                             _jv(self.bass_vel,     5))
                midi.addNote(2, 2, fifth, _jt(base + 2, 0.02), 1.85,
                             _jv(self.bass_vel - 5, 5))

            elif section == 'a_prime':
                # Root + fifth every bar, more consistent
                midi.addNote(2, 2, root,  _jt(base,     0.02), 1.85,
                             _jv(self.bass_vel,     5))
                midi.addNote(2, 2, fifth, _jt(base + 2, 0.02), 1.85,
                             _jv(self.bass_vel - 3, 5))

            else:  # development — walking bass
                passing = root + random.choice([2, 3, 4])
                octave_up = root + 12
                for beat_off, note, vel_bump in [
                    (0, root,     8),
                    (1, passing,  4),
                    (2, fifth,    8),
                    (3, octave_up if random.random() > 0.4 else fifth, 3),
                ]:
                    midi.addNote(2, 2, note, _jt(base + beat_off, 0.02), 0.85,
                                 _jv(self.bass_vel + vel_bump, 5))

    # ----------------------------------------------------------------- compose

    def compose(self):
        midi = MIDIFile(3)
        for track in range(3):
            midi.addTempo(track, 0, self.tempo)
        midi.addProgramChange(0, 0, 0, 4)    # Electric Piano
        midi.addProgramChange(1, 1, 0, 48)   # String Ensemble
        midi.addProgramChange(2, 2, 0, 32)   # Acoustic Bass
        self._melody(midi)
        self._chords(midi)
        self._bass(midi)
        return midi