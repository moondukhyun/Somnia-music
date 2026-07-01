import random
from midiutil import MIDIFile

NOTE_MIDI = {
    'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
    'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
    'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71,
}

CHORD_NOTES = {
    'maj':  [0, 4, 7],
    'min':  [0, 3, 7],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
    'add9': [0, 4, 7, 14],
}

def _jt(beat, s=0.025):
    return beat + random.uniform(-s, s)

def _jv(vel, s=5):
    return max(15, min(120, vel + random.randint(-s, s)))


class Composer:
    BEATS      = 4
    TOTAL_BARS = 48

    def __init__(self, preset):
        self.tempo   = preset['tempo']
        self.prog    = preset.get('chord_progression', [
            ('C', 'maj7'), ('G', 'maj'), ('A', 'min7'), ('F', 'maj7')
        ])
        self.mel_vel = preset.get('piano_velocity', 68)
        self.arp_vel = max(28, self.mel_vel - 24)
        self.pad_vel = preset.get('pad_velocity', 36)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _chord(self, bar, octave=4):
        root_name, chord_type = self.prog[(bar // 2) % len(self.prog)]
        base = NOTE_MIDI.get(root_name, 60) + (octave - 5) * 12
        return [base + i for i in CHORD_NOTES.get(chord_type, [0, 4, 7])]

    def _section(self, bar):
        p = bar / self.TOTAL_BARS
        if p < 0.05:  return 'intro'   # bars 0-1   (~6s at 72bpm)
        if p < 0.42:  return 'verse'   # bars 2-19
        if p < 0.62:  return 'build'   # bars 20-29
        if p < 0.81:  return 'chorus'  # bars 30-38
        if p < 0.92:  return 'verse2'  # bars 39-43
        return 'outro'                  # bars 44-47

    # ── arpeggios (flowing accompaniment) ─────────────────────────────────────

    def _arpeggios(self, midi):
        for bar in range(self.TOTAL_BARS):
            sec  = self._section(bar)
            beat = bar * self.BEATS
            low  = self._chord(bar, octave=3)
            mid  = self._chord(bar, octave=4)

            r = low[0]
            t = mid[1] if len(mid) > 1 else mid[0]
            f = mid[2] if len(mid) > 2 else mid[-1]
            h = mid[0] + 12

            bv = {
                'intro':  self.arp_vel - 6,
                'verse':  self.arp_vel,
                'build':  self.arp_vel + 6,
                'chorus': self.arp_vel + 14,
                'verse2': self.arp_vel - 4,
                'outro':  self.arp_vel - 8,
            }.get(sec, self.arp_vel)

            if sec == 'outro':
                progress = (bar - self.TOTAL_BARS * 0.92) / (self.TOTAL_BARS * 0.08 + 1)
                bv = int(bv * (1 - progress * 0.7))
                if bv < 8:
                    continue

            # 8-note arpeggio per bar: root-3rd-5th-oct-3rd-5th-oct-3rd
            pattern = [r, t, f, h, t, f, h, t]
            for i, note in enumerate(pattern):
                v = _jv(bv + (6 if i == 0 else 0), 4)
                midi.addNote(1, 1, note, _jt(beat + i * 0.5), 0.47, v)

    # ── melody ────────────────────────────────────────────────────────────────

    def _next_note(self, prev, pool):
        """Smooth voice leading: prefer stepwise, chord-tone melody."""
        if not pool:
            return 60
        if prev is None:
            return pool[len(pool) // 2]
        ordered = sorted(pool, key=lambda n: abs(n - prev))
        if random.random() < 0.72:
            candidates = ordered[:min(3, len(ordered))]
            different  = [c for c in candidates if c != prev]
            return random.choice(different) if different else ordered[0]
        return random.choice(pool)

    def _melody(self, midi):
        prev = None

        for bar in range(self.TOTAL_BARS):
            sec  = self._section(bar)
            beat = bar * self.BEATS
            mid  = self._chord(bar, octave=4)
            high = self._chord(bar, octave=5)

            if sec == 'intro':
                # Arpeggio-only intro — no melody, very brief
                continue

            if sec == 'outro':
                progress = (bar - self.TOTAL_BARS * 0.92) / (self.TOTAL_BARS * 0.08 + 1)
                v = int(self.mel_vel * (1 - progress * 0.65))
                if bar % 2 == 0 and v > 12:
                    n = self._next_note(prev, mid)
                    midi.addNote(0, 0, n, _jt(beat + 0.5), 1.8, _jv(v, 4))
                    prev = n
                continue

            # Rhythmic pattern & velocity by section
            if sec == 'verse':
                # Lyrical: long notes (half-note feel)
                patterns = [
                    [(0, 1.85), (2, 1.85)],
                    [(0, 1.85), (1.5, 0.9), (2.5, 1.3)],
                ]
                positions = random.choice(patterns)
                v = self.mel_vel - 4

            elif sec == 'build':
                positions = [(0, 1.3), (1.5, 0.9), (2.5, 0.9), (3.5, 0.85)]
                v = self.mel_vel + 3

            elif sec == 'chorus':
                # Most active — use higher octave sometimes
                patterns = [
                    [(0, 0.9), (1, 0.9), (2, 0.9), (3, 0.9)],
                    [(0, 1.3), (1.5, 0.9), (2.5, 0.9), (3.5, 0.85)],
                ]
                positions = random.choice(patterns)
                v = self.mel_vel + 11

            else:  # verse2
                positions = [(0, 1.85), (2.5, 1.3)]
                v = self.mel_vel - 10

            pool = (mid + high) if sec == 'chorus' else mid

            for pos, dur in positions:
                n = self._next_note(prev, pool)
                midi.addNote(0, 0, n, _jt(beat + pos), dur, _jv(v, 6))
                prev = n

    # ── strings ───────────────────────────────────────────────────────────────

    def _strings(self, midi):
        for bar in range(self.TOTAL_BARS):
            if bar % 2 != 0:
                continue
            sec = self._section(bar)
            if sec == 'intro':
                continue

            v = {
                'verse':  self.pad_vel,
                'build':  self.pad_vel + 7,
                'chorus': self.pad_vel + 16,
                'verse2': self.pad_vel - 6,
                'outro':  self.pad_vel - 10,
            }.get(sec, self.pad_vel)

            if sec == 'outro':
                progress = (bar - self.TOTAL_BARS * 0.92) / (self.TOTAL_BARS * 0.08 + 1)
                v = int(v * (1 - progress * 0.85))
                if v < 8:
                    continue

            notes = self._chord(bar, octave=4)
            beat  = bar * self.BEATS
            for i, note in enumerate(notes):
                midi.addNote(2, 2, note, _jt(beat + i * 0.07), self.BEATS * 2 * 0.95, _jv(v, 5))

    # ── compose ───────────────────────────────────────────────────────────────

    def compose(self):
        midi = MIDIFile(3)
        for t in range(3):
            midi.addTempo(t, 0, self.tempo)
        midi.addProgramChange(0, 0, 0, 0)   # Acoustic Grand Piano (melody)
        midi.addProgramChange(1, 1, 0, 0)   # Acoustic Grand Piano (arpeggio)
        midi.addProgramChange(2, 2, 0, 48)  # String Ensemble (pad)
        self._arpeggios(midi)
        self._melody(midi)
        self._strings(midi)
        return midi


def generate_song(category, presets):
    preset = presets[category]
    composer = Composer(preset)
    return composer.compose()