#!/usr/local/bin/python3
import os

import argparse

from google.cloud import datastore


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth-file.json"


def list_entities(client, entity):
    query = client.query(kind=entity)
    return list(query.fetch())


def choose_election(client, elections):
    print("Which Election do you want to Run?")
    print("==================================")
    d = {}
    for i, e in enumerate(elections):
        print("{}: {}".format(i + 1, e["Position"]))
        d[i] = e

    election_index = int(input("> ")) - 1
    return d[election_index]


def retrive_candidates(client, election):
    candidates = client.get_multi(election["Candidates_Keys"])

    print("Do you need to remove any candidates? (y/n)")
    ans = str(input("> "))
    if ans.lower() in ["n", "no"]:
        return candidates

    print("Which Candidates do you want to remove?")
    print("=======================================")
    d = {}
    for i, c in enumerate(candidates):
        print("{}: {}".format(i + 1, c["Name"]))
        d[i] = c

    candidate_indexs = input("> ").split(" ")
    try:
        candidate_indexs = [int(i) - 1 for i in candidate_indexs]
    except ValueError:
        return candidates

    for i in candidate_indexs[::-1]:
        client.delete(d[i].key)
        election["Candidates_Keys"].remove(d[i].key)
        candidates.pop(i)

    client.put(election)
    return candidates


def count_votes(client, election):
    query = client.query(kind="Vote")
    query.add_filter("Election_Key", "=", election["Key"])
    votes = list(query.fetch())
    d = dict()

    for vote in votes:
        candidate = vote['Candidate_Key']
        candidate_votes = d.get(candidate, [])
        candidate_votes.append(vote)
        d[candidate] = candidate_votes

    with open("logs/{}.txt".format(election["Key"]), "w") as f:
        for key, votes in d.items():
            f.write(os.linesep)
            f.write(key + os.linesep)
            f.write(len(key)*'-' + os.linesep)
            for v in votes:
                f.write(v['Voter_ID'] + ": " + v['Candidate_Key'] + os.linesep)

            print(f"{key}: {len(votes)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser.add_argument('--project-id', help='Your cloud project ID.')
    args = parser.parse_args()
    client = datastore.Client(args.project_id)

    elections = list_entities(client, "Election")

    while True:
        election = choose_election(client, elections)
        candidates = retrive_candidates(client, election)

        election["Active"] = True
        client.put(election)
        print("Election now open!")
        print("==================")
        for c in candidates:
            print(c["Name"])
        print("==================")
        print("")
        print("")

        input("Press enter to end election")
        print("===========================")
        election["Active"] = False
        client.put(election)

        count_votes(client, election)
