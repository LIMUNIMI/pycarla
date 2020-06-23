import subprocess
import numpy as np
import pretty_midi as pm
from . import Carla, MIDIPlayer, MIDIRecorder, JackServer, get_smf_duration

if __name__ == "__main__":
    import sys
    import essentia.standard as esst
    import essentia as es
    SR = 22050
    FINAL_DECAY = 4
    server = JackServer(['-R', '-d', 'alsa'])
    carla = Carla("carla_proj/pianoteq0.carxp", server, min_wait=4)
    carla.start()

    filename = sys.argv[1]
    player = MIDIPlayer()
    recorder = MIDIRecorder()

    # testing one note
    print("Playing and recording one note..")
    duration = 2
    pitch = 64
    recorder.start('tmp.wav', duration + FINAL_DECAY)
    player.synthesize_midi_note(pitch, 64, duration, 0)
    player.wait()
    recorder.wait()
    audio, sr = recorder.get_recorded()
    if not np.any(audio):
        print("Error, no sample != 0")
        carla.kill()
        sys.exit()

    # playing wav file
    print("Playing recorded file")
    proc = subprocess.Popen(['aplay', 'tmp.wav'])
    proc.wait()
    recorder.del_recorded()

    # computing pitch from audio
    print(f"Detecting pitch (correct one is {pitch})...")
    pitch, confidence = esst.PitchYin(sampleRate=sr)(es.array(
        np.mean(audio, axis=1)))
    pitch = pm.hz_to_note_number(pitch)
    print(f"Detected pitch: {pitch}, {confidence}")

    # testing full midi file
    print("Playing and recording full file..")
    duration = get_smf_duration(filename)
    recorder.start('session.wav', duration + FINAL_DECAY)
    player.synthesize_midi_file(filename)
    player.wait()
    recorder.wait()

    # playing wav file
    print("Playing recorded file")
    proc = subprocess.Popen(['aplay', 'session.wav'])
    proc.wait()

    player.close()
    carla.kill()
