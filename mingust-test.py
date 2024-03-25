# tests of the mingus package for lilypond png generation and midi to mp3 generation


from mingus.core import chords as mChords
from mingus.containers import Note as mNote
from mingus.containers import NoteContainer as mNote_container
from mingus.containers import Bar as mBar
from mingus.extra import lilypond as LilyPond
from mingus.midi.midi_file_out import write_Bar as mMidiFileOut
from  pydub  import AudioSegment
import midi2audio # import FluidSynth as Synth
import subprocess
soundFont = '/usr/share/soundfonts/FluidR3_GM.sf2'


myChord = "C7"
testVoicing = []
testVoicing = mNote_container()
testDir = "scrap"
testBar = mBar()
testPng = 'test.png'
testMIDI = 'test.mid'
testAudio = 'test.wav'
testFlac = 'testFlac'
testMp3 = 'test.mp3'

#create a chord
testChord = mChords.from_shorthand(myChord)
print('testChord --> ', testChord)

#create a test voicing: Shell voicing off 3rd
testVoicing.add_notes([mNote(testChord[1],3, channel=1), mNote(testChord[3], 3, channel=1)])
print('testVoicing --> ', testVoicing)

#create a bar from the voicing
testBar.place_notes(testVoicing,1)
print('testBar --> ',testBar)

# produce a png
try:
    LilyPond.to_png(LilyPond.from_Bar(testBar), testPng)
    print('png file from LilyPond written out as; ', testPng)
except:
    print('Png production failed')
# produce a MIDI
try:
    mMidiFileOut(testMIDI,testBar, bpm=80)
    print('MIDI file written as: ', testMIDI)
except:
    print('MIDI production failed')
# produce an mp3
# TODO
# Produce wav from MIDI with fluidsynth
# FLAC, a lossless codec, is supported as well (and recommended to be used)
try:
    subprocess.run(["fluidsynth",  "-ni",  '/usr/share/soundfonts/FluidR3_GM.sf2', testMIDI, "-F", testAudio])
    print('flac file written as: ', testFlac)
except:
    print('Conversion of MIDI to flac failed')

# read back wav and save it as mp3 with pydub
try:
    temp = AudioSegment.from_wav(testAudio)
    temp.export(testMp3, format="mp3")
    print('mp3 file written out as: ', testMp3)
except:
    print('mp3 production failed')