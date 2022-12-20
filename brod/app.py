import argparse
import os
import numpy as np
import json
from model_class import Player, Config
from util import get_matchid, get_match_details
import threading
from scoring_thread import Scorer
from instream import Stream
from track import Tracker

parser = argparse.ArgumentParser()
parser.add_argument('--src', required=True)
parser.add_argument('--setup', action='store_true')


if __name__ == '__main__':
    args = parser.parse_args()
    if args.setup and args.src:
        os.system("python setup.py --src " + (args.src))
    if args.src.isnumeric():
        src = int(args.src)
    else:
        src = args.src
    # match_id = get_matchid()
    match_id = '42185316'
    
    MatchData = get_match_details(match_id)

    playerA = Player(MatchData['playerAId'],MatchData['playerAName'],MatchData['playerSide'].lower(),
                        MatchData['playerAHandType'])
    # playerA = Player('','','','')
   
    playerB = Player(MatchData['playerBId'],MatchData['playerBName'],
                        'right' if playerA.side == 'left' else 'left',MatchData['playerBHandType'])
    # playerB = Player('','','','')
   
    RESOLUTION = [1920, 1080]
    
    with open('coordinates.json') as f:
        coordinates = json.load(f)
        ORDEREDEDGES = coordinates['coordinates']
    
    point_started = threading.Event()
    point_over = threading.Event()
    set_over = threading.Event()
    match_over = threading.Event()
    reset = threading.Event()

    with open("score.json", "r") as f:
        LiveScoreBase = json.loads(f.read())
    
    # SQS score object is continously live updated by scoring thread
    SQSscore = LiveScoreBase.copy()
    SQSscore['MatchId'] = match_id
    
    stream = Stream(src, point_started, point_over, set_over, match_over, reset)
    scorer = Scorer(SQSscore, point_started, point_over, set_over, match_over, reset, playerA, playerB, stream)
    scorer.start()
    cfg = Config(ORDEREDEDGES, stream.fps, RESOLUTION)
    
    tracker = Tracker(stream, SQSscore, point_started, point_over, set_over, match_over, cfg,
                      playerA, playerB, LiveScoreBase)
    tracker.start()
    # outstream.run(host='0.0.0.0')
    