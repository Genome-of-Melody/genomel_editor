#!/usr/bin/env python
"""This is a script that computes the statistics of the Genome of Melody
dataset. It expects the JSON dump of the complete genomel_editor database."""

import argparse
import logging
import time

import json

__version__ = "0.0.1"
__author__ = "Jan Hajic jr."


# Users that are not really annotators: various test (mostly me) and admin accounts.
IRRELEVANT_USER_IDS = [1, 2, 3, 5]


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
    parser.add_argument('--no_check_adiastematic', action='store_true',
                        help='If set, will not discard adiastematic melodies.')
    parser.add_argument('--no_check_incomplete_in_source', action='store_true',
                        help='If set, will not discard melodies marked as incomplete in source.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()

    # Load JSON with editor database dump.
    with open(args.input_json, 'r') as fh:
        editor_dump = json.load(fh)

    # Load and filter melodies.
    melodies = [record for record in editor_dump
                if record['model'] == 'GenomelEditor.melody']
    complete_melodies = [melody for melody in melodies
                         if is_complete_melody(melody,
                                               check_adiastematic=not args.no_check_adiastematic,
                                               check_incomplete_in_source=not args.no_check_incomplete_in_source)]

    n_melodies, n_complete_melodies = len(melodies), len(complete_melodies)
    print('Found {0} melodies, {1} of which are complete ({2:.1f} %).'
          ''.format(n_melodies, n_complete_melodies,
                    100 * n_complete_melodies / n_melodies))


    # Compute how many melodies were done by each user (both overall and complete melodies).
    user_melody_counts = {}
    users = [record for record in editor_dump if record['model'] == 'auth.user']
    user_id_to_name = {user['pk']: user['fields']['username'] for user in users}

    for melody in melodies:
        user_id = melody['fields']['user_transcriber']
        if user_id not in user_melody_counts:
            user_melody_counts[user_id] = 0
        user_melody_counts[user_id] += 1

    user_complete_melody_counts = {}
    for melody in complete_melodies:
        user_id = melody['fields']['user_transcriber']
        if user_id not in user_complete_melody_counts:
            user_complete_melody_counts[user_id] = 0
        user_complete_melody_counts[user_id] += 1

    # Print the user stats.
    logging.info('User stats:')
    for user_id, count in user_melody_counts.items():
        if user_id in IRRELEVANT_USER_IDS:
            continue
        user_name = user_id_to_name[user_id]
        complete_count = user_complete_melody_counts.get(user_id, 0)
        completeness_ratio = complete_count / count if count > 0 else 0
        print('User {0} ({1}): {2} melodies, {3} complete ({4:.2f}).'
              ''.format(user_id, user_name, count, complete_count, completeness_ratio))

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
