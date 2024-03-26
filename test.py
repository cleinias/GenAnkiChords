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
    templ = Template("""[lilypond=void]
                                \\paper{#(set-paper-size '(cons (* 100 mm) (* 50 mm)))
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
                                            \\new Staff   {$trebleClefNotes}
                                            \\new Staff   {$bassClefNotes}

                                        >>
                                        \\layout {}
                                        \\midi {}
                                        }
                                 [/lilypond]""")

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
        lilyPondString = '{ \\time 4/4 \key c \major <c e\' g\' b\'>1 }'
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

    # def test_ShellVOff3rd_Png(self):
    #     """ Check the proper png file has been created and with the correct filename"""
    #     Png_filename = ''
    #
    #     self.assertEqual(PngString, self.voicing.genShellVOff3rdPng(), "Check string, it seems different")

    # def test_ShellVOff7rd_Png(self):
    #     """ Check the proper png file has been created and with the correct filename"""
    #     generated_filename = voicing.genShellVOff7thPng(self.chord)
    #     desired_filename = self.chord + 'ShellVOff7th'+'.png'
    #     'Need to check how'
    #     self.assertEqual(generated_filename, desired_filename, "Check if png file has been generated")
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