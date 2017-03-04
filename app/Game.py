import sys
from pygraph.algorithms.minmax import heuristic_search
from pygraph.classes.graph import graph
from pygraph.algorithms.heuristics.chow import chow
from pygraph.classes.exceptions import NodeUnreachable

class Game(object):
    snake = {}
    turn = 0

    def __init__(self, data):
        self.game = data['game_id']
        self.height = data['height']
        self.width = data['width']

    def move(self, data):
        next_move = "up"
        if not self.is_dead(data["you"], data["dead_snakes"]):
            data = self.translate(data);
            self.snake = self.get_snake(data["you"], data["snakes"])
            self.turn = data["turn"]
            self.height = data["height"]
            self.width = data["width"]
            board = self.make_board(data["snakes"])
            foods = [tuple(node) for node in data["food"]]

            # 1. Distances
            paths, distances = self.a_star(foods, board)
            total = float(reduce(lambda a, b: a + b, distances.values()))

            print("CURRENT", self.snake["coords"], self.snake["coords"][0])
            print(paths)
            print(distances)

            # 1.1 Simulate another iteration. Is ther any food node close to another food node?

            # 2. Risk averse
            risks = dict(map(lambda f: (f, 1), foods))

            # 3. Probability of kill
            kills = dict(map(lambda f: (f, 1), foods))

            # 4. Selection
            # distance/td * (Probability of being alive * Probability of kill)
            scores = {}
            for f in foods:
                scores[f] = (distances[f]/total) * risks[f] * kills[f]

            best = min(scores, key=scores.get)
            next_move = self.next_direction(tuple(self.snake["coords"][0]), paths[best][0])
            print(next_move)
            print("\n\n")
        else:
            print("I'm dead. Turns played: %d" % self.turn)
        return next_move

    def make_board(self, snakes):
        board = graph()
        obstacles = self.find_obstacles(snakes)
        for i in range(0, self.height):
            for j in range(0, self.width):
                if (i, j) not in obstacles:
                    board.add_node((i, j))
        for node in board.nodes():
            for neighbor in self.neighbors(node, board):
                if not board.has_edge((node, neighbor)):
                    board.add_edge((node, neighbor))
        return board

    def find_obstacles(self, snakes):
        obstacles = set()
        for snake in snakes:
            _id = snake["id"]
            _coordinates = snake["coords"]
            # all snakes' bodies, unless it is our snake, and its head == its body
            obstacles.update(
                [
                    tuple(position) for position in _coordinates[1:]
                    if not (_id == self.snake["id"] and _coordinates[0] == _coordinates[1])
                ]
            )
            # ignore shorter snakes' heads
            # a snake is not shorter than itself
            shorter = len(snake["coords"]) < len(self.snake["coords"])  # is their snake shorter?
            if not shorter and _id != self.snake["id"]:
                obstacles.add(tuple(snake["coords"][0]))
        return obstacles

    def a_star(self, foods, board):
        heuristic = chow(*foods)
        heuristic.optimize(board)
        paths = {}
        distances = {}
        for food in foods:
            try:
                paths[food] = heuristic_search(board, tuple(self.snake["coords"][0]), food, heuristic)
                paths[food] = paths[food][1:]
                distances[food] = len(paths[food])
            except NodeUnreachable as e:
                distances[food] = sys.maxint
                print("UNREACHABLE: %s" % e)
                pass
        return paths, distances

    @staticmethod
    def is_dead(snake_id, dead_snakes):
        filtered = filter(lambda snake: snake["id"] == snake_id, dead_snakes)
        return len(filtered) == 1

    @staticmethod
    def get_snake(snake_id, snakes):
        return [snake for snake in snakes if snake["id"] == snake_id][0]

    @staticmethod
    def neighbors(node, board):
        directions = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        result = []
        for direction in directions:
            neighbor = (node[0] + direction[0], node[1] + direction[1])
            if board.has_node(neighbor):
                result.append(neighbor)
        return result

    @staticmethod
    def next_direction(current_node, next_node):
        label = "up"
        directions = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        for l in directions:
            r = (
                current_node[0] + directions[l][0],
                current_node[1] + directions[l][1]
            )
            print(r, r == next_node, next_node)
            if r == next_node:
                label = l
                break
        return label

    @staticmethod
    def translate(data):
        print(data)
        for i in range(0, len(data["snakes"])):
            data["snakes"][i]["coords"] = map(lambda l: [l[1], l[0]], data["snakes"][i]["coords"])
        data["food"] = map(lambda l: [l[1], l[0]], data["food"])
        print(data)
        return data
