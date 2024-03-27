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
    roots = ['Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F', 'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#']
    qualities = ['M7', 'm7', 'dom7', 'm7b5']
    voicings = ['FullStandardV', 'ShellV', 'GuideTones', 'FourNotesShExt']
    newchordsData = createChordItems((roots,qualities))

    # for fieldNames generation in chordItems
    extraFields = 'sortId'

#########################################################################################
#                                      CLASSES                                          #
#########################################################################################
class GenAnkiChords():
    """
    Contains the main logic of the app
    General flow is as follows:
    1. Generate the Chord and Voicing database:
        - Generate the skeleton of a chord database as a row per each root plus quality
        - Populate the "chord db" with voicings
        - Generate a unique ID for each row as hash of a few chosen fields
    2. Convert the chord database to Anki notes:
        - Create Anki model with appropriate Anki fields for each "column" in the db
        - Convert db's rows into notes
        - Create anki package from notes
    3. Prepare package for upload:
        - Move media files to correct location
        - Move Anki package to correct location

    """

    def __init__(self, roots, qualities, voicings):
        """
        Initialize variables and all the parameters of the app, then build all the ChordItems
        """
        self.roots = roots
        self.qualities = qualities
        self.voicings = voicings
        self.chordsDb = {}

    def initDb(self):
        # create the chordsDb with a row for each chord as a chordItem
        self.chordsDb = {r+q:ChordItem(r,q) for r in self.roots for q in self.qualities}


    def addVoicings(self):
        """
        Create all voicings for each chordItem
        :return:
        """
        for chordItem in self.chordsDb.values():
            for voicing in self.voicings:
                chordItem.addVoicing(voicing)


@dataclass
class ChordItem(object):
    __slots__ = ['id' 'sortId', 'name', 'root', 'quality', 'chord', 'inversion', 'voicingsNeeded', 'voicings']

    def __init__(self,root, quality,voicings=[]):
        self.root = root
        self.quality = quality
        self.voicingsNeeded = voicings # The list of voicings this instance can generate
        self.voicings = {}  # The dictionary actually containing the voicings
        self.name = self.addName()

    def addName(self):
        """
        Construct the chord name. Now using a simple concatenation, may change later
        :param root:
        :param quality:
        :return: name
        """
        return self.root+'-'+self.quality

    def genVoicings(self, voicing):
        """Generate all the voicings for each chordItem"""
        for voicing in self.voicings:
            v = self.addVoicing(voicing)
        return True

    def addVoicing(self, voicing):
        """
            Add a voicing (including all necessary media files) to the chordItem
            :return: True if successful
        """
        try:
            newVoicing = Voicing(self.root,self.quality)
            genVoicingMethod = getattr(Voicing,'gen'+voicing)
            genVoicingMethod(newVoicing)
            self.voicings[voicing]=(newVoicing)
            return True
        except AttributeError:
            raise NotImplementedError(
                "Class `{}` does not implement `{}`".format(Voicing.__class__.__name__, genVoicingMethod))



@dataclass
class Voicing():
    """
    TODO: Add translations of notes for every voicing
    TODO: add generation of fingering (from construction of keyboard on)
    TODO: complete shell voicing generation
    TODO: add guide tones voicing generation
    TODO: add four notes shell extended voicing
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

    ############### Utilities methods ######################################
    def barToMp3(self, bar, mp3FileOut: str, bpm=80):
        """ TODO: Find out while .wav and .mp3 files don't get closed"
        Convert a mingus bar to mp3 file using pydub and fluidsynth"""
        tempMIDIout = 'tmpMidi.mid'
        tempAudioOut =   'tmpWav.wav'
        try:
            mMidiFileOut(tempMIDIout, bar, bpm)
            p = subprocess.run(["fluidsynth", "-ni", '/usr/share/soundfonts/FluidR3_GM.sf2', tempMIDIout, "-F", tempAudioOut])
            print('flac file written as: ', tempAudioOut, "with results: ", p)
        except:
            print('Conversion of MIDI to flac failed')

        # read back wav and save it as mp3 with pydub
        try:
            temp = AudioSegment.from_wav(tempAudioOut)
            temp.export(mp3FileOut, format="mp3")
            sndTag = '<snd src="'+mp3FileOut+'" \\>'
            print('mp3 file written out as: ', mp3FileOut)
            return sndTag
        except:
            print('mp3 production failed')


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
                                        \\new Staff   {\\set fingeringOrientations = #'(up) <$trebleClefNotes>1}
                                        \\new Staff   {\\set fingeringOrientations = #'(down) \\clef bass <$bassClefNotes>1}

                                    >>
                                    \\layout {}
                                    \\midi {}
                                    }
                                    """)
        return templ

    #########################    Methods ###############################################################

    def genShellV(self):
        """ Generate lilypond, mp3, png, and fingerings for both off-3rd and off-7th  shell voicings"""
        self.shellVOff3rdLilypond = self.genShellVOff3rdLilyPond()
        self.shellVOff7thLilypond = self.genShellVOff7thLilyPond()

    def genFullStandardV(self):
        """ Generate lilypond, mp3, png, and fingerings for standard root position voicing of a 4 notes 7th chord"""
        self.fullStandardVLilyPond = self.genFullStandardVLilyPond()
        self.fullStandardVPng = self.genFullStandardVPng()
        self.fullStandardVMp3 = self.genFullStandardVMp3()
        self.fullStandardVFingering = self.genFullStandardVFingering()


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
        lilyPondString = self.lilyPondTemplate.substitute(bassClefNotes = "c-1", trebleClefNotes = "e'-1 g'-3 b'-5")
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

    def genFullStandardVMp3(self):
        "Use mingus to generate the mp3 file for the voicing from its chord"
        fileOut = self.root+self.quality+'-FullStandardV'+'.mp3'
        bar = mBar()
        bar.place_notes(mNote_container(self.genFullStandardVNotes()), 1)
        sndTag = self.barToMp3(bar, fileOut)
        return sndTag

    def genFullStandardVFingering(self):
        """TODO: use DrawSVG lib for both SVG production and rasterization (d.rasterize())
        Generate the svg file fo the keyboard with highlighted fingerings for both RH and LH"""


    def genGuideTonesV(self):
        """ TODO write genGuideTonesV """
        pass

    def genFourNotesShExtV(self):
        """ TODO write genFourNotesShExtV """
        pass


class ChordNote(genanki.Note):
    """
    Holds an Anki note to be added to an Anki Deck.
    We need to subclass the Note in order to use a custom function to generate the note ID
    (and therefore ensure possibly updated notes with additional fields in subsequent
    generations of the deck will not replace the old notes).
    """
    @property
    def guid(self):
        return genanki.guid_for(self.fields[1],self.fields[2])

class AnkiDeck(object):
    """
    Holds all the components of an Anki Deck to be packaged and saved to disk
    """
    def __init__(self, chordsDb :GenAnkiChords.chordsDb, mediaDir):
        """
        Instantiates the main instance variable to a chords database and creates an Anki deck
        :param chordsDb:
        """
        self.chordsDb = chordsDb
        self.mediaDir = mediaDir
    def genDeckFromChordsDb(self):
        self.filename = self.genFilename()
        self.fields = self.getFieldsFromChordsDb()
        self.createChordModel()
        self.engl2ItNotes, self.it2EnglNotes = self.createEnglItTransDicts()
        self.useProperMusicNotation()
        self.ankiDeck = self.createAnkiDeck()
        self.addCardsToDeck()


    def createAnkiDeck(self):
        ankiChordsDeck = genanki.Deck(
            self.deckId,
            self.deckName)
        return  ankiChordsDeck

    def addCardsToDeck(self):
        """
        TODO: write addCardsToDeck
        create notes from chordsDb and add them to ankiDeck
        :return:
        """
        pass

    def saveDeck(self):
        """
        Packages the ankiDeck  as .apkg file and saves it to disk
        :return:
        """
        genanki.Package(self.ankiDeck).write_to_file(self.fileName)
        print(len(self.ankiNotes), "cards generated and saved into deck ", self.fileName)

    def moveMediaToMediaDir(self):
        """
        TODO: write function moveMediaToMediaDir
        Extract all filenames from img tags in relevant voicing fields and move them to self.mediaDir
        """
        pass

    def getFieldsFromChordsDb(self):
        """
        Extracts the fields from the chordsDb database
        """
        fields = '' # main function goes here
        return fields

    def createChordModel(self):
        """ Generate the model, i.e.,  the note type and the card templates
        """

        chordModel = genanki.Model(self.modelId,'Chords',fields=self.fields,
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
        return chordModel

    def createEnglItTransDicts(self):
        """
        Instantiate two dictionaries for English to Italian and Italian to English translations
        of note names, using proper unicode symbols for sharps and flats
        """

        engl2ItNotes = dict(A="La", Af="Lab", As="Lad", B="Si", Bf="Sib", Bs="Sid", C="Do", Cf="Dob", Cs="Dod", D="Re",
                            Df="Reb",
                            Ds="Red", E="Mi", Ef="Mib", Es="Mid", F="Fa", Fs="Fad", Ff="Fab", G="Sol", Gs="Sold",
                            Gb="Solb")
        it2EnglNotes = {y: x for x, y in engl2ItNotes.items()}

        for key, note in engl2ItNotes.items():
            oldNote = note
            note = re.sub(r"b$", "\u266D", note)
            note = re.sub(r"d$", "\u266F", note)
            engl2ItNotes[key] = [oldNote, note]

        for key, note in it2EnglNotes.items():
            oldNote = note
            note = re.sub(r"f$", "\u266D", note)
            note = re.sub(r"s$", "\u266F", note)
            it2EnglNotes[key] = [oldNote, note]
        return engl2ItNotes, it2EnglNotes

    def useProperMusicNotation(self):
        """
        TODO: fix function to work as a method of class AnkiDeck
        Replace accidental abbreviations with proper musical notation in root and voicing fields.
        """

        fields = ["Root_it", "Rootless_V_Off_3rd", "Rootless_V_Off_7th",
                  "GuideTones_V_Off_3rd", "GuideTones_V_Off_7th",
                  "FourNotesSh_Ext_V_Off_3rd", "FourNotesSh_Ext_V_Off_7th"]
        newChordRecord = chordRecord
        properNotationDict = dict(createEnglItTransDicts()[0].values())
        for field in fields:
            newField = []
            if len(newChordRecord[field]) > 0:
                for note in newChordRecord[field].split():
                    print(field, ' --> ', note)
                    newField.append(properNotationDict[note])
                newChordRecord[field] = ' '.join(newField)
        return newChordRecord

