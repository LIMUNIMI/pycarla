"""
Simple test.

Requires aplay
Use with an argument consisting of the path to a MIDI file
"""
import subprocess
import sys

import mido
import numpy as np

from . import AudioRecorder, Carla, JackServer, MIDIPlayer, get_smf_duration

FINAL_DECAY = 4
blocksize = 1024
server = JackServer(['-R', '-d', 'alsa', '-p', str(blocksize)])
carla = Carla("carla_proj/pianoteq0.carxp", server, min_wait=4)
carla.start()

filename = sys.argv[1]
player = MIDIPlayer(False)
recorder = AudioRecorder(blocksize-blocksize)

# testing one note
# print("Playing and recording one note in real-time mode..")
# duration = 1
# pitch = 64
# recorder.start(duration + FINAL_DECAY, sync=False)
# player.synthesize_midi_note(pitch, 64, duration, 0, sync=False)
# recorder.wait()
# audio = recorder.recorded
# if not np.any(audio):
#     print("\nError, no sample != 0")
#     carla.kill()
#     sys.exit()

# computing pitch from audio
# print(f"Detecting pitch (correct one is {pitch})...")
# pitch, confidence = esst.PitchYin(sampleRate=recorder.samplerate)(es.array(
#     np.mean(audio, axis=1)))
# pitch = 69 + 12 * np.log2(pitch/440)
# print(f"Detected pitch: {pitch}, {confidence}")

# testing full midi file
player = MIDIPlayer(True)
print("Playing and recording full file in freewheeling mode..")
duration = get_smf_duration(filename)
recorder.start(duration + FINAL_DECAY, sync=False)
player.synthesize_midi_file(filename, sync=True, progress=False)
recorder.wait()
recorder.save_recorded("session.wav")
server.kill()
carla.kill()

# playing wav file
print("Playing recorded file")
proc = subprocess.Popen(['play', 'session.wav'])
proc.wait()
