# Simple file to generate an Anki deck for chords
#
# (c) Stefano Franchi <Stefano.franchi@gmail.com>
#
# License GPL

# Import the library needed to manipulate and create an Anki deck
import genanki
import csv
from string import Template
import html

# Constants
chordsDatafile = "ChordsData.csv"
model_id = 1149467492  # randomly generated with import random; random.randrange(1 << 30, 1 << 31)
deck_id = 1393751746  # randomly generated with import random; random.randrange(1 << 30, 1 << 31)
deckName = "Comping Chords"
deckFileName = "Comping-Chords.apkg"

def main():
    # Reading the chords data into a dictionary indexed
    # with the field names from the first row of the chords data file

    # Variables
    chordsData = []  # Holds all the data about chords, partly read from file and partly generated here
    ankiNotes = []  # Holds all the notes generated from chordsData
    ankiFields = []  # Holds the fields names for the anki model

    with open(chordsDatafile, newline='') as csvfile:
        # reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        # fields = next(reader)
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
    # Adding the lilypond code                                                       #
    ##################################################################################

    # The template, chords.ly,  is provided within the Anki lilypond add-on,
    # and stored in: /home/stefano/.local/share/Anki2/addons21/123418104/user_files/chords.ly
    # but it is copied here for reference:

    # \version "2.24.3"
    # \language "italiano"
    # #(set-global-staff-size 24)
    #
    # \paper{
    #   indent=0\mm
    #   line-width=120\mm
    #   oddFooterMarkup=##f
    #   oddHeaderMarkup=##f
    #   bookTitleMarkup = ##f
    #   scoreTitleMarkup = ##f
    # }
    #
    # \relative c'' { %ANKI% }

    # As the code to be put into the lilypond fields is not easily abstracted,
    # a different pattern must be provided for every single field.
    # The simple pattern is as follows (illustrated for A7, shell voicing off 3rd):
    #
    # Notice that the durations and octave placements of the pitches must be added,
    # and are voicing-dependents.
    #
    # \version "2.24.3"
    # \language "italiano"
    #
    # \score {
    #           \new GrandStaff
    #         <<
    #         \new Staff \relative  {dod'1 }
    #         \new Staff \relative {sol1 }
    #
    #         >>
    #         \midi {}
    #         }
    #
    # This structure leads well to the use of the Template class,
    # with only two placeholders needed, trebleClefNotes and bassClefNotes.
    # Notice that:
    # - The score will always have two staves, even when only the top one will be used
    # - Durations and octave placement must be added to the pitches
    # - The clef directive is NOT included in the template and must be added

    # Template for all patterns:
    lilypondString = """[lilypond=chords] 
                         \\version "2.24.3"
                         \\language "italiano"
                         \\score {
                                  \\new GrandStaff
                                  <<
                                    \\new Staff \\relative  {$trebleClefNotes}
                                    \\new Staff \\relative {$bassClefNotes}
    
                                >>
                                \\midi {}
                                }
                         [/lilypond]"""
    lilypondTemplate = Template(lilypondString)

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
              chordItem['Rootless_V_Off_3rd_lilypond'], '-->',
              chordItem['Rootless_V_Off_7th_lilypond'])

    chordsData = tempChordsData

    ##################################################################################
    # End of Lilypond code                                                           #
    ##################################################################################

    ##################################################################################
    # Adding the ABC code       (PERHAPS ADD A CONVERSION FROM LILYPOND MIDI?)       #
    ##################################################################################

    # STILL MISSING

    ##################################################################################
    # End of ABC code                                                                #
    ##################################################################################

    # creating the list of anki fields from the field names

    for field in fields:
        ankiFields.append({'name': field})

    # print(ankiFields)

    # print(chordsData[5])

    # Generating the model, i.e.,  the note type and the templates
    #
    chord_model = genanki.Model(
        model_id,
        'Chords',
        fields=ankiFields,
        templates=[
            {
                'name': 'NotesRootless3',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Rootless shell voicing, <br> <bold>off 3rd</bold> for: </font><hr> <font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Rootless_V_Off_3rd}} <hr><center>{{Rootless_V_Off_3rd_lilypond}}</center>',
            },
            {
                'name': 'NotesRootless7',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Rootless shell voicing, <br> <bold>off 3rd</bold> for: </font><hr><font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Rootless_V_Off_7th}}<hr><center>{{Rootless_V_Off_7th_lilypond}}</center>',
            },
            {
                'name': 'NotesGuideTones3',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Lead tones 3-note voicing, <br> <bold>off 3rd</bold> for: </font><hr><font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{GuideTones_V_Off_3rd}}<hr><center>{{GuideTones_V_Off_3rd_lilypond}}</center>',
            },
            {
                'name': 'NotesGuideTones7',
                'qfmt': '<center><font size=8>Notes in </font><hr> <font size=14>Rootless shell voicing, <br> <bold>off 3rd</bold> for: </font><hr><font size=16>{{Name}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{GuideTones_V_Off_7th}}<hr><center>{{GuideTones_V_Off_7th_lilypond}}</center>',
            },

        ])

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

#########################################################################################
#                                      FUNCTIONS                                        #
#########################################################################################


def addLilyRootlessVoicing(chordRecord, voicing, lilyPattern, duration=1, octave="'"):
    """ Generate the lilypond string for the Rootless voicing off-3rd and off-7th
        based on the notes contained in, respectively, the Rootless_V_Off_3rd and
        Rootless_V_Off_7th fields (fieldname passed as parameter) of the chord record
        (chordRecord, passed as a parameter).
        Return the updated record."""

    treblePattern = Template('${low}' + octave + str(duration) + ' ' + '${high}' + octave + str(duration))
    bassPattern = Template('\\clef bass $low $high')
    notes = chordRecord[voicing]
    if notes.strip():
        notesList = notes.split()
        treble = treblePattern.substitute(low=notesList[0], high=notesList[1])
        bass = bassPattern.substitute(low=' ', high=' ')
        lilypondCode = lilyPattern.substitute(trebleClefNotes=treble, bassClefNotes=bass)
        chordRecord[voicing] = html.escape(lilypondCode)
    return chordRecord


def addLilyGuideToneVoicing(chordRecord, voicing, lilyPattern, duration=1, octave="'"):
    """ Generate the lilypond string for the Guide tone voicings off-3rd and off-7th
        based on the notes contained in, respectively, the GuideTone_V_Off_3rd and
        GuideTone_V_Off_7th fields (fieldname passed as parameter) of the chord record
        (chordRecord, passed as a parameter).
        Return the updated record."""

    treblePattern = Template('${low}' + octave + str(duration) + ' ' + '${high}' + octave + str(duration))
    bassPattern = Template('\\clef bass $low')
    notes = chordRecord[voicing]
    if notes.strip():
        notesList = notes.split()
        treble = treblePattern.substitute(low=notesList[1], high=notesList[2])
        bass = bassPattern.substitute(low=notesList[0])
        lilypondCode = lilyPattern.substitute(trebleClefNotes=treble, bassClefNotes=bass)
        chordRecord[voicing] = html.escape(lilypondCode)
    return chordRecord


def addLilyShellExtVoicing(chordRecord, voicing, lilyPattern, duration=1, octave="'"):
    """ Generate the lilypond string for the Shell Extended voicings  off-3rd and off-7th
        based on the notes contained in, respectively, the FourNotesSh_Ext_V_Off_3rd and
        FourNotesSh_Ext_V_Off_7th fields (fieldname passed as parameter) of the chord record
        (chordRecord, passed as a parameter).
        Return the updated record.
        TO DO
        """

    return chordRecord

if __name__ == '__main__':
    main()
