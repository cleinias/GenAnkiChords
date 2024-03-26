######################################################################################
# -*- coding: utf-8 -*-
# Simple file to generate an Anki deck for chords
# Copyright (c) 2024 Stefano Franchi <stefano.franchi@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/licenses/gpl.html
######################################################################################


# Import the library needed to manipulate and create an Anki deck
import genanki
import csv
from string import Template
import html
import re
from mingus.core import chords as mChords
from mingus.containers import Note as mNote
from mingus.containers import NoteContainer as mNote_container
from mingus.containers import Bar as mBar
from mingus.extra import lilypond as LilyPond
from mingus.midi.midi_file_out import write_Bar as mMidiFileOut
from  pydub  import AudioSegment
import subprocess
from dataclasses import dataclass
#################################################################################################
#                                                Globals                                        #
#################################################################################################
def initGlobals():
    chordsDatafile = "ChordsData.csv"
    ankiLocalPath = '/home/stefano/.local/share/Anki2/Stefano/'
    ankiMediaRepo = 'collection.media'
    ankiMediaDir = ankiLocalPath + ankiMediaRepo
    model_id= 1149467492  # randomly generated with import random; random.randrange(1 << 30, 1 << 31)
    deck_id= 1393751746  # randomly generated with import random; random.randrange(1 << 30, 1 << 31)
    deckName= "Comping Chords"
    deckFileName= "Comping-Chords.apkg"
    engl2ItNotes, it2EnglNotes = createEnglItTransDicts()
    soundFont = '/usr/share/soundfonts/FluidR3_GM.sf2'
    return chordsDatafile,  model_id, deck_id, deckName, deckFileName, engl2ItNotes, it2EnglNotes, soundFont

    # for chord generation
    roots =  ['C', 'C#', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    qualities = ['maj7', 'min7', 'halfdim', 'dom7']
    newchordsData = createChordItems((roots,qualities))

    # for fieldNames generation in chordItems
    extraFields = 'sortId'

#########################################################################################
#                                      CLASSES                                          #
#########################################################################################
class GenAnkiChords():
    """
    Contains the procedural code generating the notes--it is a singleton
    """

    # Define the basic chords the app will build notes for as roots and qualities
    roots = ['Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F', 'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#']
    qualities = ['M7', 'm7', 'm7b5']
    voicings = ['ShellV', 'GuideTones', 'FourNotesShExt']
    chordItems = {}  # The db-like data structure that holds one row per chord+quality

    def __init__(self):
        """
        Initialize variables and all the parameters of the app, then build all the ChordItems
        """

        # generate the chordItems and add all the auxiliary fields
        self.genChordItems()

        # generate and add the desired voicings
        self.genAddVoicing(self.voicings)


    def genChordItems(chordItems,roots, qualities):
        """
        Create a chordItem row from a list of roots and a list of qualities,
        including a mingus  Chord type
        :param roots:  a list of chord roots
        :param qualities: a list of chord qualities
        :return chordItems: a dictionary of chorditems indexed by root-quality:
        """
        for root in roots:
            for quality in qualities:
                chordItems[root + '-', quality].append(root)
                chordItems[root + '-', quality].append(quality)
                chordItems[root + '-', quality].append(mChords.from_shorthand(root + quality))

    def addVocings(self):
        for chordItem in self.chordItems:
            chordItem.add


@dataclass
class ChordItem(object):
    __slots__ = ['sortId', 'name', 'root', 'quality', 'chord','inversion', 'voicings']

    def __init__(self,voicings=[]):
        pass


    def addAuxiliaryFields(self):
        """
            TODO
            Generate the auxiliary fields and files for every chordItems (png from LilyPond, sound from MIDI, fingerings)
            :return:
        """
        for voicing in self.voicings:
            v = Voicing(self.chord)
            try:
                genVoicingMethod = getattr(Voicing, 'gen'+voicing)
                self.voicings.append(v.genVoicingMethod())
            except AttributeError:
                raise NotImplementedError(
                    "Class `{}` does not implement `{}`".format(Voicing.__class__.__name__, genVoicingMethod))



@dataclass
class Voicing():
    """
    Instances of this class know how to generate a list of notes
    and auxiliary files (lilypond, png, MID), etc.) for a chord
    and for a few voicings
    """

    #__slots__ =  'chord' # the list of generated fields containing all the data for the given chord and voicing
    knownVoicings = ['FullStandardV', 'ShellV', 'GuideTones', 'FourNotesShExt'] # the class only knows these voicings
    startNotes = ['Off3rd', 'Off7th']
    auxiliaryFieldsSuffixes = ['LH', 'RH', 'LilyPond', 'LilyPondMidiLink', 'LilyPondSndLink']
    tmpPng = '' # temporary file holding the LilyPond-generated png file
    tmpMIDI = '' # temporary file holding the mingus--generated MIDI file
    tmpMp3 = '' # temporary file holding the fluidsynth-generated and pydub-converted mp3 file

    def __init__(self,root,quality):
        self.root = root
        self.quality = quality
        self.chord = mChords.from_shorthand(root+quality)
        self.lilyPondTemplate = self.getLilyPondTemplate()

    def getLilyPondTemplate(self):
        """"""
        templ= Template("""\\paper{#(set-paper-size '(cons (* 100 mm) (* 50 mm)))
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
                                        \\new Staff   {<$trebleClefNotes>1}
                                        \\new Staff   {\\clef bass <$bassClefNotes>1}

                                    >>
                                    \\layout {}
                                    \\midi {}
                                    }
                                    """)
        return templ

    def genShellV(self):
        """ Generate lilypond, mp3, png, and fingerings for both off-3rd and off-7th  shell voicings"""
        self.shellVOff3rdLilypond = self.genShellVOff3rdLilyPond()
        self.shellVOff7thLilypond = self.genShellVOff7thLilyPond()

    def genFullStandardV(self):
        """ Generate lilypond, mp3, png, and fingerings for standard 4 notes, root position voicing"""
        self.fullStandardVLilyPond = self.genFullStandardVLilyPond()


    def genFullStandardVNotes(self):
        notes = [mNote(self.chord[0],3),mNote(self.chord[1], 4),
                 mNote(self.chord[2],4), mNote(self.chord[3],4)]
        return notes


    def genShellVOff3rdNotes(self):
        "Choose the right notes and octave for the off-3rd voicing for the given chord"
        notes = [mNote(self.chord[0],3),mNote(self.chord[1],3)]
        return notes

    def genShellVOff7thNotes(self):
        "Choose the right notes and octave for the off-3rd voicing for the given chord"
        notes = [mNote(self.chord[0],3),mNote(self.chord[3],3)]
        return notes

    def genFullStandardVLilyPond(self):
        """Generate the lilypond string for the voicing"""
        bar = mBar()
        lilyPondString = self.lilyPondTemplate.substitute(bassClefNotes = "c", trebleClefNotes = "e' g' b'")
        return lilyPondString

    def genShellVOff3rdLilyPond(self):
        """Generate the lilypond string for the voicing"""
        bar = mBar()
        bar.place_notes(self.genShellVOff3rdNotes(),1)
        return LilyPond.from_Bar(bar)

    def genShellVOff7thLilyPond(self):
        """Generate the lilypond string for the voicing"""
        bar = mBar()
        bar.place_notes(mNote_container(self.genShellVOff7thNotes()),1)
        return LilyPond.from_Bar(bar)

    def genFullStandardVPng(self):
        "generate the png file for the voicing"
        fileOut = self.root+self.quality+'-FullStandardV'+'.png'
        LilyPond.to_png(self.genFullStandardVLilyPond(), fileOut)
        imgTag = '<img src=\"{filename}\"\\>'.format(filename=fileOut)
        return imgTag


    def genGuideTonesV(self):
        """ TODO """
        pass

    def genFourNotesShExtV(self):
        """ TODO """

        pass

#########################################################################################
#                                      FUNCTIONS                                        #
#########################################################################################

def addShellV(chordItem):
    """
    TODO
    Add notes for the Shell Voicing (both off 3rd and off-7th)
    and all related fields (lilypond, sound, etc.) to a chordItem
    :param chordItem:
    :return chordItem:
    """
    pass

def addGuideTonesVoicing(chordItem):
    """
    TODO
    Add notes for the Guide Tone (both off 3rd and off-7th)
    and all related fields (lilypond, sound, etc.) to a chordItem
    :param chordItem:
    :return chordItem:
    """
    return chordItem


def addFourNotesShExtVoicing(chordItem):
    """
    TODO
    Add notes for the FourNotesShExt voicing (both off 3rd and off-7th)
    and all related fields (lilypond, sound, etc.) to a chordItem
    :param chordItem:
    :return chordItem:
    """
    return chordItem


def main():
    # Reading the chords data into a dictionary indexed
    # with the field names from the first row of the chords data file

    # instantiate constants
    chordsDatafile,  model_id, deck_id, deckName, deckFileName, engl2ItNotes, it2EnglNotes, soundfont = initGlobals()
    ankiFields, ankiNotes, chordsData = initVariables()
    lilypondTemplate = getLilyPondTempl()

    # read Chords data from csv file
    with open(chordsDatafile, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"', restval='pippo', restkey='leftOver')
        for row in reader:
            chordsData.append(row)
        fields = chordsData[6].keys()
        # # Testing
        # for x, y in zip(fields, list(chordsData[0].values())):
        #   print(x, ' --> ' , y)
        # for x in chordsData:
        #   print('x --> ', len(fields), ' and ', len(list(chordsData[0].values())))
        # print('Row length = ', len(list(row.values())))
        # print(fields)

    ##################################################################################
    # Add the Lilypond code                                                          #
    ##################################################################################


    chordsData = addLilypondVoicings(chordsData, lilypondTemplate)
    for chord in chordsData:
        chord = useProperMusicNotation(chord)

    ##################################################################################
    # Generate and add image files from Lilypond code                                #
    # TODO                                                                          #
    ##################################################################################
    chordsData = genLilypondImg(chordsData)

    ##################################################################################
    # Generate and add sound files from Lilypond-produced MIDi code                  #
    # TODO                                                                          #
    ##################################################################################

    chordsData = genSoundFiles(chordsData)


    ##################################################################################
    # End of ABC code                                                                #
    ##################################################################################

    # creating the list of anki fields from the field names

    for field in fields:
        ankiFields.append({'name': field})

    # print(ankiFields)

    # print(chordsData[5])

    chord_model = createChordModel(ankiFields, model_id)

    # i=1
    # for line in zip(fields,list(chordsData[1].values())):
    #   print(i, '--> field name and value: ', line)
    #   i = i+1

    # Generating the notes as list
    for row in chordsData:
        ankiNotes.append(genanki.Note(
            model=chord_model,
            fields=list(row.values())))
    # print(ankiNotes[1])

    #
    # Creating the ankideck
    #
    ankiChordsDeck = genanki.Deck(
        deck_id,
        deckName)
    #

    # Adding the notes to the deck
    #
    #
    for note in ankiNotes:
        ankiChordsDeck.add_note(note)

    # # Packing the deck and saving it
    genanki.Package(ankiChordsDeck).write_to_file(deckFileName)
    print(len(ankiNotes), "cards generated and saved into deck ", deckFileName)

def genSoundFiles(chordsData):
    """
    TODO
    Generate sound files from the Lilypond-generated MIDI file, and store the src link in the
    appropriate field of chordsData items
    :param chordsData:
    :return:
    """
    return chordsData


def genLilypondImg(chordsData):
    """
    TODO
    Generate score image from the Lilypond code and store the src img link in the appropriate field
    :param chordsData:
    :return:
    """
    return chordsData


def createEnglItTransDicts():
    """
    Instantiate two dictionaries for English to Italian and Italian to English translations
    of note names, including a version with unicode symbols for sharps and flats
    """

    engl2ItNotes= dict(A="La", Af="Lab", As="Lad", B="Si", Bf="Sib", Bs="Sid", C="Do", Cf="Dob", Cs="Dod", D="Re", Df="Reb",
                   Ds="Red", E="Mi", Ef="Mib", Es="Mid", F="Fa", Fs="Fad", Ff="Fab", G="Sol", Gs="Sold", Gb="Solb")
    it2EnglNotes= {y: x for x, y in engl2ItNotes.items()}

    for key, note  in engl2ItNotes.items():
        oldNote = note
        note = re.sub(r"b$","\u266D",note)
        note = re.sub(r"d$","\u266F",note)
        engl2ItNotes[key]=[oldNote,note]

    for key, note  in it2EnglNotes.items():
        oldNote = note
        note = re.sub(r"f$","\u266D",note)
        note = re.sub(r"s$","\u266F",note)
        it2EnglNotes[key]=[oldNote,note]
    return engl2ItNotes, it2EnglNotes


def createChordModel(ankiFields, model_id):
    """ Generate the model, i.e.,  the note type and the card templates
    """

    chord_model = genanki.Model(
        model_id,
        'Chords',
        fields=ankiFields,
        templates=[
            {
                'name': 'NotesRootless3',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Rootless shell voicing, <br> <bold>off 3rd</bold> for: </font><hr> <font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Rootless_V_Off_3rd}} <hr><center>{{Rootless_V_Off_3rd-lilypond}}</center>',
            },
            {
                'name': 'NotesRootless7',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Rootless shell voicing, <br> <bold>off 7th</bold> for: </font><hr><font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Rootless_V_Off_7th}}<hr><center>{{Rootless_V_Off_7th-lilypond}}</center>',
            },
            {
                'name': 'NotesGuideTones3',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Lead tones 3-note voicing, <br> <bold>off 3rd</bold> for: </font><hr><font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{GuideTones_V_Off_3rd}}<hr><center>{{GuideTones_V_Off_3rd-lilypond}}</center>',
            },
            {
                'name': 'NotesGuideTones7',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Lead tones 3-note voicing, <br> <bold>off 7th</bold> for: </font><hr><font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{GuideTones_V_Off_7th}}<hr><center>{{GuideTones_V_Off_7th-lilypond}}</center>',
            },

        ])
    return chord_model


def addLilypondVoicings(chordsData, lilypondTemplate):
    """Create voicings for all chords from the chord note a the Lilypond template"""

    tempChordsData = []  # Needed to copy the modified record over
    for chordItem in chordsData:
        # Proceeding in order:
        # Rootless Voicing off 3rd
        chordItem = addLilyRootlessVoicing(chordItem, 'Rootless_V_Off_3rd', lilypondTemplate)
        chordItem = addLilyRootlessVoicing(chordItem, 'Rootless_V_Off_7th', lilypondTemplate)
        chordItem = addLilyGuideToneVoicing(chordItem, 'GuideTones_V_Off_3rd', lilypondTemplate)
        chordItem = addLilyGuideToneVoicing(chordItem, 'GuideTones_V_Off_7th', lilypondTemplate)
        chordItem = addLilyShellExtVoicing(chordItem, 'FourNotesSh_Ext_V_Off_3rd', lilypondTemplate)
        chordItem = addLilyShellExtVoicing(chordItem, 'FourNotesSh_Ext_V_Off_7th', lilypondTemplate)
        tempChordsData.append(chordItem)
        print(chordItem['Name'], ' --> ',
              chordItem['Rootless_V_Off_3rd'], '-->',
              chordItem['Rootless_V_Off_3rd-lilypond'], '-->',
              chordItem['Rootless_V_Off_7th-lilypond'])
    chordsData = tempChordsData
    return chordsData


def getLilyPondTempl():
    """Return the template to be used in the LilyPond fields of all the chords.
        We bypass the templates the Anki lilypond add-on uses and provide our own.
    """

    return Template("""[lilypond=void]
                        \\paper{#(set-paper-size '(cons (* 100 mm) (* 50 mm)))
                                indent=0\\mm
                                oddFooterMarkup=##f
                                oddHeaderMarkup=##f
                                bookTitleMarkup = ##f
                                scoreTitleMarkup = ##f
                                } 
                         \\version "2.24.3"
                         \\language "italiano"
                         \\score {
                                  \\new GrandStaff
                                  <<
                                    \\new Staff \\relative  {$trebleClefNotes}
                                    \\new Staff \\relative {$bassClefNotes}
    
                                >>
                                \\layout {}
                                \\midi {}
                                }
                         [/lilypond]""")


def initVariables():
    """Define global variables"""
    chordsData= []  # Holds all the data about chords, partly read from file and partly generated here
    fieldNames = ['SortId', 'Name', 'Root', 'Quality', 'Chord',
                  'Rootless_V_Off_3rd', 'Rootless_V_Off_7th',
                  'Rootless_V_Off_3rd_RH', 'Rootless_V_Off_3rd_LH', 'Rootless_V_Off_3rd_RH', 'Rootless_V_Off_3rd_LH',
                  'Rootless_V_Off_3rd_LilyPond', 'Rootless_V_Off_3rd_LilyPond_Image', 'Rootless_V_Off_7th_LilyPond',
                  'Rootless_V_Off_7th_LilyPond_Image', 'Rootless_V_Off_3rd_ABC', 'Rootless_V_Off_3rd_ABC_mp3',
                  'Rootless_V_Off_7th_ABC', 'Rootless_V_Off_7th_ABC_mp3',
                  'GuideTones_V_Off_3rd', 'GuideTones_V_Off_7th', 'GuideTones_V_Off_3rd_RH', 'GuideTones_V_Off_3rd_LH',
                  'GuideTones_V_Off_3rd_RH', 'GuideTones_V_Off_3rd_LH', 'GuideTones_V_Off_3rd_LilyPond',
                  'GuideTones_V_Off_3rd_LilyPond_Image', 'GuideTones_V_Off_7th_LilyPond',
                  'GuideTones_V_Off_7th_LilyPond_Image', 'GuideTones_V_Off_3rd_ABC', 'GuideTones_V_Off_3rd_ABC_mp3',
                  'GuideTones_V_Off_7th_ABC', 'GuideTones_V_Off_7th_ABC_mp3', 'FourNotesSh_Ext_V_Off_3rd',
                  'FourNotesSh_Ext_V_Off_7th', 'FourNotesSh_Ext_V_Off_3rd_RH', 'FourNotesSh_Ext_V_Off_3rd_LH',
                  'FourNotesSh_Ext_V_Off_3rd_RH', 'FourNotesSh_Ext_V_Off_3rd_LH', 'FourNotesSh_Ext_V_Off_3rd_LilyPond',
                  'FourNotesSh_Ext_V_Off_3rd_LilyPond_Image', 'FourNotesSh_Ext_V_Off_7th_LilyPond',
                  'FourNotesSh_Ext_V_Off_7th_LilyPond_Image', 'FourNotesSh_Ext_V_Off_3rd_ABC',
                  'FourNotesSh_Ext_V_Off_3rd_ABC_mp3', 'FourNotesSh_Ext_V_Off_7th_ABC',
                  'FourNotesSh_Ext_V_Off_7th_ABC_mp3']

    ankiNotes = []  # Holds all the notes generated from chordsData
    ankiFields= []  # Holds the fields names for the anki model
    return chordsData, ankiNotes, ankiFields




def addLilyRootlessVoicing(chordRecord, voicing, lilyPattern, duration=1, octave="'"):
    """ Generate the lilypond string for the Rootless voicing off-3rd and off-7th
        based on the notes contained in, respectively, the Rootless_V_Off_3rd and
        Rootless_V_Off_7th fields (fieldname passed as parameter) of the chord record
        (chordRecord, passed as a parameter).
        Return the updated record."""

    treblePattern = Template('<< ${low}' + octave + str(duration) + ' ' + '${high}' + octave + str(duration)+'>>')
    bassPattern = Template('\\clef bass $low $high')
    notes = chordRecord[voicing]
    if notes.strip():
        notesList = notes.split()
        treble = treblePattern.substitute(low=notesList[0].lower(), high=notesList[1].lower())
        bass = bassPattern.substitute(low='r1 ', high=' ')
        lilypondCode = lilyPattern.substitute(trebleClefNotes=treble, bassClefNotes=bass)
        chordRecord[voicing+'-lilypond'] = html.escape(lilypondCode)
    return chordRecord


def addLilyGuideToneVoicing(chordRecord, voicing, lilyPattern, duration=1, octave="'"):
    """ Generate the lilypond string for the Guide tone voicings off-3rd and off-7th
        based on the notes contained in, respectively, the GuideTone_V_Off_3rd and
        GuideTone_V_Off_7th fields (fieldname passed as parameter) of the chord record
        (chordRecord, passed as a parameter).
        Return the updated record."""

    treblePattern = Template('<< ${low}' + octave + str(duration) + ' ' + '${high}' + octave + str(duration)+ ' >>')
    bassPattern = Template('\\clef bass $low')
    notes = chordRecord[voicing]
    if notes.strip():
        notesList = notes.split()
        treble = treblePattern.substitute(low=notesList[1].lower(), high=notesList[2].lower())
        bass = bassPattern.substitute(low=notesList[0].lower())
        lilypondCode = lilyPattern.substitute(trebleClefNotes=treble, bassClefNotes=bass)
        chordRecord[voicing+'-lilypond'] = html.escape(lilypondCode)
    return chordRecord


def addLilyShellExtVoicing(chordRecord, voicing, lilyPattern, duration=1, octave="'"):
    """ Generate the lilypond string for the Shell Extended voicings  off-3rd and off-7th
        based on the notes contained in, respectively, the FourNotesSh_Ext_V_Off_3rd and
        FourNotesSh_Ext_V_Off_7th fields (fieldname passed as parameter) of the chord record
        (chordRecord, passed as a parameter).
        Return the updated record.
        TODO
        """

    return chordRecord

def useProperMusicNotation(chordRecord):
    """ Replace accidental abbreviations with proper musical notation in root and voicing fields.
        Must be run after generation of lilypond code (lilypond relies on shorthand notation).
    """

    fields = ["Root_it", "Rootless_V_Off_3rd", "Rootless_V_Off_7th",
              "GuideTones_V_Off_3rd", "GuideTones_V_Off_7th",
              "FourNotesSh_Ext_V_Off_3rd", "FourNotesSh_Ext_V_Off_7th"]
    newChordRecord=chordRecord
    properNotationDict = dict(createEnglItTransDicts()[0].values())
    for field in fields:
        newField = []
        if len(newChordRecord[field]) > 0:
            for note in newChordRecord[field].split():
                print(field, ' --> ' ,note)
                newField.append(properNotationDict[note])
            newChordRecord[field]=' '.join(newField)
    return newChordRecord

if __name__ == '__main__':
    main()


#############################################################################
#############################################################################
#############################################################################
#############################################################################
# TEMP: COPIED OVER LILYPOND CODE FROM LILYPOND ADD_ON
#############################################################################
#############################################################################
#############################################################################
#############################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 Andreas Klauer <Andreas.Klauer@metamorpher.de>
# Copyright (c) 2019 Luca Panno <panno.luca@gmail.com>
# Copyright (c) 2024 Stefano Franchi <stefano.franchi@gmail.com>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/gpl.html

'''
LilyPond (GNU Music Typesetter) integration addon for Anki 2.1.x
Code is based on / inspired by libanki's LaTeX integration and Andreas Klauer's LiliPond integration add-ons.
'''
# http://lilypond.org/doc/Documentation/usage/lilypond-output-in-other-programs#inserting-lilypond-output-into-other-programs


########################## TESTS

#############################

# --- Imports: ---

#from anki.utils import call, checksum, strip_html, tmpfile
#from aqt import mw
#from aqt.qt import *
# from aqt.utils import getOnlyText, showInfo
from html.entities import entitydefs
#import cgi, os, re, shutil

from typing import Any
from typing import Dict

# from anki.cards import Card
# from anki.media import MediaManager
# from anki.models import NoteType
# from aqt.editor import Editor

#import subprocess
#from . import i18n
#_=i18n._
#from PyQt5.QtWidgets import QMessageBox

# # --- Globals: ---
#
# lilypondTmpFile = tmpfile("lilypond", ".ly")
# # lilypondCmd = ["lilypond", "-V", "-dbackend=eps", "-dno-gs-load-fonts", "-dinclude-eps-fonts", "--o", lilypondTmpFile, "--png", lilypondTmpFile]
# lilypondCmd = ["lilypond", "-V", "-dbackend=eps", "-dno-gs-load-fonts", "-dinclude-eps-fonts", "--o", lilypondTmpFile, "--png", lilypondTmpFile]
# lilypondPattern = "%ANKI%"
# lilypondSplit = "%%%"
# lilypondTemplate = """\\paper{
#   indent=0\\mm
#   line-width=120\\mm
#   oddFooterMarkup=##f
#   oddHeaderMarkup=##f
#   bookTitleMarkup = ##f
#   scoreTitleMarkup = ##f
# }
#
# \\relative c'' { %s }
# """ % (lilypondPattern,)
# lilypondTemplates = {}
# addonDir=__name__.split(".")[0]
# tplDir = os.path.join(mw.pm.addonFolder(),addonDir,"user_files")
# print("*** ly dir ***") ####debug
# print(tplDir) ####debug
# lilypondTagRegexp = re.compile(        # Match tagged code
#     r"\[lilypond(=(?P<template>[a-z0-9_-]+))?\](?P<code>.+?)\[/lilypond\]", re.DOTALL | re.IGNORECASE)
# lilypondFieldRegexp = re.compile(     # Match LilyPond field names
#     r"^(?P<field>.*)-lilypond(-(?P<template>[a-z0-9_-]+))?$", re.DOTALL | re.IGNORECASE)
# tplNameRegexp = re.compile(r"^[a-z0-9_-]+$", re.DOTALL | re.IGNORECASE) # Template names must match this
# imgTagRegexp = re.compile("^<img.*>$", re.DOTALL | re.IGNORECASE)  # Detects if field already contains rendered img
# imgFieldSuffix="-lilypondimg" # Suffix on LilyPond field destinations
# lilypondCache = {}
#
# # --- Templates: ---
#
# def tplFile(name):
#     '''Build the full filename for template name.'''
#     return os.path.join(tplDir, "%s.ly" % (name,))
#
# def setTemplate(name, content):
#     '''Set and save a template.'''
#     lilypondTemplates[name] = content
#     f = open(tplFile(name), 'w')
#     f.write(content)
#
# def getTemplate(name, code):
#     '''Load template by name and fill it with code.'''
#     if name is None:
#         name="default"
#
#     tpl = None
#
#     if name not in lilypondTemplates:
#         try:
#             tpl = open(tplFile(name)).read()
#             if tpl and lilypondPattern in tpl:
#                 lilypondTemplates[name] = tpl
#         except:
#             if name == "default":
#                 tpl = lilypondTemplate
#                 setTemplate("default", tpl)
#         finally:
#             if name not in lilypondTemplates:
#                 raise IOError("LilyPond Template %s not found or not valid." % (name,))
#
#     # Replace one or more occurences of lilypondPattern
#
#     codes = code.split(lilypondSplit)
#
#     r = lilypondTemplates[name]
#
#     for code in codes:
#         r = r.replace(lilypondPattern, code, 1)
#
#     return r
#
# # --- GUI: ---
#
# def templatefiles():
#     '''Produce list of template files.'''
#     return [f for f in os.listdir(tplDir)
#             if f.endswith(".ly")]
#
#
#     for f in templatefiles():
#         m = lm.addMenu(os.path.splitext(f)[0])
#         a = QAction(_("Edit..."), mw)
#         p = os.path.join(tplDir, f)
#         a.triggered.connect(lambda b,p=p: editFile(p))
#         m.addAction(a)
#         a = QAction(_("Delete..."), mw)
#         a.triggered.connect(lambda b,p=p: removeFile(p))
#         m.addAction(a)
#
# # --- Functions: ---
#
# def _lyFromHtml(ly):
#     '''Convert entities and fix newlines.'''
#
#     ly = re.sub(r"<(br|div|p) */?>", "\n", ly)
#     ly = strip_html(ly)
#
#     ly = ly.replace("&nbsp;", " ")
#
#     for match in re.compile(r"&([a-zA-Z]+);").finditer(ly):
#         if match.group(1) in entitydefs:
#             ly = ly.replace(match.group(), entitydefs[match.group(1)])
#
#     return ly
#
# def _buildImg(ly, fname):
#     '''Build the image PNG file itself and add it to the media dir.'''
#     lyfile = open(lilypondTmpFile, "w")
#     lyfile.write(ly.decode("utf-8"))
#     lyfile.close()
#
#     log = open(lilypondTmpFile+".log", "w")
#
# #    if call(lilypondCmd, stdout=log, stderr=log):
#     print("##################################")
#     print('#######   LILYPOND OUTPUT   ######')
#     print("##################################")
#     if call(lilypondCmd):
#         print("Lilypond file: ", lilypondTmpFile)
#         print("Image file: ", lilypondTmpFile+".png")
#         print("##################################")
#         print('#### END OF LILYPOND OUTPUT ######')
#         print("##################################")
#         if call(lilypondCmd):
#             return _errMsg("lilypond")
#
#     # add to media
#     try:
#         shutil.move(lilypondTmpFile+".png", os.path.join(mw.col.media.dir(), fname))
#         print(lilypondTmpFile+".png", "moved to ", os.path.join(mw.col.media.dir(), fname))
#     except:
#         # debugging
#         print("could note move file: ", lilypondTmpFile+".png", "to: ",  os.path.join(mw.col.media.dir(), fname))
#         return _("Could not move LilyPond PNG file to media dir. No output?<br>")+_errMsg("lilypond")
#
# def _imgLink(template, ly):
#     '''Build an <img src> link for given LilyPond code.'''
#
#     # Finalize LilyPond source.
#     ly = getTemplate(template, ly)
#     ly = ly.encode("utf8")
#
#     # Derive image filename from source.
#     fname = "lilypond-%s.png" % (checksum(ly),)
#     link = '<img src="%s" alt=%s>' % (fname,"")
#
#     # Build image if necessary.
#     if os.path.exists(fname):
#         return link
#     else:
#         # avoid erroneous cards killing performance
#         if fname in lilypondCache:
#             return lilypondCache[fname]
#
#         err = _buildImg(ly, fname)
#         if err:
#             lilypondCache[fname] = err
#             return err
#         else:
#             print("Link to source img created --> ", link)
#             return link
#
# def _errMsg(type):
#     '''Error message, will be displayed in the card itself.'''
#     msg = (_("Error executing %s.") % type) + "<br>"
#     try:
#         log = open(lilypondTmpFile+".log", "r").read()
#         if log:
#             msg += """<small><pre style="text-align: left">""" + cgi.escape(log) + "</pre></small>"
#     except:
#         msg += _("Have you installed lilypond? Is your lilypond code correct?")
#     return msg
#
# def _getfields(notetype: Union[NoteType,Dict[str,Any]]):
#     '''Get list of field names for given note type'''
#     return list(field['name'] for field in notetype['flds'])
#
# # --- Hooks: ---
#
# def _mungeString(text: str) -> str:
#     """
#         Replaces tagged LilyPond code with rendered images
#     :return: Text with tags substituted in-place
#     """
#     print('in _mungeString')
#     for match in lilypondTagRegexp.finditer(text):
#         lyCode = _lyFromHtml(match.group(lilypondTagRegexp.groupindex['code']))
#         tplName = match.group(lilypondTagRegexp.groupindex['template'])
#         print('About to replace text in field ', match.group())
#         text = text.replace(
#             match.group(), _imgLink(tplName, lyCode)
#         )
#     print('Out of _mungeString, returning --> ', text)
#     return text
#
#
# def mungeCard(html: str, card: Card, kind: str):
#     print('In mungeCard')
#     if kind.startswith(cardEditorPrefix):
#         # In card editor, may contain invalid but tagged LilyPod code
#         return html
#     return _mungeString(html)
#
# # This is the function that does not work and needs to be changed, possibly using _mungeString instead,
# # or changing the definition to reflect the argument that card_will_show will pass to it
# # (namely: html: str, card: Card, kind: str as per mungeCard). Need to check out the definition of the class Card
# def mungeFields(txt: str, editor: Editor):#fields, model, data, col):
#     '''Parse lilypond tags before they are displayed.'''
#     # Fallback if it can't identify current field
#     # Substitute LilyPond tags
#
#     print('in mungeFields')
#     if editor.currentField is None:
#         return txt
#     fields: list[str] = _getfields(editor.note.model())
#     print('fields: ',fields)
#     field: str = fields[editor.currentField]
#     print('field: ', field)
#     if fieldMatch := lilypondFieldRegexp.match(field):
#         tplName = fieldMatch.group(lilypondFieldRegexp.groupindex['template'])
#         # This is where the function chain to the eventual call to lilypond starts
#         # _imgLink --> _buildImg (which calls it) and returns a link to the image source
#         # Check it the add-on can actually find the image source field:
#         print("The image destination field is: ", fieldMatch.group(lilypondFieldRegexp.groupindex['field']) + imgFieldSuffix,  " Does it exist?")
#         #
#         imgLink= _imgLink(tplName, _lyFromHtml(txt)) if txt != "" else "" # Check to avoid compiling empty templates
#         if (destField := fieldMatch.group(lilypondFieldRegexp.groupindex['field']) + imgFieldSuffix) in fields:
#             # This is where the image gets copied to the image field.
#             # Target field exists, populate it
#             editor.note[destField] = imgLink
#             print('I populated the image field ', destField)
#             return txt
#         else:
#             # Substitute in-place
#                 if imgTagRegexp.match(txt):
#                 # Field already contains rendered image
#                     return txt
#                 else:
#                   return imgLink
#     elif field.endswith(imgFieldSuffix):
#         print('I am in the image field')
#         # Field is a destination for rendered images, won't contain code
#         return txt
#     else:
#         # Normal field
#         # Substitute LilyPond tags
#         return _mungeString(txt)
#






