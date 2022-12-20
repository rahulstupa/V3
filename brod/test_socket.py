import socketio

sio = socketio.Client()


@sio.event
def connect():
    print('connected')

@sio.on('set')
def set(data):
    print("Set Data")
    print(data)

@sio.on('match')
def set(data):
    print("Match Data")
    print(data)

# @sio.event
# def score(data):
    # print(data)
    # sio.disconnect()
  


@sio.event
def connect_error(e):
    print("Printing error")
    print(e)


@sio.event
def disconnect():
    print('disconnected')


def main():
    sio.connect('http://stupa-event-api.stupaanalytics.com:5100')
    sio.wait()


if __name__ == '__main__':
    main()

