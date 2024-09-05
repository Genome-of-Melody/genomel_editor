#!/usr/bin/env python
"""This is a script that produces a series of FASTA files into a target directory: one for each Cantus ID,
with the source IDs (normalized siglum) as the FASTA headers, and the melody in Volpiano
as just the cleaned note sequence (gaps do not play a role in the divtime_christmas pipeline).
This creates inputs to the divtime_christmas pipeline.

Applied volpiano cleaning steps:

- Discard differentiae
- Normalize liquescents
- Normalize flats: omit notes, apply only once
- Remove all non-note characters

Sigla that are used as sequence headers in the output FASTA files are cleaned as well.

- Dots, slaches, and whitespace are replaced with underscores.
- Parentheses, semicolons, and other special characters are removed.

The output FASTA files have no empty lines.
"""

import argparse
import functools
import logging
import os.path
import time

import csv

import pycantus.volpiano.utils as volpiano_utils

__version__ = "0.0.1"
__author__ = "Jan Hajic jr."


def clean_volpiano_for_divtime_christmas(volpiano):
    '''Apply volpiano cleaning steps:

    - Discard differentiae
    - Normalize liquescents
    - Normalize flats: omit notes, apply only once
    - Remove all non-note characters
    '''
    # Discard differentiae
    volpiano = volpiano_utils.discard_differentia(volpiano)
    # Normalize liquescents
    volpiano = volpiano_utils.normalize_liquescents(volpiano)
    # Normalize accidentals: omit notes, apply only once
    volpiano = volpiano_utils.expand_accidentals(volpiano,
                                                 omit_notes=True, apply_once_only=True)
    # Remove all non-note characters
    volpiano = volpiano_utils.clean_volpiano(volpiano,
                                             keep_bars=False,
                                             keep_boundaries=False)
    return volpiano


@functools.lru_cache(maxsize=1024)
def siglum_to_fasta_header_name(siglum):
    '''Formats a siglum to a string that can be used as a FASTA header.
    This means discarding all special characters, and changing all whitespace to underscores,
    to make compatibility with any FASTA-reading software more likely.
    '''
    siglum = siglum.replace('.', '_')  # Dots often separate elements of a numbering system
    siglum = siglum.replace(',', '_')  # Dots often separate elements of a numbering system
    siglum = siglum.replace('/', '_')  # Slashes as well.
    siglum = siglum.replace(':', '')   # Semicolons are usually only separators between RISM ID part and rest of siglum.
    siglum = siglum.replace('(', '')   # Parentheses are not important separators
    siglum = siglum.replace(')', '')
    siglum = siglum.replace('<', '')
    siglum = siglum.replace('>', '')
    siglum = siglum.replace('"', '')
    siglum = siglum.replace("'", "")
    siglum = siglum.replace(";", "")
    siglum = siglum.replace('-', '_')  # Unfortunately, dashes from RISM sigla like CZ-Pu can also be risky.

    siglum = siglum.replace(' ', '_')
    return siglum


def compute_occurence_table(chants_by_cantus_id):
    """Computes the occurence table: for each source (identified by its 'siglum' field),
    and for each available Cantus ID, the table has a 0/1 depending on whether the Cantus ID
    is found in that source.

    This table can then be used e.g. to filter out sources with too few chants.

    :param chants_by_cantus_id: A dictionary mapping Cantus IDs to lists of chants.
        The chants are dicts from the CantusCorpus CSV, obtained via CSV DictReader.
        They are expected to have the 'siglum' field.

    :returns: A tuple `(all_cids, all_sigla, occurences_table)`, where:
        - all_cids is a list of all Cantus IDs found in the input data (sorted so that it can
          serve as a column header in the occurences table)
        - all_sigla is a list of all sigla found in the input data (sorted so that it can
          the i-th siglum in the list corresponds to the i-th row of the occurences table),
        - occurences_table is a list of lists, where each inner list corresponds to a siglum,
          and the j-th element of that list is 1 if the j-th Cantus ID is found in the source
          and 0 otherwise.
    """
    # Prepare table row (sigla) and column (cid) labels.
    all_sigla = []
    for cid in chants_by_cantus_id:
        chants = chants_by_cantus_id[cid]
        sigla = set(chant['siglum'] for chant in chants)
        all_sigla.extend(sigla)
    all_sigla = list(sorted(set(all_sigla)))
    all_cids = list(sorted(chants_by_cantus_id.keys()))

    # Prepare table
    occurences_table = [[0 for cid in all_cids] for siglum in all_sigla]

    # Fill table
    for j, cid in enumerate(all_cids):
        chants = chants_by_cantus_id[cid]
        for chant in chants:
            siglum = chant['siglum']
            i = all_sigla.index(siglum)
            occurences_table[i][j] = 1

    return all_cids, all_sigla, occurences_table


##################################################################


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--input_csv', '-i', type=str, required=True,
                        help='A CantusCorpus-format CSV file with chants that should be transformed'
                             ' into FASTA files.')
    parser.add_argument('--output_folder', '-o', type=str, required=True,
                        help='Path to the output folder where the FASTA files will be stored.'
                             ' If the folder does not exist, it will be created.'
                             ' If the folder is not empty, the script will stop. This can'
                             ' be overriden by using the --overwrite_output flag')
    parser.add_argument('--overwrite_output', action='store_true',
                        help='If set, will overwrite files within the output folder if they exists.'
                             ' Note that it will not delete the files that are already there with'
                             ' different Cantus ID numbers, so if you forget to change the output'
                             ' directory for a different dataset and set this flag, you will contaminate'
                             ' the output folder from the previous run.')

    parser.add_argument('--min_cids_per_source', type=int, default=1,
                        help='If set, will only include sources that have at least this many Cantus IDs.'
                             ' Default: 1.')
    parser.add_argument('--min_melody_length', type=int, default=1,
                        help='If set, discards melodies that are shorter than this.')

    parser.add_argument('--occurences_table', type=str, required=False,
                        help='Outputs a table of which sources contain which chants.'
                             ' This is useful to determine if certain Cantus IDs or'
                             ' certain sources should be discounted. Table rows are sigla,'
                             ' table columns are Cantus IDs. The table is output as a CSV,'
                             ' with the header row containing "siglum" and the CIDs, '
                             ' and the first column containing the sigla and the 0/1 values'
                             ' indicating whether the givel source contains a chant with the ID.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()

    with open(args.input_csv, 'r', newline='') as fh:
        chants_reader = csv.DictReader(fh)
        chants = [row for row in chants_reader]

    logging.info('Read {} chants from {}'.format(len(chants), args.input_csv))

    # Collect chants for each Cantus ID.
    chants_by_cantus_id = {}
    for chant in chants:
        cantus_id = chant['cantus_id']
        if cantus_id not in chants_by_cantus_id:
            chants_by_cantus_id[cantus_id] = []

        if len(clean_volpiano_for_divtime_christmas(chant['volpiano'])) < args.min_melody_length:
            logging.info('Discarding chant with Cantus ID {} from source {} because its melody is too short.'
                         ''.format(cantus_id, chant['siglum']))
            continue
        chants_by_cantus_id[cantus_id].append(chant)

    logging.info('Found {} unique Cantus IDs.'.format(len(chants_by_cantus_id)))
    logging.info('Chant counts per Cantus ID: {}'
                 ''.format({cid: len(chants) for cid, chants in chants_by_cantus_id.items()}))

    # Compute the occurence table.
    all_cids, all_sigla, occurences_table = compute_occurence_table(chants_by_cantus_id)

    # If the occurences table is requested, write it.
    if args.occurences_table:
        with open(args.occurences_table, 'w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['siglum'] + all_cids)
            for i, siglum in enumerate(all_sigla):
                writer.writerow([siglum] + occurences_table[i])

    # If the min_cids_per_source filter is set, filter out sources with too few chants.
    if args.min_cids_per_source > 1:
        # Collect chants per source. Use occurences table.
        n_cids_per_siglum = {siglum: sum(occurences_table[i]) for i, siglum in enumerate(all_sigla)}
        excluded_sigla = [siglum for siglum in all_sigla
                          if n_cids_per_siglum[siglum] < args.min_cids_per_source]
        logging.info('Excluded {} sigla because they had fewer than {} chants.'
                     ''.format(len(excluded_sigla), args.min_cids_per_source))
        logging.info('The excluded sigla: {}'.format(sorted(excluded_sigla)))

    # Create the FASTA string for each Cantus ID.
    volpiano_by_cantus_id_and_fasta_siglum = {cid: {} for cid in chants_by_cantus_id}
    for cid in chants_by_cantus_id:
        chants = chants_by_cantus_id[cid]
        for chant in chants:
            siglum = chant['siglum']
            fasta_siglum = siglum_to_fasta_header_name(siglum)

            volpiano = chant['volpiano']
            cleaned_volpiano = clean_volpiano_for_divtime_christmas(volpiano)

            current_cid_dict = volpiano_by_cantus_id_and_fasta_siglum[cid]

            # Note: we have to deal with multiple instances of the same chant in a source.
            # We retain the longest melody (because some might be shorter incipits).
            if fasta_siglum not in current_cid_dict:
                current_cid_dict[fasta_siglum] = cleaned_volpiano
            elif len(cleaned_volpiano) > len(current_cid_dict[fasta_siglum]):
                current_cid_dict[fasta_siglum] = cleaned_volpiano
            # else (a longer version of this chant from this source is already in the dict)

    # Create output folder if it does not exist.
    if not os.path.isdir(args.output_folder):
        os.makedirs(args.output_folder)

    # If the output folder is not empty, fail (unless overwrite_output is set).
    if os.listdir(args.output_folder):
        if not args.overwrite_output:
            logging.error('Output folder {} is not empty. Exiting.'
                          ''.format(args.output_folder))
            raise OSError('Output folder {} is not empty and overwrite flag is not set. Exiting.')
    # (If the overwrite flag *is* set, then it does not care about the previous contents
    # of the folder at all.)

    # For each CID, create its FASTA string, then create a FASTA file and write the string to it.
    # Note: no empty lines in the output files.
    for cid in volpiano_by_cantus_id_and_fasta_siglum:
        fasta_strings = []
        for fasta_siglum in sorted(volpiano_by_cantus_id_and_fasta_siglum[cid].keys()):
            volpiano = volpiano_by_cantus_id_and_fasta_siglum[cid][fasta_siglum]
            fasta_string = '>{0}\n{1}'.format(fasta_siglum, volpiano)
            fasta_strings.append(fasta_string)

        fasta_filename = os.path.join(args.output_folder, '{0}.fasta'.format(cid))
        with open(fasta_filename, 'w') as fh:
            fh.write('\n'.join(fasta_strings))

    _end_time = time.process_time() # Occurence
    logging.info('cantus_csv_to_divtime_christmas_fastas.py done in {0:.3f} s'.format(_end_time - _start_time))


if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
