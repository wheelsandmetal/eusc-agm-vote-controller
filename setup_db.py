#!/usr/local/bin/python3
import os

import argparse

from google.cloud import datastore


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth-file.json"


def create_client(project_id):
    return datastore.Client(project_id)


def add_candidate(client, path, candidate_key):
    key = client.key('Candidate')

    path = f'{path}/{candidate_key}'
    (_, dirs, files) = next(os.walk(path))

    with open(f'{path}/name.txt', 'r') as f:
        candidate_name = f.read()

    try:
        with open(f'{path}/message.txt', 'r', newline='') as f:
            candidate_message = f.read()
    except:
        candidate_message = "flip flop"

    candidate = datastore.Entity(key)
    candidate.update({
        'Key': candidate_key,
        'Name': candidate_name,
        'Message': candidate_message,
    })
    client.put(candidate)
    return candidate.key


def add_election(client, path, position_key):
    key = client.key('Election')

    path = f'{path}/{position_key}'
    (_, dirs, files) = next(os.walk(path))

    with open(f'{path}/{files[0]}', "r") as f:
        text = f.read()

    text = text.split('\n')
    position = text[0]
    order = text[1]

    candidates_keys = []
    for candidate in dirs:
        candidates_keys.append(add_candidate(client, path, candidate))

    election = datastore.Entity(key)
    election.update({
        'Position': position,
        'Key': position_key,
        'Candidates_Keys': candidates_keys,
        'Active': False,
        'Order': int(order),
    })

    client.put(election)
    return election


def add_elections(client, path):
    (_, position_keys, _) = next(os.walk(path))
    for position_key in position_keys:
        add_election(client, path, position_key)


def list_keys(client, entity):
    query = client.query(kind=entity)
    query.keys_only()
    return query.fetch()


def add_voter(client, voter_id):
    key = client.key("Voter")

    voter = datastore.Entity(key)
    voter.update({
        'Voter_ID': voter_id,
    })

    client.put(voter)
    return voter


def add_voters(client, path):
    with open(f'{path}', 'r') as f:
        voter_id = f.readline().split('\n')[0]
        while voter_id:
            add_voter(client, voter_id)
            voter_id = f.readline().split('\n')[0]


def clean_datastore(client):
    elections = list_keys(client, 'Election')
    for i in elections:
        client.delete(i.key)

    candidates = list_keys(client, 'Candidate')
    for i in candidates:
        client.delete(i.key)

    voters = list_keys(client, 'Voter')
    for i in voters:
        client.delete(i.key)

    voter = list_keys(client, 'Vote')
    for i in voter:
        client.delete(i.key)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser.add_argument('--project-id', help='Your cloud project ID.')
    args = parser.parse_args()
    client = create_client(args.project_id)

    clean_datastore(client)

    add_elections(client, "elections/")
    add_voters(client, "voters.txt")
