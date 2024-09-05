# genomel_editor

Volpiano editor for Genome of Melody annotations.

## Exporting data on the server

The data from a Django server can be exported from the commandline using the `dumpdata` command. 
This command will export the data in JSON format. 

```bash
python manage.py dumpdata --indent 2 > ../exports/2024-05-27_everything.json
```


## Postprocessing

The JSON with everything (including user data, unprocessed melodies, etc.)
then has to be postprocessed into a CantusCorpus-style CSV file.
This is done with the `scripts/editor_dumped_json_to_cantus_csv.py` script.
(See the script's `--help` for more usage.)

Once this CSV file that contains (presumably) only chant records with transcribed
melodies is ready, the next step is to prepare it for the `divtime_christmas` pipeline.
This is done with the `scripts/cantus_csv_to_divtime_christmas_fastas.py` script,
which produces a series of FASTA files into a target directory: one for each Cantus ID,
with the source IDs (normalized siglum) as the FASTA headers, and the melody in Volpiano
(including neume, syllable and word breaks, but other non-note characters are stripped).
