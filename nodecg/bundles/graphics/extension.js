'use strict';

const { getRandomValues } = require('crypto');

function trimName(name){
	if(name.includes('/')){
		var names = name.split('/')
		names.forEach((element,index) => {
			names[index] = element.split(' ')[0]
		});
		name = names.join('/')
		return name
	}
	else if(name.length>20){
		name = name.split(' ')[0]
		return name
	}
	return name
}
function randomNumber(minimum, maximum){
    return Math.round( Math.random() * (maximum - minimum) + minimum);
}

module.exports = function (nodecg) {

	const MatchID = nodecg.Replicant('MatchID', {defaultValue: '2825859'})
	const ManualNamesSW = nodecg.Replicant('ManualNamesSW', {defaultValue:'false'})
	// ScoreBoard Binds
	const PlayerATimeout = nodecg.Replicant('PlayerATimeout')
	const PlayerBTimeout = nodecg.Replicant('PlayerBTimeout')
	const FinalPoint = nodecg.Replicant('FinalPoint')
	const FinalSet = nodecg.Replicant('FinalSet')
	const PlayingStatus = nodecg.Replicant('Status')
	const PLayerADATA = nodecg.Replicant('PLayerADATA',)
	const PLayerBDATA = nodecg.Replicant('PLayerBDATA',)
	const PlayerASetScoreDATA = nodecg.Replicant('PlayerASetScoreDATA',)
	const PlayerBSetScoreDATA = nodecg.Replicant('PlayerBSetScoreDATA',)
	const CurrentSetA = nodecg.Replicant('CurrentSetA')
	const CurrentSetB = nodecg.Replicant('CurrentSetB')
	const TeamScoreA = nodecg.Replicant('TeamScoreA',{defaultValue: 0})
	const TeamScoreB = nodecg.Replicant('TeamScoreB',{defaultValue: 0})
	const PlayerAGameScoreDATA = nodecg.Replicant('PlayerAGameScoreDATA',{defaultValue: 0})
	const PlayerBGameScoreDATA = nodecg.Replicant('PlayerBGameScoreDATA',{defaultValue: 0})
	const PlayerServing = nodecg.Replicant('PlayerServing', {defaultValue: -1})
	
	// RallyCount Binds
	const RallyCount = nodecg.Replicant('RallyCount')
	// ShotSpeed Binds
	const ShotSpeed = nodecg.Replicant('ShotSpeed')
	// GameSummary Bindings
	const GameTotalServesA = nodecg.Replicant('GameTotalServesA')
	const GameTotalServesWinA = nodecg.Replicant('GameTotalServesWinA')
	const GameTotalReceivesA = nodecg.Replicant('GameTotalReceivesA')
	const GameTotalReceivesWinA = nodecg.Replicant('GameTotalReceivesWinA')
	const GameAvgServeSpeedA = nodecg.Replicant('GameAvgServeSpeedA')
	const GameTotalServesB = nodecg.Replicant('GameTotalServesB')
	const GameTotalServesWinB = nodecg.Replicant('GameTotalServesWinB')
	const GameTotalReceivesB = nodecg.Replicant('GameTotalReceivesB')
	const GameTotalReceivesWinB = nodecg.Replicant('GameTotalReceivesWinB')
	const GameAvgServeSpeedB = nodecg.Replicant('GameAvgServeSpeedB')

	// MatchSummary Bindings
	const MatchTotalServesA = nodecg.Replicant('MatchTotalServesA')
	const MatchTotalServesWinA = nodecg.Replicant('MatchTotalServesWinA')
	const MatchTotalReceivesA = nodecg.Replicant('MatchTotalReceivesA')
	const MatchTotalReceivesWinA = nodecg.Replicant('MatchTotalReceivesWinA')
	const MatchAvgServeSpeedA = nodecg.Replicant('MatchAvgServeSpeedA')
	const MatchTotalServesB = nodecg.Replicant('MatchTotalServesB')
	const MatchTotalServesWinB = nodecg.Replicant('MatchTotalServesWinB')
	const MatchTotalReceivesB = nodecg.Replicant('MatchTotalReceivesB')
	const MatchTotalReceivesWinB = nodecg.Replicant('MatchTotalReceivesWinB')
	const MatchAvgServeSpeedB = nodecg.Replicant('MatchAvgServeSpeedB')
	var coordinates = nodecg.Replicant('coordinates')

	const socket_io_client = require('socket.io-client');
	const io = socket_io_client('http://stupa-event-api.stupaanalytics.com:5100');
	const io2 = socket_io_client('http://localhost:5100');

	console.log(ManualNamesSW.value)
	io.on('score', (data) => {
		if(String(data.MatchId)===String(MatchID.value)){
			console.log(data)
			PLayerADATA.value = trimName(data.PlayerAName)
			PLayerBDATA.value = trimName(data.PlayerBName)
			PlayerASetScoreDATA.value = String(data.SetScoreA)
			PlayerBSetScoreDATA.value = String(data.SetScoreB)
			CurrentSetA.value = String(data.CurrentSetScoreA)
			CurrentSetB.value = String(data.CurrentSetScoreB)
			PlayerAGameScoreDATA.value = String(data.GameScoreA)
			PlayerBGameScoreDATA.value = String(data.GameScoreB)
			FinalPoint.value = data.FinalPoint
			FinalSet.value = data.FinalSet
			PlayingStatus.value = data.Status
			PlayerATimeout.value = data.PlayerATimeout
			PlayerBTimeout.value = data.PlayerBTimeout

			
			if(data.ServiceBy==data.PlayerAId){
				PlayerServing.value = "ServeA"
			}
			else{
				PlayerServing.value = "ServeB"
			}

			if((PlayerAGameScoreDATA.value==0 && PlayerBGameScoreDATA.value==0) && (PlayerASetScoreDATA.value==0 && PlayerBSetScoreDATA.value==0)) {
				nodecg.sendMessage('matchStart')
				console.log('New Match Started')
			}
			if(FinalPoint.value == true) {
				nodecg.sendMessage('triggerSetfinish')
				console.log('Set Finish Triggered')

			}
			if(FinalSet.value == true || PlayingStatus.value == 'destroy') {
				nodecg.sendMessage('triggerMatchfinish')
				console.log('Match Finish Triggered')
				
			}
			if(PlayerAGameScoreDATA.value==0 && PlayerBGameScoreDATA.value==0){
				nodecg.sendMessage('triggerSetstart')
				console.log('Set Start Triggered')
			}
			
			if (FinalSet.value == false && PlayingStatus.value != 'destroy' && FinalPoint.value == false) {

				if (PlayerATimeout.value == true) {
					nodecg.sendMessage('triggerAtimeout')
				}
				if (PlayerBTimeout.value == true) {
					nodecg.sendMessage('triggerBtimeout')
				}

			}		
		}
		else{
			console.log("Please Check MatchID in Dashboard")
		}
	});
	io2.on('tracking', (data) => {
		console.log(data)
		// coordinates = data;
		nodecg.sendMessage('showPitches', data, coordinates)
	})
	io.on('teamscore', (data) => {
		if(String(data.MatchId)===String(MatchID.value)){
			console.log(data.teamAScore, data.teamBScore)
			console.log("Score Received")
			
			TeamScoreA.value = String(data.teamAScore)
			TeamScoreB.value = String(data.teamBScore)
			
		}
		else{
			console.log("Please Check MatchID in Dashboard")
		}
	});
	io2.on('point', (data) => {
		// if(String(data.MatchId)===String(MatchID.value)){
			console.log("Point Over")
			RallyCount.value = String(data.RallyCount)
			ShotSpeed.value = String(data.LastShotSpeed)
			nodecg.sendMessage("clearPitches")
			nodecg.sendMessage('triggerRallyGraphic')
		// }

		
		
	});
	io2.on('set', (data) => {
		// if(String(data.MatchId)===String(MatchID.value)){
			GameTotalServesA.value = data.playerA_analysis.TotalService
			GameTotalServesWinA.value = data.playerA_analysis.PtWonOnService
			GameTotalReceivesA.value = data.playerA_analysis.TotalReceive
			GameTotalReceivesWinA.value = data.playerA_analysis.PtWonOnReceive
			GameAvgServeSpeedA.value = data.playerA_analysis.AvgServeSpeed
			GameTotalServesB.value = data.playerB_analysis.TotalService
			GameTotalServesWinB.value = data.playerB_analysis.PtWonOnService
			GameTotalReceivesB.value = data.playerB_analysis.TotalReceive
			GameTotalReceivesWinB.value = data.playerB_analysis.PtWonOnReceive
			GameAvgServeSpeedB.value = data.playerB_analysis.AvgServeSpeed
			nodecg.sendMessage("triggerSetHeatmaps")
			console.log("Game summary TRIGGERED")
		// }
	});
	io2.on('match', (data) => {
		// if(String(data.MatchId)===String(MatchID.value)){
			MatchTotalServesA.value = data.playerA_analysis.TotalService
			MatchTotalServesWinA.value = data.playerA_analysis.PtWonOnService
			MatchTotalReceivesA.value = data.playerA_analysis.TotalReceive
			MatchTotalReceivesWinA.value = data.playerA_analysis.PtWonOnReceive
			MatchAvgServeSpeedA.value = data.playerA_analysis.AvgServeSpeed
			MatchTotalServesB.value = data.playerB_analysis.TotalService
			MatchTotalServesWinB.value = data.playerB_analysis.PtWonOnService
			MatchTotalReceivesB.value = data.playerB_analysis.TotalReceive
			MatchTotalReceivesWinB.value = data.playerB_analysis.PtWonOnReceive
			MatchAvgServeSpeedB.value = data.playerB_analysis.AvgServeSpeed
			nodecg.sendMessage("triggerMatchHeatmaps")
			console.log("MATCH summary TRIGGERED")

		// }
	});
	
};

