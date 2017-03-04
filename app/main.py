import bottle
import os
from Game import Game

games = {}


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    games[data["game_id"]] = Game(data)
    print("here", games[data["game_id"]])
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
def move():
    data = bottle.request.json
    print(data["game_id"], games)
    return {
        'move': games[data["game_id"]].move(data),
        'taunt': 'Hasta la vista, baby'
    }


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
