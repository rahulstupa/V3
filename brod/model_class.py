import math
from util import line_intersection, getLine
import cv2
from shapely.geometry import Polygon, Point
import numpy as np

class Player:
    def __init__(self, id_, name, side, handedness):
        self.id_ = id_
        self.name = name
        self.side = side
        self.handedness = handedness
        self.serving = False
        self.score = 0
        self.set_score = 0
        self.reset_analysis()

    def reset_analysis(self):
        self.analysis = {}
        self.analysis["TotalService"] = 0
        self.analysis["TotalReceive"] = 0
        self.analysis["PtWonOnService"] = 0
        self.analysis["PtWonOnReceive"] = 0
        self.analysis["ForehandWin"] = 0
        self.analysis["BackHandWin"] = 0
        self.analysis["AvgServeSpeedSum"] = 0
        self.analysis["AvgServeSpeed"] = 0

    def update_metadata(self, id_, name, side, handedness):
        self.id_ = id_
        self.name = name
        self.side = side
        self.handedness = handedness



class Config():
    def __init__(self, orderedEdges, fps, resolution):
        self.resolution = resolution
        self.SPEED_CONVERSION_FACTOR = 3.6
        self.LARGE_CONTOUR_THRESHOLD_FACTOR = 9
        self.table_length = math.hypot(orderedEdges[2][0] - orderedEdges[3][0],
                                       orderedEdges[2][1] - orderedEdges[3][1])
        self.PIXEL_TO_CMS = self.table_length / 274.32  # Table length in centimeters is 9 feet = 274.32 cms
        self.orderedEdges = orderedEdges
        edgedict = orderedEdges
        self.table_center = line_intersection(((orderedEdges[0]), orderedEdges[2]), (orderedEdges[1], orderedEdges[3]))
        self.fps = fps
        self.time_per_frame = 1 / (self.fps)  # seconds
        self.table_x_min = int(min(edgedict[0][0], edgedict[1][0], edgedict[2][0], edgedict[3][0]))
        self.table_x_max = int(max(edgedict[0][0], edgedict[1][0], edgedict[2][0], edgedict[3][0]))
        self.table_y_min = int(min(edgedict[0][1], edgedict[1][1], edgedict[2][1], edgedict[3][1]))
        self.table_y_max = int(max(edgedict[0][1], edgedict[1][1], edgedict[2][1], edgedict[3][1]))

        self.ballsize_px = self.PIXEL_TO_CMS * 3.7  # DIAMETER OF TT BALL IS 4 CMS (40 millimeters) (Ball pixels at the edge will diterioriate so taking 3.7
        minimum_contour_area = math.pi * (self.ballsize_px / 2) ** 2
        self.large_contour_threshold = self.LARGE_CONTOUR_THRESHOLD_FACTOR * minimum_contour_area
        self.min_contour_perimeter = math.pi * self.ballsize_px

        self.contour_area_range = range(int(minimum_contour_area), int(self.large_contour_threshold))
        print('Min Ball Area', int(minimum_contour_area), 'Max Ball Area', self.large_contour_threshold)
        Leftlin = getLine(orderedEdges[0][0], orderedEdges[0][1], orderedEdges[3][0],
                          orderedEdges[3][1])  # 370, 346, 282, 397)
        self.Leftlin = [[int(x[0]), int(x[1])] for x in Leftlin]
        Rightlin = getLine(orderedEdges[1][0], orderedEdges[1][1], orderedEdges[2][0], orderedEdges[2][1])
        self.Rightlin = [[int(x[0]), int(x[1])] for x in Rightlin]
        self.detection_range = Polygon([(self.table_x_min, self.table_y_max), (self.table_x_min, 0),
                                  (self.table_x_max, 0), (self.table_x_max, self.table_y_max)])
        self.table_poly = Polygon(orderedEdges)
        
