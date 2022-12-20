import socketio
import cv2
from threading import Thread
import time
from util_graphics import load_scoreboard

class Scorer():

    def __init__(self, score, point_started, point_over, set_over, match_over, reset, playerA, playerB, stream):
        self.score = score
        self.point_started = point_started
        self.point_over = point_over
        self.set_over = set_over
        self.match_over = match_over
        self.reset = reset
        self.playerA = playerA
        self.playerB = playerB
        self.thread = Thread(target=self.get_score, args=())
        self.point_time = 0
        self.set_time = 0
        self.match_time = 0
        self.stream = stream
        # self.stream.scoreboard = load_scoreboard(playerA, playerB)
    
    def start(self):
        self.thread.start()
        return self
    
    def get_score(self):
        sio = socketio.Client()

        @sio.event
        def connect():
            print('connected')

        @sio.event
        def score( data):
        
            if data is None:
                print('Received Null')
                            
            elif self.score['MatchId'] == str(data['MatchId']):
                
                if bool(data['SwitchSides']):
                    if int(data['GameNumber'])>1 and data['GameScoreA']==0 and data['GameScoreB']==0:
                        if data['PlayerSide'].lower() == 'left':
                            data['PlayerSide'] = 'right'
                        else:
                            data['PlayerSide'] = 'left'
                    
                data['MatchId'] = str(data['MatchId'])
                
                self.playerA.update_metadata(data["PlayerAId"], data["PlayerAName"],
                                    data['PlayerSide'].lower(),data["PlayerAHandType"])
                self.playerB.update_metadata(data["PlayerBId"], data["PlayerBName"],'right' if data['PlayerSide'].lower() == 'left' else 'left',
                                    data["PlayerBHandType"])
                
                if data["ServiceBy"] == self.playerA.id_:
                    self.playerA.serving = True
                    self.playerB.serving = False
                    data["ServiceFrom"] = self.playerA.side
                else:
                    self.playerB.serving = True
                    self.playerA.serving = False
                    data["ServiceFrom"] = self.playerB.side
                    
                self.score.update(data)
                if data['StartPlaying']:
                    self.point_time = time.time()
                    if self.playerA.score+self.playerB.score==0:
                        self.set_time = time.time()
                        if self.score["GameNumber"]==1:
                            self.match_time = time.time()
                            
                    self.point_started.set()
                    self.point_over.clear()
                    self.set_over.clear()
                
                elif not data['StartPlaying']:
                    if str(data['Status']).lower() == 'score':
                        # Finding PointWinner on giving point
                        if not self.playerA.score==data['GameScoreA']:
                            self.score["PointWinner"] = self.playerA.id_
                        elif not self.playerB.score==data['GameScoreB']:
                            self.score["PointWinner"] = self.playerB.id_
                        self.playerA.score = data["GameScoreA"]
                        self.playerB.score = data["GameScoreB"]
                        self.score["PointTime"] = round(time.time()-self.point_time,2)
                        self.point_over.set()
                        
                        if data['FinalPoint']:
                            if not self.playerA.set_score==data['SetScoreA']:
                                self.score["GameWinner"] = self.playerA.id_
                            elif not self.playerB.set_score==data['SetScoreB']:
                                self.score["GameWinner"] = self.playerB.id_  
                            self.playerA.set_score = data["SetScoreA"]
                            self.playerB.set_score = data["SetScoreB"]
                            self.score["SetTime"] = round(time.time() - self.set_time,2)
                            if data['FinalSet']:
                                self.score["MatchTime"] = round(time.time() - self.match_time,2)
                                self.match_over.set()
                                # self.set_over.set()
                            else:
                                self.set_over.set()
                    elif str(data['Status']).lower() == 'reset':
                        self.reset.set()
                    else:
                        self.playerA.score = data["GameScoreA"]
                        self.playerB.score = data["GameScoreB"]
                        self.playerA.set_score = data["SetScoreA"]
                        self.playerB.set_score = data["SetScoreB"]
                        
                    self.point_started.clear()
            # self.stream.scoreboard[:] = load_scoreboard(self.playerA, self.playerB)

                # print(self.score)
                # print(self.playerA.__dict__)
                # print(self.playerB.__dict__)
                # print("...........................................")
                
        sio.connect('http://stupa-event-api.stupaanalytics.com:5100')
        sio.wait()

