#!/usr/bin/env python
"""This is a script that extracts the Christmas expansion set
from the Cantus Index dump and outputs it as the CantusCorpus-style
CSV, so that it can then be used for annotation."""

import argparse
import logging
import time

import csv
import pprint

__version__ = "0.0.1"
__author__ = "Jan Hajic jr."


CHRISTMAS_CANTUS_IDS = ['003511', '007040', '007040a', '001737', '004195', '002000']
CHRISTMAS_EXPANSION_CANTUS_SOURCES = [] # TODO

def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--cantus_offices_csv', '-i', type=str, required=True,
                        help='Path to the CSV file with the Cantus Index dump.')
    parser.add_argument('--output_csv', '-o', type=str, required=True,
                        help='Path to the output CSV file in CantusCorpus format.')
    parser.add_argument('--relevant_cids', nargs='+', type=str,
                        default=CHRISTMAS_CANTUS_IDS,
                        help='Cantus IDs of the chants that should be included in the output CSV.')
    # parser.add_argument('--relevant_sources', nargs='+', type=str,
    #                     default=CHRISTMAS_EXPANSION_CANTUS_SOURCES,
    #                     help='Source IDs of the chants that should be included in the output CSV.'
    #                          ' Result of manual filtering of what is available via Cantus Index.')
    parser.add_argument('--christmas_sources_table', type=str, required=True,
                        help='Path to the table with manually selected sources.')

    parser.add_argument('--sources_delimiter', type=str, default=',',
                        help='Delimiter for the sources table. I had something exported'
                             ' with a semicolon instead of a comma, which is why this'
                             ' parameter exists.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()

    # Load Christmas sources table
    with open(args.christmas_sources_table, 'r', newline='') as fh:
        sources_reader = csv.DictReader(fh, delimiter=args.sources_delimiter)
        # For whatever reason, numbers exported the table with semicolon.
        sources = [row for row in sources_reader]

    logging.info('Loaded {} sources from {}'.format(len(sources), args.christmas_sources_table))
    logging.debug('First source:\n{}'.format(sources[0]))

    # Prepare the list of relevant source IDs
    relevant_source_ids = [source['source'] for source in sources]

    logging.info('Found {} relevant source IDs.'.format(len(relevant_source_ids)))
    logging.debug('Relevant source IDS: {}'.format(relevant_source_ids))

    # Load CantusIndex office chants dump
    with open(args.cantus_offices_csv, 'r', newline='') as fh:
        chants_reader = csv.DictReader(fh)
        chants = [row for row in chants_reader]
        # Remember the column labels
        chant_column_labels = chants_reader.fieldnames

    logging.info('Loaded {} chants from {}'.format(len(chants), args.cantus_offices_csv))
    logging.info('First chant:\n{}'.format(chants[0]))

    # Filter for sources in the selection.
    # For each source, filter for chants in the list of relevant CIDs
    relevant_chants_per_source = {s: {cid: None for cid in args.relevant_cids}
                                  for s in relevant_source_ids}
    for chant in chants:
        if chant['source_id'] in relevant_source_ids and chant['cantus_id'] in args.relevant_cids:
            relevant_chants_per_source[chant['source_id']][chant['cantus_id']] = chant

    logging.info('Relevant chants found: {}'
                 ''.format(sum(len(chants) for chants in relevant_chants_per_source.values())))
    logging.debug(pprint.pformat(relevant_chants_per_source))

    # Output the resulting CSV
    with open(args.output_csv, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=chant_column_labels)
        writer.writeheader()
        for source_id, chants in relevant_chants_per_source.items():
            for chant in chants.values():
                if chant is not None:
                    writer.writerow(chant)

    _end_time = time.process_time()
    logging.info('scrape_cantus_db_sources.py done in {0:.3f} s'.format(_end_time - _start_time))


if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
