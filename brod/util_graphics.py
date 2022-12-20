from asyncore import read
import cv2
from html2image import Html2Image
import os.path as osp
from PIL import Image
import numpy as np
from graphic import AnimatedGraphic, CombinedGraphic, ChainGraphics, SequenceGraphic

def check_name(name):
    if name.find(" ") == -1:
        return name
    else:
        nameary = name.split(" ")
        return nameary[0] + " " + nameary[1][0].upper()

def read_graphic(name):
    path = osp.join('./graphics/htmlResults/', name)
    return cv2.imread(path,cv2.IMREAD_UNCHANGED)

def overlay_scoreboard(img, scoreboard):
    # print (img.shape, self.scoreboard.shape)
    # return overlay_transparent(img, self.scoreboard, 0, 0)
    back = Image.fromarray(img)
    scoreboard = Image.fromarray(scoreboard)
    back.paste(scoreboard, (0,0), scoreboard)
    return np.array(back)

def load_scoreboard(playerA, playerB ):
    hti = Html2Image(output_path = './graphics/htmlResults/')
    f =  open('./graphics/htmlTemplates/scoreBoard/ScoreBoard.html', 'r')
    htmlStr = f.read()
    htmlStr= htmlStr.replace("PLayerADATA", check_name(playerA.name))
    htmlStr= htmlStr.replace("PlayerAGameScoreDATA", str(playerA.score))
    htmlStr= htmlStr.replace("PlayerASetScoreDATA", str(playerA.set_score))
    htmlStr= htmlStr.replace("PLayerBDATA", check_name(playerB.name))
    htmlStr= htmlStr.replace("PlayerBGameScoreDATA", str(playerB.score))
    htmlStr= htmlStr.replace("PlayerBSetScoreDATA", str(playerB.set_score))

    hti.screenshot(html_str=htmlStr, save_as='scoreboard.png', size=(1920, 1080))
    f.close()
    return read_graphic('scoreboard.png')

def overlay_rallyboard(img, rallyboard):
    # print (img.shape, self.scoreboard.shape)
    # return overlay_transparent(img, self.scoreboard, 0, 0)
    back = Image.fromarray(img)
    scoreboard = Image.fromarray(rallyboard)
    back.paste(scoreboard, (0,0), scoreboard)
    return np.array(back)

def loadAfterPoint(stats, stream):
    hti = Html2Image(output_path = './graphics/htmlResults/')
    with open('./graphics/htmlTemplates/pointRally/LastRallyCount.html', 'r') as f:
        htmlStr = f.read()
    htmlStr = htmlStr.replace("Data",str(stats['RallyCount']))
    hti.screenshot(html_str=htmlStr, save_as='rallyboard.png', size=(1920, 1080))
    f.close()

    with open('./graphics/htmlTemplates/pointSpeed/WinnerShotSpeed.html', 'r') as f:
        htmlStr = f.read()
    htmlStr = htmlStr.replace("Data", str(int(stats['LastShotSpeed'])))
    hti.screenshot(html_str=htmlStr, save_as='speedboard.png', size=(1920, 1080))
    f.close()
    
    stream.rallyboard = AnimatedGraphic('rallyboard.png', stream.fps, 3, ready = True)
    stream.speedboard = AnimatedGraphic('speedboard.png', stream.fps, 3, ready = False)
    
    
def is_graphic_ready(graphic):
    if graphic is not None and graphic.ready:
        return True

def loadAfterSet(playerA, playerB, stats, stream):
    hti = Html2Image(output_path = './graphics/htmlResults/')
    with open('./graphics/htmlTemplates/gameSummary/GameSummary.html', 'r') as f:
        htmlStr = f.read()
    htmlStr = htmlStr.replace("PLayerADATA", check_name(playerA.name))
    htmlStr = htmlStr.replace("PlayerAGameScoreDATA", str(playerA.score))
    htmlStr = htmlStr.replace("PLayerBDATA", check_name(playerB.name))
    htmlStr = htmlStr.replace("PlayerBGameScoreDATA", str(playerB.score))
    htmlStr = htmlStr.replace("TotalServeA", str(stats['PlayerA_Analysis']['TotalService']))
    htmlStr = htmlStr.replace("TotalServeB", str(stats['PlayerB_Analysis']['TotalService']))
    htmlStr = htmlStr.replace("ServeWinA", str(stats['PlayerA_Analysis']['PtWonOnService']))
    htmlStr = htmlStr.replace("ServeWinB", str(stats['PlayerB_Analysis']['PtWonOnService']))
    htmlStr = htmlStr.replace("TotalReceiveA", str(stats['PlayerA_Analysis']['TotalReceive']))
    htmlStr = htmlStr.replace("TotalReceiveB", str(stats['PlayerB_Analysis']['TotalReceive']))
    htmlStr = htmlStr.replace("ReceiveWinA", str(stats['PlayerA_Analysis']['PtWonOnReceive']))
    htmlStr = htmlStr.replace("ReceiveWinB", str(stats['PlayerB_Analysis']['PtWonOnReceive']))
    htmlStr = htmlStr.replace("ServeSpeedA", str(stats['PlayerA_Analysis']['AvgServeSpeed']))
    htmlStr = htmlStr.replace("ServeSpeedB", str(stats['PlayerB_Analysis']['AvgServeSpeed']))

    hti.screenshot(html_str=htmlStr, save_as='gameboard.png', size=(1920, 1080))
    f.close()
    total = AnimatedGraphic('graphics/heatmaps/set_heatmap.png', 25, 3, ready=True, partial=False, delay=1)
    serve = AnimatedGraphic('graphics/heatmaps/set_service_heatmap.png', 25, 3, ready=False, partial=False,)
    third = AnimatedGraphic('graphics/heatmaps/set_third_heatmap.png', 25, 3, ready=False, partial=False, )
    winning = AnimatedGraphic('graphics/heatmaps/set_winning_heatmap.png', 25, 3, ready=False, partial=False, ) 
    # third = AnimatedGraphic('graphics/3rd Ball.png'), stream.fps, 2, ready=False)
    # placement = AnimatedGraphic('graphics/heatmaps/set_third_heatmap.png'), stream.fps, 2, ready=False)
    base = SequenceGraphic('./graphics/heatmapDetail/GAME HEAT MAP', ready = True)
    
    gameSummary = AnimatedGraphic('gameboard.png', stream.fps, 8, ready=False) 
    
    all_heatmaps = ChainGraphics([total, serve, third, winning], ready=True)
    complete_heatmap = CombinedGraphic([base, all_heatmaps], ready=True)
    final = ChainGraphics([complete_heatmap, gameSummary], ready=True) 
    stream.afterGame = final

def loadAfterMatch(playerA, playerB, stats, stream):
    hti = Html2Image(output_path = './graphics/htmlResults/')
    with open('./graphics/htmlTemplates/matchSummary/MatchSummary.html', 'r') as f:
        htmlStr = f.read()
    htmlStr = htmlStr.replace("PLayerADATA", check_name(playerA.name))
    htmlStr = htmlStr.replace("PlayerAGameScoreDATA", str(playerA.score))
    htmlStr = htmlStr.replace("PLayerBDATA", check_name(playerB.name))
    htmlStr = htmlStr.replace("PlayerBGameScoreDATA", str(playerB.score))
    htmlStr = htmlStr.replace("TotalServeA", str(stats['PlayerA_Analysis']['TotalService']))
    htmlStr = htmlStr.replace("TotalServeB", str(stats['PlayerB_Analysis']['TotalService']))
    htmlStr = htmlStr.replace("ServeWinA", str(stats['PlayerA_Analysis']['PtWonOnService']))
    htmlStr = htmlStr.replace("ServeWinB", str(stats['PlayerB_Analysis']['PtWonOnService']))
    htmlStr = htmlStr.replace("TotalReceiveA", str(stats['PlayerA_Analysis']['TotalReceive']))
    htmlStr = htmlStr.replace("TotalReceiveB", str(stats['PlayerB_Analysis']['TotalReceive']))
    htmlStr = htmlStr.replace("ReceiveWinA", str(stats['PlayerA_Analysis']['PtWonOnReceive']))
    htmlStr = htmlStr.replace("ReceiveWinB", str(stats['PlayerB_Analysis']['PtWonOnReceive']))
    htmlStr = htmlStr.replace("ServeSpeedA", str(stats['PlayerA_Analysis']['AvgServeSpeed']))
    htmlStr = htmlStr.replace("ServeSpeedB", str(stats['PlayerB_Analysis']['AvgServeSpeed']))

    hti.screenshot(html_str=htmlStr, save_as='matchboard.png', size=(1920, 1080))
    f.close()
    total = AnimatedGraphic('graphics/heatmaps/match_heatmap.png', 25, 3, ready=True, partial=False, delay=1)
    serve = AnimatedGraphic('graphics/heatmaps/match_service_heatmap.png', 25, 3, ready=False, partial=False,)
    third = AnimatedGraphic('graphics/heatmaps/match_third_heatmap.png', 25, 3, ready=False, partial=False, )
    winning = AnimatedGraphic('graphics/heatmaps/match_winning_heatmap.png', 25, 3, ready=False, partial=False, ) 
    # third = AnimatedGraphic('graphics/3rd Ball.png'), stream.fps, 2, ready=False)
    # placement = AnimatedGraphic('graphics/heatmaps/set_third_heatmap.png'), stream.fps, 2, ready=False)
    base = SequenceGraphic('./graphics/heatmapDetail/MATCH HEAT MAP', ready = True)
    
    gameSummary = AnimatedGraphic('matchboard.png', stream.fps, 8, ready=False) 
    
    all_heatmaps = ChainGraphics([total, serve, third, winning], ready=True)
    complete_heatmap = CombinedGraphic([base, all_heatmaps], ready=True)
    final = ChainGraphics([complete_heatmap, gameSummary], ready=True) 
    stream.afterGame = final