import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.heuristics.euclidean import euclidean
from pygraph.algorithms.heuristics.chow import chow
from pygraph.classes import exceptions


class Game(object):
    snake = {}
    turn = 0

    def __init__(self, data):
        self.game = data['game_id']
        self.height = data['height']
        self.width = data['width']

    # Q1: does the board size change?
    def move(self, data):
        m = "up"
        if not self.is_dead(data["you"], data["dead_snakes"]):
            self.snake = self.get_snake(data["you"], data["snakes"])
            self.turn = data["turn"]
            board = self.make_board(data["snakes"])
            food = data["food"]
        else:
            print("I'm dead. Turns played: %d" % self.turn)
        return m

    def is_dead(self, snake_id, dead_snakes):
        filtered = filter(lambda snake: snake["id"] == snake_id, dead_snakes)
        return len(filtered) == 1

    def make_board(self, snakes):
        board = graph()
        obstacles = self.find_obstacles(snakes)
        node = 0
        for i in range(0, self.height):
            for j in range(0, self.width):
                if (i, j) not in obstacles:
                    board.add_node(node)
                node += 1
        return board

    def find_obstacles(self, snakes):
        obstacles = set()
        for snake in snakes:
            # all snakes' bodies
            obstacles.update([tuple(position) for position in snake["coords"][1:]])
            # shorter snakes' heads
            # a snake is not shorter than itself
            shorter = len(snake["coords"]) < len(self.snake["coords"])
            if shorter:
                obstacles.add(tuple(snake["coords"][1]))
        return obstacles

    @staticmethod
    def get_snake(snake_id, snakes):
        return [snake for snake in snakes if snake["id"] == snake_id][0]
