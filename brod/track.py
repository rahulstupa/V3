from ball import Ball, BallRecord
import cv2
import math
import os.path as osp
import numpy as np
import threading
from threading import Thread, local
import time
import sys
import json
from shapely.geometry import Polygon, Point
import pandas as pd
from util import drawline, overlay_transparent, reconnect, getTransformation, emit_set_json, emit_match_json
from util_graphics import loadAfterPoint, loadAfterSet, loadAfterMatch
from stats import GameStats, MatchStats, PointStats
import imutils
import bbox_visualizer as bbv
import subprocess as sp
from PIL import Image
from imutils.video import FPS


class Tracker:

    def __init__(self, stream, score, point_started, point_over, set_over, match_over, cfg,
                 playerA, playerB, LiveScoreBase):
        self.score = score
        self.LiveScoreBase = LiveScoreBase
        self.point_started = point_started
        self.point_over = point_over
        self.set_over = set_over
        self.match_over = match_over
        self.stream = stream
        self.cfg = cfg
        self.playerA = playerA
        self.playerB = playerB
        self.thread = Thread(target=self.track, args=())
        self.sio = reconnect() 
        
    def start(self):
        self.thread.start()
        return self
    
    def get_ball_bbox(self, preds, frame):
        preds = preds.pandas().xyxy[0]
        # print(preds)
        ball_preds =  preds[preds['name'] == 'class0']  # Change class0 to ball for non-tensorrt model
        
        if len(ball_preds)>0:
            preds = np.array(ball_preds.to_records(index=False).tolist())
            # Choosing the most confident prediction
            idx = np.argsort(preds[:,4])[-1]
            ball_box = preds[idx, :4].astype(float).astype(int).tolist()
            return ball_box
        
        return []
    
    def get_ball(self, nd, roi, frame_number):
        xmin, ymin, xmax, ymax = roi
        # Check if ball lies in table range
        ball_poly = Polygon([(xmin,ymin),(xmax,ymin), (xmax,ymax), (xmin,ymax)])
        range = nd[roi[1]:roi[3], roi[0]:roi[2]]
        contours, _ = cv2.findContours(range, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
                                   offset=(roi[0],roi[1]))

        if len(contours)>0:
            # print("Contour Passed")
            temp = np.zeros((1080,1920,3),np.uint8)
            contours = np.vstack(contours)
            try:
                ellipse = cv2.fitEllipse(contours)
                cv2.ellipse(temp,ellipse,(0,255,0),2)
                temp = cv2.cvtColor(temp, cv2.COLOR_BGR2GRAY)
                range = temp[roi[1]:roi[3], roi[0]:roi[2]]
                contours, _ = cv2.findContours(range, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,
                                    offset=(roi[0],roi[1]))
                contours = contours[0]
            except:
                # print("Ellipse Fit failed")
                pass
            try:
                return Ball(contours,self.cfg,frame_number, in_range = self.cfg.table_poly.intersects(ball_poly))
            except Exception as e:
                # print(e)
                return None
        # print("Contour not Passed")
        return None
    
    def track(self):
        cap = self.stream.start()
        
        frame_number = 0
        ball_record = BallRecord(self.cfg, self.score, self.sio)
        game_stats = GameStats(self.playerA, self.playerB, ball_record, self.score)
        match_stats = MatchStats(self.playerA, self.playerB, ball_record, self.score)
        # 
        # fgbg1 = cv2.createBackgroundSubtractorKNN(detectShadows=False)
        fgbg1 = cv2.bgsegm.createBackgroundSubtractorMOG()
        # fgbg1 = cv2.createBackgroundSubtractorMOG2(detectShadows=False)

        # result = cv2.VideoWriter('filename.avi',
        #                  cv2.VideoWriter_fourcc(*'MJPG'),
        #                  self.cfg.fps, self.cfg.resolution)
        # fps = FPS().start()

        while cap.more():
        # while fps._numFrames < 2000:

            frame_number+=1
            predictions, frame_current, status = cap.read()
            final_image = frame_current.copy()
            start_time = time.time()

            ball = None
            nd_all = fgbg1.apply(imutils.resize(frame_current,width=960))
            # if self.point_started.is_set():
            if 'point_started' in status:
            # if True:
                # print("Tracking ......")
                roi = self.get_ball_bbox(predictions, frame_current)
                if roi:
                    print( "Ball Found")
                    
                    nd_all = imutils.resize(nd_all, width=1920)
                    # temp = np.copy(nd_all)
                    ball = self.get_ball(nd_all, roi, frame_number)
                    # ball=None
                    
                    if ball is not None:
                        frame_current[:] = bbv.draw_rectangle(frame_current, roi, (0,255,0))
                        bbv.add_label(frame_current, 'ball', roi, top=True)
                        ball_record.add_ball(ball, frame_current)
                    else:
                        # cv2.rectangle(frame_current,(roi[:2]),(roi[2:]),(0,0,255),2)
                        pass
                # Drawing Pitches
                if len(ball_record.pitches) > 0:
                    frame_current = overlay_transparent(background=frame_current, overlay=ball_record.pitches[-1].get_overlay(), x=ball_record.pitches[-1].coords[0] - 21,
                                                        y=ball_record.pitches[-1].coords[1] - 12)
                    # for i, pitch in enumerate(ball_record.pitches):
                    #     final_image = overlay_transparent(background=frame_current, overlay=pitch.get_overlay(), x=pitch.coords[0] - 21,
                                                        # y=pitch.coords[1] - 12, alpha=False)
        
                    # for i,line in enumerate(ball_record.lines):
                    #     line.draw(final_image)
                    pass
                else:
                    # pass
                    final_image = frame_current.copy()
                    
            else:            
                # if self.point_over.is_set():
                if 'reset' in status:
                    ball_record.record = []
                    ball_record.pitches = []
                    ball_record.lines = []
                if 'point_over' in status:
                    if len(ball_record.pitches)>0:
                        if len(ball_record.pitches)>=2:
                            if self.score['ServiceFrom']==ball_record.pitches[0].side:
                                ball_record.pitches.pop(0)

                        point_stats = PointStats(self.playerA, self.playerB, ball_record, self.score.copy())
                        stats_json = point_stats.get_stats()
                        self.emit_pt_json(stats_json)
                        # threading.Thread(target=loadAfterPoint, args=(stats_json,self.stream)).start()
                        print("Here are your Point stats.")
                        print(stats_json)

                        json_object = json.dumps(stats_json, indent=4)
                        # Writing to sample.json
                        with open("point_data.json", "w") as outfile:
                            outfile.write(json_object)

                        print("*************************  JSon ***************** ")
                            
                        ball_record.update_set_match_pitches()
                        game_stats.add_point(point_stats)
                        match_stats.add_point(point_stats)
                      
                    # if self.set_over.is_set():
                    if 'set_over' in status:
                        print("Here are your Game stats")
                        game_stats_json = game_stats.get_stats()
                        # threading.Thread(target=loadAfterSet, args=(self.playerA, self.playerB, game_stats_json,self.stream)).start()
                        print(game_stats_json)

                        json_object = json.dumps(game_stats_json, indent=4)
                        # Writing to sample.json
                        with open("game_data.json", "w") as outfile:
                            outfile.write(json_object)

                        ball_record.generate_set_heatmaps()
                        match_stats.update_set_analysis(game_stats_json)
                        threading.Thread(target=emit_set_json, args=(game_stats_json, self.sio, self.playerA, self.playerB)).start()
                        self.playerA.reset_analysis()
                        self.playerB.reset_analysis()
                        self.set_over.clear()
                                 
                    # if self.match_over.is_set():
                    if 'match_over' in status:
                        game_stats_json = game_stats.get_stats()
                        match_stats.update_set_analysis(game_stats_json)
                        print("Here are your Match stats")
                        match_stats_json = match_stats.get_stats()

                        json_object = json.dumps(match_stats_json, indent=4)
                        # Writing to sample.json
                        with open("match_data.json", "w") as outfile:
                            outfile.write(json_object)

                        # threading.Thread(target=loadAfterMatch, args=(self.playerA, self.playerB, match_stats_json,self.stream)).start()
                        print(match_stats_json)
                        ball_record.generate_match_heatmaps()
                        threading.Thread(target=emit_match_json, args=(match_stats_json, self.sio, self.playerA, self.playerB)).start()
                        self.match_over.clear()
            
            # self.p.stdin.write(final_image.tobytes())                                        
            # self.emit_track_json(frame_number, ball_record)
            # time_taken = time.time() - start_time
            # print("Time Taken ",round(time_taken*1000,2))
            # fps.update()

            # if time_taken < self.cfg.time_per_frame:
                # time.sleep(self.cfg.time_per_frame - time_taken)
            # print(self.stream.Q.qsize())
            # result.write(final_image)
            # frame_current = cv2.resize(frame_current, (1280, 720))
            # cv2.imshow('Frame', frame_current)
            # Press Q on keyboard to  exit
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     self.thread.join()
            #     cv2.destroyAllWindows()
            #     break
            
        # fps.stop()
        # print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        # print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    
    def emit_track_json(self, frame_number, ball_record):
        if len(ball_record.record)>1:
            ball = ball_record.record[-2]
            data = {}
            data["Frame Number"] = frame_number
            data["X"] = ball.cX if ball is not None else 0
            data["Y"] = ball.cY if ball is not None else 0
            data["speed"] = ball.speed
            data["pitch"] = ball.pitching
            data["pitch_X"] = ball.pX
            data["pitch_Y"] = ball.pY
            data["pointend"] = self.point_over.is_set()
            data["player_A_name"] = self.playerA.name
            data["player_B_name"] = self.playerB.name
            data["player_A_score"] = self.playerA.score
            data["player_B_score"] = self.playerB.score
            data["player_A_setscore"] = self.playerA.set_score
            data["player_B_setscore"] = self.playerB.set_score
            data["MatchId"] = self.score["MatchId"]
            
            self.sio.emit('tracking', data)
    
    def emit_pt_json(self, pt_stats):
        data = {}
        data['LastShotSpeed'] = int(pt_stats['LastShotSpeed'])
        data['AvgSpeed'] = pt_stats['AvgSpeed']
        data['WinnerPlacement'] = ""
        data["RallyCount"] = pt_stats["RallyCount"]
        
        self.sio.emit('point', data)
