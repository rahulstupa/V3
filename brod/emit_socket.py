import socketio

sio = socketio.Client()

def main():
    sio.connect('http://stupa-event-api.stupaanalytics.com:5100')
    data = {}
    data['LastShotSpeed'] = 7
    data['AvgSpeed'] = 6
    data['WinnerPlacement'] = ""
    data["RallyCount"] = 9
        
    sio.emit('set', data)
    # sio.disconnect()

if __name__ == '__main__':
    main()

