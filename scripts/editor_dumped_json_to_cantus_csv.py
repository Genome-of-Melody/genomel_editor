#!/usr/bin/env python
"""This is a script that just reformats the JSON dump from the editor
(django manage.py dump) into the CantusCorpus-format CSV file."""

import argparse
import logging
import time

import pprint
import json
import csv

__version__ = "0.0.1"
__author__ = "Jan Hajic jr."


def is_complete_melody(melody, minimum_length=10,
                       check_adiastematic=True, check_incomplete_in_source=True):
    """Returns True if the melody is complete, False otherwise."""
    fields = melody['fields']
    if check_adiastematic and fields['is_adiastematic']:
        return False
    if check_incomplete_in_source and fields['is_incomplete_in_source']:
        return False
    volpiano = fields['volpiano']
    if len(volpiano) < minimum_length:
        return False
    return True




def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--input_json', '-i', type=str, required=True,
                        help='Path to the JSON file with the editor dump.')
    parser.add_argument('--output_csv', '-o', type=str, required=True,
                        help='Path to the output CSV file in CantusCorpus format.')
    parser.add_argument('--chant_csv_example', '-c', type=str, required=True,
                        help='Chant CSV that is in the desired format. From this, we will'
                             ' derive the order of fields in the output CSV.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()

    # Load input JSON
    with open(args.input_json, 'r') as fh:
        editor_dump = json.load(fh)

    # Collect 'chant' records from JSON.
    chants = [record for record in editor_dump
              if record['model'] == 'GenomelEditor.chant']

    # Collect 'melody' records from JSON.
    melodies = [record for record in editor_dump
                if record['model'] == 'GenomelEditor.melody']
    # Filter out incomplete melodies. For this filtering, we use the default values.
    complete_melodies = [melody for melody in melodies
                         if is_complete_melody(melody)]

    # Assign 'melody' records from JSON to their chants.
    #pprint.pprint(complete_melodies[0])
    #pprint.pprint(chants[0])

    chants_dict = {chant['pk']: chant for chant in chants}
    chants_with_melodies = []
    for melody in complete_melodies:
        chant_pk = melody['fields']['chant']
        chant = chants_dict[chant_pk]
        chant['fields']['volpiano'] = melody['fields']['volpiano']
        chants_with_melodies.append(chant)

    # How many chants have complete melodies assigned?
    logging.info('Found {0} chants with complete melodies.'.format(len(chants_with_melodies)))

    # Write out the CSV.
    #  - Load the "template" csv
    reader = csv.DictReader(open(args.chant_csv_example, 'r'))
    fieldnames = reader.fieldnames

    #  - Check fieldnames
    logging.debug('---- Fieldnames in the example CSV:')
    logging.debug(' '.join(sorted(fieldnames)))
    logging.debug('  In the original order: {0}'.format(fieldnames))
    logging.debug('---- Fieldnames in the chants with melodies:')
    logging.debug(' '.join(sorted(chants_with_melodies[0]['fields'].keys())))

    fieldnames_not_in_template = set(chants_with_melodies[0]['fields'].keys()) - set(fieldnames)
    fieldnames_not_in_chants = set(fieldnames) - set(chants_with_melodies[0]['fields'].keys())
    logging.info('Fieldnames not in the template CSV: {0}'.format(fieldnames_not_in_template))
    logging.info('Fieldnames not in the chants with melodies: {0}'.format(fieldnames_not_in_chants))

    # - Write the CSV, with the fieldnames in the order of the template CSV.
    writer = csv.DictWriter(open(args.output_csv, 'w'), fieldnames=fieldnames)
    writer.writeheader()
    # Write out the chants sorted by their ID (the primary key in the chants table
    # in the database). This makes the output easier to work with.
    for chant in sorted(chants_with_melodies, key=lambda x: x['pk']):
        # For the 'id' field in the template CSV (CantusCorpus standard but not part
        # of the data model for chant in GenomelEditor), use the 'pk' of the chant.
        chant['fields']['id'] = chant['pk']
        for fieldname in fieldnames_not_in_template:
            if fieldname in chant['fields']:
                del chant['fields'][fieldname]
        writer.writerow(chant['fields'])

    _end_time = time.process_time()
    logging.info('editor_dumped_json_to_cantus_csv.py done in {0:.3f} s'.format(_end_time - _start_time))


if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
