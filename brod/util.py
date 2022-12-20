import os
import socketio
from urllib.request import urlopen
import json
import math
import numpy as np
import cv2
from PIL import ImageFont, ImageDraw, Image
import time

def reconnect():
    sio = socketio.Client()
    sio.connect('http://localhost:5100')
    # sio.wait()
    return sio

def emit_set_json(game_stats, sio, playerA, playerB):
        time.sleep(3)
        data = {}
        data["playerA_name"] = playerA.name
        data["playerB_name"] = playerB.name
        data["playerA_id"] = playerA.id_
        data["playerB_id"] = playerB.id_
        data["playerA_analysis"] = game_stats["PlayerA_Analysis"]
        data["playerB_analysis"] = game_stats["PlayerB_Analysis"]

        sio.emit('set', data)

def emit_match_json(match_stats, sio, playerA, playerB):
        # time.sleep(15)
        data = {}
        data["playerA_name"] = playerA.name
        data["playerB_name"] = playerB.name
        data["playerA_id"] = playerA.id_
        data["playerB_id"] = playerB.id_
        data["playerA_analysis"] = match_stats["PlayerA_Analysis"]
        data["playerB_analysis"] = match_stats["PlayerB_Analysis"]

        sio.emit('match', data)

def get_matchid():
    print("Please provide a Re-Point in Stupa Events to Fetch Match ID")
    os.system("python soc_client_event.py>matchid.txt")
    with open("matchid.txt", "r") as f:
        text = f.read()
    start_idx = text.index(":") + 2
    end_idx = text.index(",")
    match_id = text[start_idx:end_idx]
    print(f"Match ID Fetched : {match_id}")
    return match_id


def get_match_details(MatchId):
    with open('./StreamConfiguration.json') as f:
        ConfigFile = json.load(f)
    MatchId = int(MatchId)
    url = ConfigFile['fetchMatchAPI'] + str(MatchId)
    response = urlopen(url)
    data = response.read().decode(response.headers.get_content_charset())
    data = json.loads(data)["data"]
    if data["playerSide"] is None:
        data["playerSide"] = "left"
    return data

def drawline(img, pt1, pt2, color, thickness, style='dotted', gap=20):
    dist = ((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2) ** .5
    pts = []
    # print('inside_function_drawline')
    for i in np.arange(0, dist, gap):
        r = i / dist
        x = int((pt1[0] * (1 - r) + pt2[0] * r) + .5)
        y = int((pt1[1] * (1 - r) + pt2[1] * r) + .5)
        p = (x, y)
        pts.append(p)

    if style == 'dotted':
        for p in pts:
            cv2.circle(img, p, thickness, color, -1)
    else:
        s = pts[0]
        e = pts[0]
        i = 0
        for p in pts:
            s = e
            e = p
            if i % 2 == 1:
                cv2.line(img, s, e, color, thickness)
            i += 1
    return img

def drawLine(image, regionLengths, coordinates):
    for i, Ypos in enumerate(regionLengths):
        if i == 0:
            x1, x2 = int(coordinates[0][0]), int(coordinates[1][0])
            y1, y2 = int(coordinates[0][1]), int(coordinates[1][1])
        elif i == 1:
            x1, x2 = int(coordinates[3][0]) + int((coordinates[0][0] - coordinates[3][0]) * (2 / 3)), int(
                coordinates[1][0]) + int((coordinates[2][0] - coordinates[1][0]) * (1 / 3))
            y1, y2 = int(coordinates[0][1]) + int((coordinates[3][1] - coordinates[0][1]) * (1 / 3)), int(
                coordinates[1][1]) + int((coordinates[2][1] - coordinates[1][1]) * (1 / 3))
        elif i == 2:
            x1, x2 = int(coordinates[3][0]) + int((coordinates[0][0] - coordinates[3][0]) * (1 / 3)), int(
                coordinates[1][0]) + int((coordinates[2][0] - coordinates[1][0]) * (2 / 3))
            y1, y2 = int(coordinates[0][1]) + int((coordinates[3][1] - coordinates[0][1]) * (2 / 3)), int(
                coordinates[1][1]) + int((coordinates[2][1] - coordinates[1][1]) * (2 / 3))
        else:
            x1, x2 = int(coordinates[3][0]), int(coordinates[2][0])
            y1, y2 = int(coordinates[3][1]), int(coordinates[2][1])
        cv2.line(image, (x1, y1), (x2, y2), (148, 210, 150), 2, cv2.LINE_AA)
    return image

def line_intersection(line1, line2):
    try:
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return (a[0] * b[1]) - (a[1] * b[0])

        div = det(xdiff, ydiff)
        if div == 0:
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        # print("sending x, y back")
        return x, y
    except:
        # print("Line Dont intersect")
        return 0, 0

def overlay_transparent(background, overlay, x, y, alpha=False):
    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        overlay = np.concatenate(
            [
                overlay,
                np.ones((overlay.shape[0], overlay.shape[1], 1), dtype=overlay.dtype) * 255
            ],
            axis=2,
        )

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0
    if not alpha:
        background[y:y + h, x:x + w] = (1.0 - mask) * background[y:y + h, x:x + w] + mask * overlay_image
    else:
        background[y:y + h, x:x + w, 3:] = overlay[..., 3:]
        background[y:y + h, x:x + w, :3] = overlay_image
        
    return background

def point_distance(x2, x1, y2, y1):
    dist = abs(math.hypot(x2 - x1, y2 - y1))
    return round(dist, 2)

def get_line_corners(ball, shape_X):
    # vx, vy, x, y = row['cX'], row['cY'], row['x'], row['y']
    # left_pt = int((-x * vy / vx) + y)
    vx, vy, x, y = ball.vX, ball.vY, ball.x, ball.y
    left_pt = int((-x * vy / vx) + y)
    right_pt = int(((shape_X - x) * vy / vx) + y)
    return left_pt, right_pt

def getLine(x1, y1, x2, y2):
    if x1 == x2:  ## Perfectly horizontal line, can be solved easily
        return [(x1, i) for i in range(y1, y2, int(abs(y2 - y1) / (y2 - y1)))]
    else:  ## More of a problem, ratios can be used instead
        if x1 > x2:  ## If the line goes "backwards", flip the positions, to go "forwards" down it.
            x = x1
            x1 = x2
            x2 = x
            y = y1
            y1 = y2
            y2 = y
        slope = (y2 - y1) / (x2 - x1)  ## Calculate the slope of the line
        line = []
        i = 0
        while x1 + i < x2:  ## Keep iterating until the end of the line is reached
            i += 1
            line.append((x1 + i, y1 + slope * i))  ## Add the next point on the line
        return line  ## Finally, return the line!



def GetZonePercentages(image, coordinates, pitches, center, lHand, rHand):
    LR1, LR2, LR3, RR1, RR2, RR3 = 0, 0, 0, 0, 0, 0
    BH, C, FH = 'BH', 'C', 'FH'
    bufferPixels = 2
    regionsOrdered = []
    if lHand.lower() == 'lefty':
        regionsOrdered.append(FH)
        regionsOrdered.append(C)
        regionsOrdered.append(BH)
    else:
        regionsOrdered.append(BH)
        regionsOrdered.append(C)
        regionsOrdered.append(FH)
    if rHand.lower() == 'lefty':
        regionsOrdered.append(BH)
        regionsOrdered.append(C)
        regionsOrdered.append(FH)
    else:
        regionsOrdered.append(FH)
        regionsOrdered.append(C)
        regionsOrdered.append(BH)

    # Get RegionBorders
    L0 = int(min([coordinates[0][1], coordinates[1][1]]) - bufferPixels)
    L3 = int(max([coordinates[2][1], coordinates[3][1]]) + bufferPixels)
    L1 = int(((L3 - L0) / 3) + L0)
    L2 = int((((L3 - L0) / 3) * 2) + L0)

    for pitch in pitches:
        if pitch.coords[1] >= L0 and pitch.coords[1] < L1:
            if pitch.side=='right':
                RR1 += 1
            else:
                LR1 += 1
        elif pitch.coords[1] >= L1 and pitch.coords[1] < L2:
            if pitch.side=='right':
                RR2 += 1
            else:
                LR2 += 1
        else:
            if pitch.side=='right':
                RR3 += 1
            else:
                LR3 += 1
    resolution = image.shape[0:2]
    # print(resolution)
    drawPositions = getPositions(coordinates, [L0, L1, L2, L3], resolution, center)
    image = drawLine(image, [L0, L1, L2, L3], coordinates)
    count = 0
    wordsize = 22
    font = ImageFont.truetype('./graphics/fonts/Prometo-Black.ttf', wordsize)

    for Val, position, region in zip([LR1, LR2, LR3, RR1, RR2, RR3], list(drawPositions.values()), regionsOrdered):
        if count < 3:
            percentage = int(round((Val / (LR1 + LR2 + LR3)) * 100, 2))

        else:
            percentage = int(round((Val / (RR1 + RR2 + RR3)) * 100, 2))

        if percentage < 50:
            img_pil = Image.fromarray(image)
            draw = ImageDraw.Draw(img_pil)
            draw.text(position, str(percentage) + "%", font=font, fill=(255, 255, 255, 0))
            image = np.array(img_pil)
            # old
            # cv2.putText(image, str(percentage) + "%", position, cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
        else:
            img_pil = Image.fromarray(image)
            draw = ImageDraw.Draw(img_pil)
            draw.text(position, str(percentage) + "%", font=font, fill=(3, 230, 18, 0))
            image = np.array(img_pil)
            # old
            # cv2.putText(image, str(percentage) + "%", position, cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        count += 1
    return image

def getPositions(coordinates, regionLengths, res, center):
    positions = {}
    yshift = 20
    center1 = int((coordinates[0][0] - coordinates[3][0]) / 2) + coordinates[3][0]
    positions['LBH'] = (int(center1 + ((6 / 100) * res[1])),
                        int(((regionLengths[1] - regionLengths[0]) * (70 / 100)) - yshift) + regionLengths[0])
    positions['LC'] = (int(center1 + ((5 / 100) * res[1])),
                       
                       int(((regionLengths[2] - regionLengths[1]) * (70 / 100)) - yshift) + regionLengths[1])
    positions['LFH'] = (int(center1 + ((4 / 100) * res[1])),
                        int(((regionLengths[3] - regionLengths[2]) * (70 / 100)) - yshift) + regionLengths[2])
    positions['RFH'] = (int(center[0] + ((4 / 100) * res[1])),
                        int(((regionLengths[1] - regionLengths[0]) * (70 / 100)) - yshift) + regionLengths[0])
    positions['RC'] = (int(center[0] + ((5 / 100) * res[1])),
                       int(((regionLengths[2] - regionLengths[1]) * (70 / 100)) - yshift) + regionLengths[1])
    positions['RBH'] = (int(center[0] + ((6 / 100) * res[1])),
                        int(((regionLengths[3] - regionLengths[2]) * (70 / 100)) - yshift) + regionLengths[2])
    return positions

def getTransformation(X, Y, Center, Leftlin, Rightlin, ordedges, width, height, player):
    newX, newY = 0, 0
    greater = [True if int(X) > int(Center[0]) else False][0]
    if not greater:
        a, b = zip(*Leftlin)
        cY = Y
        if int(Y) in b:
            cY = Y
        elif int(Y) + 1 in b:
            cY = Y + 1
        elif int(Y) - 1 in b:
            cY = Y - 1
        for p in Leftlin:
            if cY == p[1]:
                percentageX = abs(X - p[0]) / abs(int(Center[0]) - p[0])
                newX = percentageX * (width / 2)

                percentageY = abs(p[1] - min(ordedges[0][1], ordedges[1][1]) + 0) / abs(
                    max(ordedges[2][1], ordedges[3][1]) - min(ordedges[0][1], ordedges[1][1]))
                newY = percentageY * (height)
                break

    else:
        a, b = zip(*Rightlin)
        cY = Y
        if int(Y) in b:
            cY = Y
        elif int(cY) + 1 in b:
            cY = Y + 1
        elif int(cY) - 1 in b:
            cY = Y - 1
        for p in Rightlin:
            if cY == p[1]:
                percentage = abs(X - p[0]) / abs(int(Center[0]) - p[0])
                newX = ((1 - percentage) * (width / 2)) + (width / 2)

                percentageY = abs(p[1] - min(ordedges[0][1], ordedges[1][1]) + 0) / abs(
                    max(ordedges[2][1], ordedges[3][1]) - min(ordedges[0][1], ordedges[1][1]))
                newY = percentageY * (height)
                break
    point_trans = [newX, newY]

    place = placement(int(point_trans[0]), int(point_trans[1]), width, height, greater,
                      player[1])
    rotPoint = rotate([int(point_trans[0]), int(point_trans[1])], height, width, 90)
    if player[2] == 'right':
        rotPoint = rotate([int(rotPoint[0]), int(rotPoint[1])], width, height, 180)
    return rotPoint[0], rotPoint[1], place