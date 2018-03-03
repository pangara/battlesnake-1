import sys
from pygraph.algorithms.minmax import heuristic_search
from pygraph.classes.graph import graph
from pygraph.algorithms.heuristics.chow import chow
from pygraph.classes.exceptions import NodeUnreachable


class Game(object):
    snake = {}
    turn = 0
    lower_tolerance = 10

    def __init__(self, data):
        self.game = data['id']
        self.height = data['height']
        self.width = data['width']

    def move(self, data):
        next_move = "up"
        if not self.is_dead(data["you"]["id"], data["snakes"]["data"]):
            data = self.translate(data);
            self.snake = self.get_snake(data["you"]["id"], data["snakes"]["data"])
            self.snakes = data["snakes"]["data"]
            self.turn = data["turn"]
            self.height = data["height"]
            self.width = data["width"]
            self.board = self.make_board(data["snakes"]["data"])
            targets = [tuple(node) for node in data["food"]]

            if len(targets) < 5:
                self.lower_tolerance = 90
            elif len(targets) < 10:
                self.lower_tolerance = 65
            elif len(targets) < 15:
                self.lower_tolerance = 40
            elif len(targets) < 20:
                self.lower_tolerance = 30
            elif len(targets) < 25:
                self.lower_tolerance = 20
            else:
                self.lower_tolerance = 10

            opponents = [snake for snake in data["snakes"]["data"] if snake["id"] != self.snake["id"]]

            # IF NOT EATING
            # list shorter snakes
            # list their possible moves
            # include those points as targets
            self.lower_tolerance = 60
            if opponents and self.snake["health"] >= self.lower_tolerance:
                shorter_snakes = [snake for snake in opponents if len(snake["coords"]) < len(self.snake["coords"])-1]
                if not shorter_snakes:
                    self.lower_tolerance = 100
                for snake in shorter_snakes:
                    head = snake["coords"][0]
                    neighbors = self.neighbors(head, self.board)
                    if snake["coords"][1] in neighbors:
                        neighbors.remove(snake["coords"][1]) # remove the one in the body
                    targets.extend(neighbors)

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
            if self.snake["health"] >= self.lower_tolerance:
                if opponents:
                    try:
                        risks = self.risk(paths, opponents)
                        if risks.values():
                            maximum = float(max(risks.values())) + 1  # we don't want to multiply by 0
                        else:
                            maximum = 1
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

        # Key errors here - see if the next move is a valid one
        # else go a safe direction
        return next_move

    def make_board(self, snakes):
        return self._board(self.find_obstacles(snakes))

    def make_board_with_heads(self, snakes):
        return self._board(self.find_obstacles(snakes, False))

    def _board(self, obstacles):
        # include possible moves for snakes that are longer or the same length
        # for snake in self.snakes:
        #     shorter = len(snake["coords"]) < len(self.snake["coords"])
        #     if not shorter:
        #         neighbors = self.neighbors_from_grid(snake["coords"][0])
        #         if snake["coords"][1] in neighbors:
        #             neighbors.remove(snake["coords"][1])
        #         print(neighbors)
        #         obstacles.update(neighbors)
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
                shorter = len(snake["coords"]) < len(self.snake["coords"])
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
            except Exception as e:
                distances[target] = sys.maxint
                print("ERROR %s" % e)
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
    def is_dead(snake_id, snakes):
        filtered = filter(lambda snake: snake["id"] == snake_id, snakes)
        return len(filtered) == 0

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

    def neighbors_from_grid(self, node):
        directions = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        result = []
        for direction in directions:
            neighbor = (node[0] + direction[0], node[1] + direction[1])
            if neighbor[0] >= 0 and neighbor[0] < self.width and neighbor[1] >= 0 and neighbor[1] < self.height:
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
        for i in range(0, len(data["snakes"]["data"])):
            data["snakes"]["data"][i]["coords"] = map(lambda l: [l[1], l[0]], Game.snake_coords(data["snakes"]["data"][i]))
        data["food"] = map(lambda l: [l[1], l[0]], Game.food_coords(data["food"]))
        return data

    def select(self, targets, paths, distances, risks, kills):
        total = float(reduce(lambda a, b: a + b, distances.values()))
        scores = {}
        for f in targets:
            scores[f] = (distances[f] / total) * risks[f] * kills[f]
        best = min(scores, key=scores.get)
        return self.next_direction(tuple(self.snake["coords"][0]), paths[best][0])

    @staticmethod
    def snake_coords(snake):
        return map(lambda item: [item["x"], item["y"]], snake["body"]["data"])

    @staticmethod
    def food_coords(food_list):
        return map(lambda item: [item["x"], item["y"]], food_list["data"])

    @staticmethod
    def is_in_board(x, y, width, height):
        if x < 0 or x > width-1 or y < 0 or y > height-1:
            return False
        return True


