GenAnkiChords create a new Anki deck of cards for commonly used jazz chords and voicings.

The data about the chords are mostly drawn from Phil DeGreg's 
_Jazz Keyboard Harmony_ (New Albany, Ind., Jamey Aebersold Jazz, 1992). 
They are stored in the csv file ChordsData.csv 
(currently produced from a spreadsheet). 


GenAnkiChords uses the Python package genanki for the creation and 
manipulation of the Anki deck, and it can use the Anki add-ons [Lilypond integration](https://ankiweb.net/shared/info/123418104)
and [ABC integration](https://ankiweb.net/shared/info/203713821) to generate a lilypond-generated score representation 
of the chords and an ABC-generated mp3 file with the chords' sounds.

A call to chord-generation.py will read the data from the csv file 
and produce an Anki-readable deck ("Comping-Chords.apkg") 