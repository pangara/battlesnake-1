import bottle
import os
from Game import Game

games = {}


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start(data):
    #data = bottle.request.json
    games[data["game_id"]] = Game(data)
    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )
    return {
        'color': '#BADA55',
        'taunt': 'Hasta la vista, baby',
        'head_url': head_url,
        'name': 'Sneakey Sneakerson'
    }


@bottle.post('/move')
def move(data):
    #data = bottle.request.json
    return {
        'move': games[data["game_id"]].move(data),
        'taunt': 'Hasta la vista, baby'
    }


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    #bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
    start({
        'game_id': '6c41d3e0-7374-4e19-bd59-ca1bd1aa4d4a',
        'width': 20,
        'height': 20
    })
    move({
        'snakes': [
            {
                'health_points': 100,
                'taunt': '6c41d3e0-7374-4e19-bd59-ca1bd1aa4d4a (20x20)',
                'coords': [
                    [5, 4],
                    [5, 4],
                    [5, 4]
                ],
                'name': 'Sneakey Sneakerson',
                'id': '51f6ae95-1fe7-44f3-9148-14ba138071b7'
            }
        ],
        'turn': 0,
        'food': [
            [12, 12],
            [5, 0],
            [2, 5]
        ],
        'height': 20,
        'width': 20,
        'dead_snakes': [],
        'game_id': '6c41d3e0-7374-4e19-bd59-ca1bd1aa4d4a',
        'you': '51f6ae95-1fe7-44f3-9148-14ba138071b7'
    })
