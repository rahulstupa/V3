import numpy as np

class PointStats():
    def __init__(self, playerA, playerB, ball_record, score):
        self.playerA = playerA
        self.playerB = playerB
        self.ball_record = ball_record
        self.pitches = ball_record.pitches
        self.score = score
        self.rally = self.update_rally()
        self.update_player_analysis()
    
    def get_stats(self):
        stats = {}
        stats['MatchId'] = self.score['MatchId']
        stats['GameNo.'] = self.score['GameNumber']
        stats['GameScore'] = self.score['GameScore']
        stats['PointNo.'] = self.find_point_num()
        stats['FastestShot'] = self.find_fastest_shot()
        stats['LastShotSpeed'] = self.find_last_shot()
        stats['AvgSpeed'] = self.find_average_speed()
        stats['PointWinner'] = self.score["PointWinner"]
        stats['RallyCount'] = self.rally["count"]
        stats["PointTime"] = self.score['PointTime']
        stats["Pitches"] = self.find_pitches_list()
        return stats
    
    def find_point_num(self):
        return self.playerA.score+self.playerB.score
    
    def find_server(self):
        return self.playerA if self.playerA.serving else self.playerB
    
    def find_pitches_list(self):
        pitch_list = {}
        for i, pitch in enumerate(self.pitches):
            pitch_list[i] = {'pX':pitch.coords[0], 'pY':pitch.coords[1], 
                             'speed':pitch.speed}
        
        return pitch_list

    def find_fastest_shot(self):
        return max(self.pitches, key=lambda pitch:pitch.speed).speed
    
    def find_last_shot(self):
        return self.pitches[-1].speed
    
    def find_average_speed(self):
        return sum([pitch.speed for pitch in self.pitches])/len(self.pitches)
    
    def update_player_analysis(self):
        score_sum = self.playerA.score+self.playerB.score
        is_deuce = bool(self.score["Deuce"])
        serve_switched = True if ((score_sum)%2==0 or is_deuce) and score_sum>0 else False
        if self.playerA.serving:
            current_server = self.playerA
            current_receiver = self.playerB
        elif self.playerB.serving:
            current_server = self.playerB
            current_receiver = self.playerA
        
        if serve_switched:
            server = current_receiver
            receiver = current_server
        else:
            server = current_server
            receiver = current_receiver

        server.analysis["TotalService"]+=1
        server.analysis["AvgServeSpeedSum"]+=self.pitches[0].speed
        server.analysis["AvgServeSpeed"] = int(server.analysis["AvgServeSpeedSum"]/server.analysis["TotalService"])
        receiver.analysis["TotalReceive"]+=1
        
        if self.score["PointWinner"]==server.id_:
            server.analysis["PtWonOnService"]+=1
        elif self.score["PointWinner"]==receiver.id_:
            receiver.analysis["PtWonOnReceive"]+=1
        
    
    def update_rally(self):      
        point_winner = self.playerA if self.score["PointWinner"]==self.playerA.id_ else self.playerB
        
        rally_end_side = 'right' if point_winner.side=='left' else 'left'
        ball_sides = [ball.side for ball in self.ball_record.record]
        ball_dist = [ball.dist_from_center for ball in self.ball_record.record]
        last_idx = len(ball_sides) - ball_sides[::-1].index(rally_end_side)
        ball_sides = ball_sides[:last_idx]
        ball_dist = ball_dist[:last_idx]
        rally_count = 0
        prev_ball_side = ball_sides[0]
        print(rally_end_side)
        rally = {'Rally':"",'A':0,'B':0}

        for side in ball_sides:

            if side!=prev_ball_side:
                if prev_ball_side==self.playerA.side:
                    rally['A']+=1
                else:
                    rally['B']+=1
                rally_count+=1
                prev_ball_side = side
        
        if rally_count<5:
            rally["Rally"] = "Short"
        elif rally_count>=5 and rally_count<9:
            rally["Rally"] = "Medium"
        elif rally_count>9:
            rally["Rally"] = "Long"
        rally["count"] = rally_count
        
        return rally
        
class GameStats:
    def __init__(self, playerA, playerB, ball_record, score):
          self.playerA = playerA
          self.playerB = playerB
          self.ball_record = ball_record
          self.score = score
          self.rallies = []
          self.active_time = 0
    
    def add_point(self, point_stats):
        self.rallies.append(point_stats.rally)
        self.active_time+=point_stats.score["PointTime"]
        
    def get_stats(self):
        stats = {}
        stats['MatchId'] = self.score['MatchId']
        stats['GameNo.'] = self.score['GameNumber']
        stats['GameScore'] = self.score['GameScore']
        stats['GameWinner'] = self.score["GameWinner"]
        stats["SetTime"] = self.score['SetTime']
        stats["ActiveTime"] = self.active_time
        stats["Rallies"] = self.rallies
        stats["LongestRally"] = self.find_longest_rally()
        stats["IdleTime"] = self.score['SetTime'] - self.active_time
        stats["TotalPitches"] = self.find_pitches_list(self.ball_record.set_pitches)
        stats["ServicePitches"] = self.find_pitches_list(self.ball_record.set_service_pitches)
        stats["ThirdPitches"] = self.find_pitches_list(self.ball_record.set_third_pitches)
        stats["WinningPitches"] = self.find_pitches_list(self.ball_record.set_winning_pitches)
        stats["PlayerA_Analysis"] = self.playerA.analysis.copy()
        stats["PlayerB_Analysis"] = self.playerB.analysis.copy()
        return stats
    
    def find_pitches_list(self, pitches):
        pitch_list = {}
        for i, pitch in enumerate(pitches):
            pitch_list[i] = {'pX':pitch.coords[0], 'pY':pitch.coords[1], 
                             'speed':pitch.speed}
        
        return pitch_list

    def find_longest_rally(self):
        max_count = -np.inf
        longest_rally = None
        for rally in self.rallies:
            if rally["count"]>max_count:
                longest_rally = rally
                max_count = rally["count"]
        
        return longest_rally

class MatchStats:
    def __init__(self, playerA, playerB, ball_record, score):
          self.playerA = playerA
          self.playerB = playerB
          self.ball_record = ball_record
          self.score = score
          self.rallies = []
          self.active_time = 0
          self.playerA_analysis = self.playerA.analysis.copy()
          self.playerB_analysis = self.playerB.analysis.copy()
    
    def add_point(self, point_stats):
        self.rallies.append(point_stats.rally)
        self.active_time+=point_stats.score["PointTime"]
    
    def update_player_analysis(self,player_analysis, data):
        for key,val in player_analysis.items():
            player_analysis[key]+=data[key]

    def update_set_analysis(self, game_stats_json):
        self.update_player_analysis(self.playerA_analysis, game_stats_json["PlayerA_Analysis"])
        self.update_player_analysis(self.playerB_analysis, game_stats_json["PlayerB_Analysis"])
        
    def get_stats(self):
        stats = {}
        stats['MatchId'] = self.score['MatchId']
        stats['MatchNumber'] = self.score['MatchNumber']
        stats['GameScore'] = self.score['GameScore']
        stats["MatchTime"] = self.score['MatchTime']
        stats["ActiveTime"] = self.active_time
        stats["Rallies"] = self.rallies
        stats["LongestRally"] = self.find_longest_rally()
        stats["IdleTime"] = self.score['SetTime'] - self.active_time
        stats["TotalPitches"] = self.find_pitches_list(self.ball_record.match_pitches)
        stats["ServicePitches"] = self.find_pitches_list(self.ball_record.match_service_pitches)
        stats["ThirdPitches"] = self.find_pitches_list(self.ball_record.match_third_pitches)
        stats["WinningPitches"] = self.find_pitches_list(self.ball_record.match_winning_pitches)
        stats["PlayerA_Analysis"] = self.playerA_analysis
        stats["PlayerB_Analysis"] = self.playerB_analysis
        return stats
    
    def find_pitches_list(self, pitches):
        pitch_list = {}
        for i, pitch in enumerate(pitches):
            pitch_list[i] = {'pX':pitch.coords[0], 'pY':pitch.coords[1], 
                             'speed':pitch.speed}
        
        return pitch_list

    def find_longest_rally(self):
        max_count = -np.inf
        longest_rally = None
        for rally in self.rallies:
            if rally["count"]>max_count:
                longest_rally = rally
                max_count = rally["count"]
        
        return longest_rally
