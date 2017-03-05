import sys
from pygraph.algorithms.minmax import heuristic_search
from pygraph.classes.graph import graph
from pygraph.algorithms.heuristics.chow import chow
from pygraph.classes.exceptions import NodeUnreachable


class Game(object):
    snake = {}
    turn = 0
    lower_tolerance = 30

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
            self.board = self.make_board(data["snakes"])
            targets = [tuple(node) for node in data["food"]]

            # PRIORITIES
            # DON'T GET KILLED
            # DON'T TRAP YOURSELF

            # 1. Distances
            paths, distances = self.a_star(targets)

            # 1.1 Simulate another iteration. Is ther any food node close to another food node?
            # 1.2 Too eat more: detect food inside other food's path
            # maybe later

            # 2. Risk averse
            risks = dict(map(lambda f: (f, 1), targets))
            if self.snake["health_points"] >= self.lower_tolerance:
                opponents = [snake for snake in data["snakes"] if snake["id"] != self.snake["id"]]
                if opponents:
                    try:
                        risks = self.risk(paths, opponents)
                        maximum = float(max(risks.values())) + 1  # we don't want to multiply by 0
                        risks = {k: (maximum - v)/maximum for k, v in risks.items()}
                    except KeyError as e:
                        print("UNKNOWN ERROR: %s" % e)
                        risks = dict(map(lambda f: (f, 1), targets))
                        pass

            # 3. Probability of kill
            # Useful to break ties
            kills = dict(map(lambda f: (f, 1), targets))

            # 4. Selection
            try:
                next_move = self.select(targets, paths, distances, risks, kills)
            except KeyError as e:
                print("UNKNOWN ERROR: %s" % e)
                next_move = self.next_direction(tuple(self.snake["coords"][0]), paths[paths.keys()[0]][0])
                pass
        else:
            print("I'm dead. Turns played: %d" % self.turn)
        return next_move

    def make_board(self, snakes):
        return self._board(self.find_obstacles(snakes))

    def make_board_with_heads(self, snakes):
        return self._board(self.find_obstacles(snakes, False))

    def _board(self, obstacles):
        board = graph()
        for i in range(0, self.height):
            for j in range(0, self.width):
                if (i, j) not in obstacles:
                    board.add_node((i, j))
        for node in board.nodes():
            for neighbor in self.neighbors(node, board):
                if not board.has_edge((node, neighbor)):
                    board.add_edge((node, neighbor))
        return board

    def find_obstacles(self, snakes, include_heads=True):
        obstacles = set()
        for snake in snakes:
            _id = snake["id"]
            _coordinates = snake["coords"]
            # all snakes' bodies, unless it is our snake, and its head == its body
            obstacles.update(
                [
                    tuple(position) for position in _coordinates[1:]
                    # don't add our snake's body if body == head
                    if not (_id == self.snake["id"] and _coordinates[0] == _coordinates[1])
                    # when adding heads too, don't add the body if body == head
                    and not (not include_heads and _coordinates[0] == _coordinates[1])
                ]
            )
            # ignore shorter snakes' heads
            # a snake is not shorter than itself
            if include_heads:
                shorter = len(snake["coords"]) < len(self.snake["coords"])  # is their snake shorter?
                if not shorter and _id != self.snake["id"]:
                    obstacles.add(tuple(snake["coords"][0]))
        return obstacles

    def a_star(self, targets):
        paths = {}
        distances = {}
        heuristic = chow(*targets)
        heuristic.optimize(self.board)
        for target in targets:
            try:
                paths[target] = heuristic_search(self.board, tuple(self.snake["coords"][0]), target, heuristic)
                paths[target] = paths[target][1:]  # remove first (current position)
                distances[target] = len(paths[target])
            except NodeUnreachable as e:
                distances[target] = sys.maxint
                print("UNREACHABLE: %s" % e)
                pass
        return paths, distances

    def risk(self, paths, snakes):
        # for each point in a path, calculate distance to other snakes
        # for each path, the score is the sum of all distances. greater is better
        # return {path1: score, path2: score, ...}
        board_with_heads = self.make_board_with_heads(snakes)
        _heuristic = chow(*paths.keys())
        _heuristic.optimize(board_with_heads)
        return dict([(food, self._risk(_heuristic, board_with_heads, paths[food], snakes)) for food in paths.keys()])

    def _risk(self, _heuristic, board_with_heads, path, snakes):
        score = 0
        for node in path:
            for snake in snakes:
                opponent_path = heuristic_search(
                    board_with_heads, tuple(snake["coords"][0]), node, _heuristic)
                # distance between the opponent's head and path point
                score += len(opponent_path)
        return score

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
            if r == next_node:
                label = l
                break
        return label

    @staticmethod
    def translate(data):
        for i in range(0, len(data["snakes"])):
            data["snakes"][i]["coords"] = map(lambda l: [l[1], l[0]], data["snakes"][i]["coords"])
        data["food"] = map(lambda l: [l[1], l[0]], data["food"])
        return data

    def select(self, targets, paths, distances, risks, kills):
        total = float(reduce(lambda a, b: a + b, distances.values()))
        scores = {}
        for f in targets:
            scores[f] = (distances[f] / total) * risks[f] * kills[f]
        best = min(scores, key=scores.get)
        return self.next_direction(tuple(self.snake["coords"][0]), paths[best][0])
