import math
from util import line_intersection, get_line_corners
import cv2
from util import point_distance
from shapely.geometry import Polygon, Point
import numpy as np
from util import overlay_transparent, GetZonePercentages
import pandas as pd
import glob


class Ball():
    def __init__(self, contour, cfg, frame_number, in_range):
        # contour = cv2.convexHull(contour)
        M = cv2.moments(contour)

        if M["m00"] > 0:
            self.cX = int(M["m10"] / M["m00"])
            self.cY = int(M["m01"] / M["m00"])
        else:
            self.cX = self.cY = 0
        contour_points = contour.reshape(contour.shape[0], contour.shape[2])
        [vX, vY, x, y] = cv2.fitLine(contour_points, cv2.DIST_L2, 0, 0.01, 0.01)
        self.vX, self.vY = round(vX[0],2), round(vY[0],2)
        self.x, self.y = x[0], y[0]
        self.dist_from_center = point_distance(self.cX, cfg.table_center[0] ,self.cY, cfg.table_center[1])
        self.cfg = cfg
        if self.cX < cfg.table_center[0]:
            self.side = 'left'
        else:
            self.side = 'right'
        self.frame_number = frame_number
        self.speed = 0
        self.direction = "unknown"
        self.pX, self.pY = 0,0
        self.pitching = False
        self.in_range = in_range
    
    def update_speed(self, prev_ball):
        frame_diff = self.frame_number - prev_ball.frame_number
        distance = math.hypot(abs(self.cX - prev_ball.cX),abs(self.cY - prev_ball.cY)) / self.cfg.PIXEL_TO_CMS
        if self.cfg.resolution[0] == 720:
            speed = round(
                18.34 + 0.77 * (abs((distance / 100) / self.cfg.time_per_frame) * self.cfg.SPEED_CONVERSION_FACTOR), 0)
        else:
            speed = round(
                35.3 + 0.33 * (abs((distance / 100) / self.cfg.time_per_frame) * self.cfg.SPEED_CONVERSION_FACTOR), 0)

        speed = round(speed / int(frame_diff), 0)
        self.speed = speed

    def update_direction(self, prev_ball):
        if self.cX > prev_ball.cX:
            self.direction = 'right'
        else:
            self.direction = 'left'


class BallRecord():
    def __init__(self, cfg, score, sio):
        self.cfg = cfg
        self.score = score
        self.record = []
        # Point Data
        self.pitches = []
        self.lines = []
        #  Set Data
        self.set_pitches = []
        self.set_service_pitches = []
        self.set_third_pitches = []
        self.set_winning_pitches = []
        # Match Data
        self.match_pitches = []
        self.match_service_pitches = []
        self.match_third_pitches = []
        self.match_winning_pitches = []
        
        self.last_pitch_frame = 0
        self.sio = sio
        
    def add_ball(self, ball, frame):
        if len(self.record)==0:
            self.record.append(ball)
        else:
            ball.update_speed(self.record[-1])
            ball.update_direction(self.record[-1])
            self.record.append(ball)
            
            if len(self.record)>3:
                found = self.find_pitch(frame)
                if found:
                    self.sio.emit('tracking', {"pitch":self.pitches[-1].coords, "side":self.pitches[-1].side})
        
        # print(ball.__dict__)
    
    def find_pitch(self, frame):
        ball1 = self.record[-3]
        ball2 = self.record[-2]
        ball3 = self.record[-1]
        pitch_frame_diff = 0
        pX, pY = 0,0
        if (ball1.side == ball2.side == ball3.side) and (ball1.in_range or ball2.in_range or ball3.in_range):
            if ball1.direction == ball2.direction == ball3.direction:
                if (ball3.direction=="left" and (ball3.vY-ball1.vY)>0.075) or (ball3.direction=="right" and (ball3.vY-ball1.vY)<-0.075):
                    # print("...............................................................")
                    # print("Angle Check Satisifed", ball3.vY, ball2.vY, ball1.vY)
                    # if (ball3.direction=="left" and ball2.vY<ball1.vY and ball2.vY*ball1.vY>0) or (ball3.direction=="right" and ball2.vY>ball1.vY and ball2.vY*ball1.vY>0):
                    #     print("Ball Still Descending")
                    #     return
                    # nextMaxY = ball1
                    selected_ball = 'ball1'
                    # if ball1.cY <= ball2.cY > ball3.cY:
                    #     print("Old Method used")
                    #     if ball1.cY>ball3.cY:
                    #         nextMaxY = ball1
                    #         selected_ball = 'ball1'
                    #     elif ball1.cY<ball3.cY:
                    #         nextMaxY = ball3
                    #         selected_ball = 'ball3'
                    pX,pY = self.get_pitch_coordinates(ball2, ball3, frame)
                        
                    #     if pX==0:
                    #         if selected_ball=='ball1':
                    #             nextMaxY = ball3
                    #             pX,pY = self.get_pitch_coordinates(ball2, nextMaxY, frame)
                    #         else:
                    #             nextMaxY = ball1
                    # pX,pY = self.get_pitch_coordinates(ball2, ball3, frame)
                    # else:
                    # print("New Method used")
                    if pX==0:
                        pX,pY = self.get_pitch_coordinates(ball1, ball3, frame)
                else:
                    pX,pY = 0,0
            else:
                pX,pY = 0,0
            if pX!=0:
                # print("Pitch Found ", selected_ball)
                dist = math.sqrt((pX - ball2.cX) ** 2 + (pY - ball2.cY) ** 2)
                # print("Pitch Ball Distance ", dist)
                # if int(dist)>100:
                #     pX,pY = ball2.cX, ball2.cY
                
                if self.cfg.table_poly.contains(Point(pX,pY)):
                    ball2.pX = pX
                    ball2.pY = pY
                    if len(self.pitches)>0:
                        pitch_frame_diff = self.cfg.fps//5 if ball2.side!=self.pitches[-1].side else 3*self.cfg.fps//5 
                    if ball2.frame_number-self.last_pitch_frame>pitch_frame_diff:
                        print("Pitch Added")
                        self.pitches.append(Pitch(int(pX), int(pY), ball2.speed, ball2.side,))
                        ball2.pitching=True
                        self.last_pitch_frame = ball2.frame_number
                        return True
                    else:
                        print("asdsdfsfssfsdfsf")
                        if len(self.pitches)>1 and self.pitches[-2].side!=self.pitches[-1].side:
                            self.lines.append(Line(self.pitches[-2].coords, self.pitches[-1].coords))
        return False
                
    
    def get_pitch_coordinates(self, ball2, nextMaxY, frame):
        pX,pY = 0,0

        if ball2.vX!=0 and ball2.vY!=0 and nextMaxY.vX!=0 and nextMaxY.vY!=0:
            current_left_pt, current_right_pt = get_line_corners(ball2, self.cfg.resolution[0])
            next_left_pt, next_right_pt = get_line_corners(nextMaxY, self.cfg.resolution[0])
            pX, pY = line_intersection(
                [[self.cfg.resolution[0] - 1, current_right_pt], [0, current_left_pt]],
                [[self.cfg.resolution[0] - 1, next_right_pt], [0, next_left_pt]])
            # if pX>0:
            #     cv2.line(frame,[self.cfg.resolution[0] - 1, current_right_pt], [0, current_left_pt], (0,0,255), 1)
            #     cv2.line(frame,[self.cfg.resolution[0] - 1, next_right_pt], [0, next_left_pt], (0,0,255), 1)
        # elif nextMaxY.vY==0 or ball2.vY==0:
        #     pX,pY = ball2.cX,ball2.cY
        return pX,pY
                    
    def update_set_match_pitches(self):
        self.set_service_pitches.append(self.pitches[0])
        if len(self.pitches) >= 3:
            self.set_third_pitches.append(self.pitches[2])
        self.set_winning_pitches.append(self.pitches[-1])
        self.set_pitches.extend(self.pitches)
        self.match_service_pitches.extend(self.set_service_pitches)
        self.match_winning_pitches.extend(self.set_winning_pitches)
        self.match_third_pitches.extend(self.set_third_pitches)
        self.match_pitches.extend(self.set_pitches)
        
        self.record = []
        self.pitches = []
        self.lines = []
    
    def generate_heatmaps(self, pitches, serve_pitches, winning_pitches, third_pitches, type="set"):
        h, w = 1080, 1920
        n = 3
        trans = np.zeros((h, w, n), dtype=np.uint8)
        watermark = cv2.imread('graphics/ball.png', cv2.IMREAD_UNCHANGED)
        service_ball = cv2.imread('graphics/yellow_ball.png', cv2.IMREAD_UNCHANGED)
        third_ball = cv2.imread('graphics/orange_ball.png', cv2.IMREAD_UNCHANGED)
        last_ball = cv2.imread('graphics/green_ball.png', cv2.IMREAD_UNCHANGED)
        
        heatmap = trans.copy()
        placement_heatmap = trans.copy()
        service_heatmap = trans.copy()
        third_heatmap = trans.copy()
        winning_heatmap = trans.copy()
        for s_pitch in pitches:
            heatmap = overlay_transparent(background=heatmap, overlay=watermark, x=s_pitch.coords[0], y=s_pitch.coords[1])

        *_, alpha = cv2.split(heatmap)
        gray_layer = cv2.cvtColor(heatmap, cv2.COLOR_BGR2GRAY)
        dst = cv2.merge((gray_layer, gray_layer, gray_layer, alpha))
        cv2.imwrite(f'../nodecg/bundles/graphics/graphics/{type}_heatmap.png', dst)
        
        placement_heatmap = GetZonePercentages(placement_heatmap, self.cfg.orderedEdges,
                                               pitches, self.cfg.table_center,
                                               self.score['PlayerAHandType'],
                                               self.score['PlayerBHandType'])
        tmp = cv2.cvtColor(placement_heatmap, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(tmp, 0, 255, cv2.THRESH_BINARY)
        b, g, r = cv2.split(placement_heatmap)
        rgba = [b, g, r, alpha]
        dst = cv2.merge(rgba, 4)
        cv2.imwrite(f'../nodecg/bundles/graphics/graphics/{type}_placement_heatmap.png', dst)
        
        for s_service_pitch in serve_pitches:
            service_heatmap = overlay_transparent(background=service_heatmap, overlay=service_ball, x=s_service_pitch.coords[0], y=s_service_pitch.coords[1])
        b, g, r = cv2.split(service_heatmap)
        *_, alpha = cv2.split(service_heatmap)
        rgba = [b, g, r, alpha]
        dst = cv2.merge(rgba, 4)
        cv2.imwrite(f'../nodecg/bundles/graphics/graphics/{type}_service_heatmap.png', dst)
        
        for s_third_pitch in third_pitches:
            third_heatmap = overlay_transparent(background=third_heatmap, overlay=third_ball, x=s_third_pitch.coords[0], y=s_third_pitch.coords[1])
        b, g, r = cv2.split(third_heatmap)
        *_, alpha = cv2.split(third_heatmap)
        rgba = [b, g, r, alpha]
        dst = cv2.merge(rgba, 4)
        cv2.imwrite(f'../nodecg/bundles/graphics/graphics/{type}_third_heatmap.png', dst)
        
        for s_winning_pitch in winning_pitches:
            winning_heatmap = overlay_transparent(background=winning_heatmap, overlay=last_ball, x=s_winning_pitch.coords[0], y=s_winning_pitch.coords[1])
        b, g, r = cv2.split(winning_heatmap)
        *_, alpha = cv2.split(winning_heatmap)
        rgba = [b, g, r, alpha]
        dst = cv2.merge(rgba, 4)
        cv2.imwrite(f'../nodecg/bundles/graphics/graphics/{type}_winning_heatmap.png', dst)

    def generate_set_heatmaps(self):
        self.generate_heatmaps(self.set_pitches, self.set_service_pitches, self.set_winning_pitches,
                                self.set_third_pitches, type="set")
        self.set_pitches = []
        self.set_service_pitches = []
        self.set_third_pitches = []
        self.set_winning_pitches = []

    def generate_match_heatmaps(self):
        self.generate_heatmaps(self.match_pitches, self.match_service_pitches, self.match_winning_pitches,
                                self.match_third_pitches, type="match")
            
class Pitch:
    def __init__(self, pX, pY, speed, side):
        self.coords = (pX,pY)
        self.speed = speed
        self.side = side
        overlays = glob.glob("./graphics/pitchframewhite/*.png")
        overlays.sort()
        # print(overlays)
        self.overlays = [cv2.imread(im, cv2.IMREAD_UNCHANGED) for im in overlays]
        
    def get_overlay(self):
        if len(self.overlays)>2:
            return self.overlays.pop(0)
        else:
            return self.overlays[0]

class Line:
    def __init__(self,pt1, pt2):
        dist = ((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2) ** .5
        self.pts = []
        # print('inside_function_drawline')
        gap=25
        for i in np.arange(0, dist, gap):
            r = i / dist
            x = int((pt1[0] * (1 - r) + pt2[0] * r) + .5)
            y = int((pt1[1] * (1 - r) + pt2[1] * r) + .5)
            p = (x, y)
            self.pts.append(p)
        self.counter = 0
        self.pts.pop(0)
        # self.pts.pop(1)
        self.pts.pop(-1)
        # self.pts.pop(-2)
        
    def draw(self, img):
        color = (255, 255, 255)
        thickness = 2
        if self.counter!=len(self.pts):
            for p in self.pts[:self.counter]:
                cv2.circle(img, p, thickness, color, -1)
            self.counter+=1
        else:
            for p in self.pts:
                cv2.circle(img, p, thickness, color, -1)