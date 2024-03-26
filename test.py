###
# Units test for Anki chord generation app
###

import chord_generation
import unittest
from bs4 import BeautifulSoup as BSHTML
from string import Template



from mingus.core import chords as mChords
from mingus.containers import Note as mNote
from mingus.containers import NoteContainer as mNote_container
from mingus.containers import Bar as mBar
from mingus.extra import lilypond as LilyPond
from mingus.midi.midi_file_out import write_Bar as mMidiFileOut
from  pydub  import AudioSegment
import subprocess
soundFont = '/usr/share/soundfonts/FluidR3_GM.sf2'

class TestGenAnkiChords(unittest.TestCase):
    """ Test main functions of the app"""

    roots = ['Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F', 'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#']
    qualities = ['M7', 'm7', 'dom7', 'm7b5']
    voicings = ['FullStandardV', 'ShellV', 'GuideTones', 'FourNotesShExt']
    app = chord_generation.GenAnkiChords(roots,qualities,voicings)

    def test_ChordDBCreated(self):
        self.assertEqual(type(self.app.chordsDB).__name__, 'dict', "GenAnkiChords apps should own a chordsDB \
                                                                           dictionary as an iVar")

    def test_allRowsPresentInChordsDB(self):
        keys = []
        for root in self.roots:
            for quality in self.qualities:
                keys.append(root+quality)
        app = chord
        self.assertEqual(keys, self.app.keys, "GenAnkiChords app should have a row for each chord in its chordsDB ivar")

    def test_EachRowHasVoicings(self):
        for voicing in self.voicing:
            self.assertIn(voicing,  self.app.chordsDB['voicings'].keys(), "GenAnkiChords app's chordsDB should \
                                                                                 have a voicing instance for all required\
                                                                                voicings")
class TestChordItemGen(unittest.TestCase):
    """ Test correct generation of a ChordItem"""

class TestVoicingCreation(unittest.TestCase):
    """ Test generation of Shell voicing"""
    # @classmethod
    # def __init__(self):
    voicings = ['ShellV', 'GuideTones', 'FourNotesShExt']
    root  = 'C'
    quality = 'M7'
    chord = mChords.from_shorthand(root+quality)
    voicing = chord_generation.Voicing(root,quality)
    templ = Template("""\\paper{#(set-paper-size '(cons (* 100 mm) (* 50 mm)))
                                    indent=0\\mm
                                    oddFooterMarkup=##f
                                    oddHeaderMarkup=##f
                                    bookTitleMarkup = ##f
                                    scoreTitleMarkup = ##f
                                    } 
                             \\version "2.24.3"
                             \\language "english"
                             \\score {
                                      \\new GrandStaff
                                      <<
                                        \\new Staff   {\\set fingeringOrientations = #'(up) <$trebleClefNotes>1}
                                        \\new Staff   {\\set fingeringOrientations = #'(down) \\clef bass <$bassClefNotes>1}

                                    >>
                                    \\layout {}
                                    \\midi {}
                                    }
                                    """)

    def filenameFromSrcTag(tag):
        """ Extracts a filename from the standard HTML src link"""
        soup = BSHTML(tag)
        image = soup.findAll('img')
        return image['src']

    def test_FullStandardVNotes(self):
        voicingNotes = mNote_container([mNote("C", 3, channel=1), mNote('E', 4, channel=1),
                                        mNote('G',4),mNote('B',4)])
        self.assertEqual(voicingNotes, self.voicing.genFullStandardVNotes(),
                         "Notes for {chord} shell voicing off 3rd should be {notes} in octave {octave}".format(chord='CM7',
                                                                                            notes = 'C, E, G, B',
                                                                                            octave = '3 for root and 4 o/w'))


    def test_ShellVOff3rdNotes(self):
        voicingNotes = mNote_container([mNote("C", 3, channel=1), mNote('E', 3, channel=1)])
        self.assertEqual(voicingNotes, self.voicing.genShellVOff3rdNotes(),
                         "Notes for {chord} shell voicing off 3rd should be {notes} in octave {octave}".format(chord='CM7',
                                                                                            notes = 'C and E',
                                                                                            octave = '3'))

    def test_ShellVOff7thNotes(self):
        voicingNotes = mNote_container([mNote('C', 3, channel=1), mNote('B', 3, channel=1)])
        self.assertEqual(voicingNotes, self.voicing.genShellVOff7thNotes(),
                         "Notes for {chord} shell voicing off 7th should be {notes} in octave {octave}".format(chord='CM7',
                                                                                                        notes='C and B',
                                                                                                        octave = '3'))
    def test_FullStandardV_LilyPond(self):
        lilyPondString = self.templ.substitute(trebleClefNotes = "e'-1 g'-3 b'-5", bassClefNotes = "c-1")
        self.assertEqual(lilyPondString, self.voicing.genFullStandardVLilyPond(),
                         "Check genFullStandardVLilyPond method, string seems different")


    def test_ShellVOff3rd_LilyPond(self):
        lilyPondString = '{ \\time 4/4 \key c \major <c e>1 }'
        self.assertEqual(lilyPondString, self.voicing.genShellVOff3rdLilyPond(),
                         "Check ShellVOff3rd_LilyPond method, string seems different")

    def test_ShellVOff7rd_LilyPond(self):
        lilyPondString = '{ \\time 4/4 \key c \major <c b>1 }'
        self.assertEqual(lilyPondString, self.voicing.genShellVOff7thLilyPond(),
                         "Check ShellVOff7th_LilyPond method, string  seems different")

    def test_FullStandardV_Png(self):
        """ Check the proper img tag has been created for the png file and with the correct filename"""
        filename = "CM7" + "-FullStandardV"+ ".png"
        pngTag  = '<img src=\"' + filename +  '\"\\>'
        self.assertEqual(pngTag, self.voicing.genFullStandardVPng(), "Check if png file is correct")

    def test_FullStandardV_mp3(self):
        """ Check the proper snd tag has been created for the mp3 file and with the correct filename"""
        filename = "CM7" + "-FullStandardV"+ ".mp3"
        pngTag  = '<snd src=\"' + filename +  '\" \\>'
        self.assertEqual(pngTag, self.voicing.genFullStandardVMp3(), "Check if mp3 file is correct")

    def test_ShellVOff3rd_Png(self):
        """ Check the proper png file has been created and with the correct filename"""
        filename = "CM7" + "-ShellVOff3rd" + ".png"
        pngTag = '<img src=\"' + filename +  '\"\\>'
        self.assertEqual(pngTag, self.voicing.genShellVOff3rdPng(), "Check if png file is correct")

    def test_ShellVOff7th_Png(self):
        """ Check the proper png file has been created and with the correct filename"""
        filename = "CM7" + "-ShellVOff7th" + ".png"
        pngTag = '<img src=\"' + filename + '\"\\>'
        self.assertEqual(pngTag, self.voicing.genShellVOff7thPng(), "Check if png file is correct")

    #
    # def test_ShellVOff3rdMp3(self):
    #     """ Check the proper mp3 file has been created and with the correct filename"""
    #     mp3_filename = ''
    #     self.assertEqual(lilyPondString, self.voicing.genShellVOff3rdLilyPond(), "Check string, it seems different")
    #
    # def test_ShellVOff7rdMp3(self):
    #     """ Check the proper png file has been created and with the correct filename"""
    #     mp3_filename = ''
    #     self.assertEqual(lilyPondString, self.voicing.genShellVOff7thLilyPond(), "Check string, it seems different")
    #
    # def test_ShellVOff3rdFingRH(self):
    #     """ Check the proper png file for RH fingering  has been created and with the correct filename"""
    #     RH_filename = ''
    #     self.assertEqual(PngString, self.voicing.genShellVOff3rdPng(), "Check string, it seems different")
    #
    # def test_ShellVOff7rdFingRH(self):
    #     """ Check the proper png file for RH fingering  has been created and with the correct filename"""
    #
    #     RH_filename = ''
    #     self.assertEqual(PngString, self.voicing.genShellVOff3rdPng(), "Check string, it seems different")
    #
    # def test_ShellVOff3rdFingLH(self):
    #     """ Check the proper png file for LH fingering  has been created and with the correct filename"""
    #     LH_filename = ''
    #     self.assertEqual(PngString, self.voicing.genShellVOff3rdPng(), "Check string, it seems different")
    #
    # def test_ShellVOff7rdFingLH(self):
    #     """ Check the proper png file for LH fingering  has been created and with the correct filename"""
    #     LH_filename = ''
    #     self.assertEqual(PngString, self.voicing.genShellVOff3rdPng(), "Check string, it seems different")
