import random
from midiutil import MIDIFile

NOTE_MIDI = {
    'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
    'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
    'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71,
}

CHORD_INTERVALS = {
    'maj':  [0, 4, 7],
    'min':  [0, 3, 7],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    'add9': [0, 4, 7, 14],
}


def build_chord(root_midi, chord_type):
    return [root_midi + i for i in CHORD_INTERVALS[chord_type]]


def jv(vel, spread=8):
    return max(10, min(127, vel + random.randint(-spread, spread)))


def jt(t, spread=0.025):
    return t + random.uniform(-spread, spread)


class Composer:
    BEATS = 4
    TOTAL_BARS = 48  # ~3 min depending on tempo

    def __init__(self, preset):
        self.preset = preset
        self.tempo = preset['tempo']
        self.progression = preset['chord_progression']

    def compose(self):
        midi = MIDIFile(4)
        for t in range(4):
            midi.addTempo(t, 0, self.tempo)

        inst = self.preset.get('instruments', {})
        midi.addProgramChange(0, 0, 0, inst.get('piano', 0))
        midi.addProgramChange(1, 1, 0, inst.get('bass', 32))
        midi.addProgramChange(2, 2, 0, inst.get('pad', 48))

        for bar in range(self.TOTAL_BARS):
            beat = bar * self.BEATS
            root_str, chord_type = self.progression[bar % len(self.progression)]
            root = NOTE_MIDI[root_str]
            chord = build_chord(root, chord_type)
            vs = self._vel_scale(bar)

            self._piano(midi, beat, chord, vs)
            self._bass(midi, beat, root, vs, bar)
            self._pad(midi, beat, chord, vs, bar)
            self._drums(midi, beat, vs, bar)

        return midi

    def _vel_scale(self, bar):
        if bar < 4:
            return 0.35 + 0.65 * (bar / 4)
        if bar >= self.TOTAL_BARS - 4:
            return max(0.15, 1.0 - (bar - (self.TOTAL_BARS - 4)) / 4 * 0.85)
        return 1.0

    def _piano(self, midi, beat, chord, vs):
        style = self.preset.get('piano_style', 'arpeggiate')
        bv = int(self.preset.get('piano_velocity', 68) * vs)

        if style == 'arpeggiate':
            notes = chord[:3]
            step = self.BEATS / len(notes)
            for i, note in enumerate(notes):
                t = jt(beat + i * step)
                midi.addNote(0, 0, note, t, step * 0.82, jv(bv))
                if i == 0:
                    midi.addNote(0, 0, note - 12, t, step * 0.82, jv(bv - 12))

        elif style == 'block_chord':
            for note in chord[:3]:
                midi.addNote(0, 0, note, jt(beat), 1.85, jv(bv))
            if random.random() > 0.45:
                for note in chord[:3]:
                    midi.addNote(0, 0, note, jt(beat + 2), 1.85, jv(bv - 12))

        elif style == 'sparse':
            if random.random() > 0.35:
                offset = random.choice([0, 1, 2, 3])
                midi.addNote(0, 0, chord[0], jt(beat + offset), 1.5, jv(bv - 15))
                if len(chord) >= 3 and random.random() > 0.5:
                    midi.addNote(0, 0, chord[2], jt(beat + offset + 0.5), 1.0, jv(bv - 20))

    def _bass(self, midi, beat, root, vs, bar):
        if bar < 2:
            return
        bass_root = root - 24
        bv = int(self.preset.get('bass_velocity', 62) * vs)
        style = self.preset.get('bass_style', 'simple')

        if style == 'simple':
            midi.addNote(1, 1, bass_root, jt(beat), 1.8, jv(bv))
            if random.random() > 0.5:
                midi.addNote(1, 1, bass_root + 7, jt(beat + 2), 1.8, jv(bv - 8))
        elif style == 'walking':
            for i, off in enumerate([0, 4, 7, 5]):
                midi.addNote(1, 1, bass_root + off, jt(beat + i), 0.88, jv(bv))
        elif style == 'sustained':
            midi.addNote(1, 1, bass_root, beat, self.BEATS * 0.97, jv(bv, 4))

    def _pad(self, midi, beat, chord, vs, bar):
        if bar < 2:
            return
        bv = int(self.preset.get('pad_velocity', 52) * vs)
        for note in [n + 12 for n in chord[:3]]:
            midi.addNote(2, 2, note, beat, self.BEATS * 0.97, jv(bv, 5))

    def _drums(self, midi, beat, vs, bar):
        style = self.preset.get('percussion', 'none')
        if style == 'none' or bar < 4:
            return
        KICK, SNARE, HIHAT, HIHAT_OPEN = 36, 38, 42, 46
        bv = int(58 * vs)

        if style == 'lofi':
            for b in [0, 2]:
                midi.addNote(3, 9, KICK, jt(beat + b, 0.02), 0.35, jv(bv + 8))
            for b in [1, 3]:
                midi.addNote(3, 9, SNARE, jt(beat + b, 0.03), 0.35, jv(bv))
            for step in range(8):
                ht = HIHAT_OPEN if step in [3, 7] else HIHAT
                midi.addNote(3, 9, ht, jt(beat + step * 0.5, 0.02), 0.2, jv(bv - 18, 10))
        elif style == 'minimal':
            if random.random() > 0.3:
                midi.addNote(3, 9, KICK, jt(beat), 0.35, jv(bv - 8))
            if random.random() > 0.55:
                midi.addNote(3, 9, KICK, jt(beat + 2), 0.35, jv(bv - 12))
            for b in [0, 1, 2, 3]:
                if random.random() > 0.35:
                    midi.addNote(3, 9, HIHAT, jt(beat + b, 0.03), 0.2, jv(bv - 28, 8))


def generate_song(category, presets):
    return Composer(presets[category]).compose()
