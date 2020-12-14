"""
Simple test.

Requires aplay
Use with an argument consisting of the path to a MIDI file
"""
import subprocess
import sys

import numpy as np
import mido

from .synth import (AudioRecorder, Carla, JackServer, MIDIPlayer,
                    get_smf_duration)

FINAL_DECAY = 4
server = JackServer(['-R', '-d', 'alsa'])
carla = Carla("carla_proj/pianoteq0.carxp", server, min_wait=4)
carla.start()

filename = sys.argv[1]
player = MIDIPlayer()
recorder = AudioRecorder()

# testing one note
print("Playing and recording one note..")
duration = 1
pitch = 64
recorder.start(duration + FINAL_DECAY)
player.synthesize_midi_note(pitch, 64, duration, 0)
recorder.wait()
audio = recorder.recorded
if not np.any(audio):
    print("Error, no sample != 0")
    carla.kill()
    sys.exit()

# computing pitch from audio
# print(f"Detecting pitch (correct one is {pitch})...")
# pitch, confidence = esst.PitchYin(sampleRate=recorder.samplerate)(es.array(
#     np.mean(audio, axis=1)))
# pitch = 69 + 12 * np.log2(pitch/440)
# print(f"Detected pitch: {pitch}, {confidence}")

# testing full midi file
print("Playing and recording full file..")
midifile = mido.MidiFile(filename)
duration = get_smf_duration(filename)
recorder.start(duration + FINAL_DECAY)
player.synthesize_midi_file(midifile, sync=False)
player.wait()
recorder.wait()
recorder.save_recorded("session.wav")

# playing wav file
print("Playing recorded file")
proc = subprocess.Popen(['aplay', 'session.wav'])
proc.wait()

carla.kill()
