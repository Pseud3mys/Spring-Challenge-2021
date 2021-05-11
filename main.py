import sys
import time
from enum import Enum
import random

TURN = -1
MY_MINI_TURN = -1
LAST_TURN = 23

# cell_num: cell_obj
CELLS = []

# turn: cells_obj
SHADOW_CELLS = {}

# action_array:
WAIT = "WAIT"
SEED = "SEED"
GROW = "GROW"
COMPLETE = "COMPLETE"
ACTIONS = {WAIT: [], SEED: [], GROW: [], COMPLETE: []}
BEST_ACTION = {WAIT: None, SEED: None, GROW: None, COMPLETE: None}


_ACTION_SEND = False
LAST_ACTION = None
TURN_COST_LIMIT = 99


def debug(*args):
    out = ""
    for arg in args:
        out += str(arg) + " "
    print(out, file=sys.stderr, flush=True)


"""basic game class"""


class Game:
    def __init__(self):
        self.turn = 0
        self.nutrients = 0

        self.trees = []
        self.possible_actions = []
        self.my_sun = 0
        self.my_score = 0
        self.opponent_sun = 0
        self.opponent_score = 0
        self.opponent_is_waiting = 0

        self.levels_trees = [[], [], [], []]
        self.all_level3_tree = []

    def new_turn(self):
        global ACTIONS
        self.levels_trees = [[], [], [], []]
        self.all_level3_tree = []
        self.trees = []
        self.possible_actions = []
        ACTIONS = {WAIT: [], SEED: [], GROW: [], COMPLETE: []}
        # le tree des cells changent aussi !
        for c_obj in CELLS:
            c_obj.Tree = None


class Cell:
    def __init__(self, cell_index, richness, neighbors):
        self.num = cell_index
        self.richness = richness
        self.richness_bonus = (richness - 1) * 2
        self.neighbors = neighbors

        # tree object or none
        self.Tree = None


class Tree:
    def __init__(self, cell_obj, size, is_mine, is_dormant):
        self.cell = cell_obj
        self.size = size
        self.is_mine = is_mine
        self.is_dormant = is_dormant
        # array of Action
        self.actions = []


class ActionSEED:
    def __init__(self, target_cell_id, origin_cell_id):
        self.type = SEED
        self.target_cell = CELLS[target_cell_id]
        self.origin_cell = CELLS[origin_cell_id]

        self.sun_cost = len(game.levels_trees[0])
        self.sun_earn = 0
        self.best_neighbor = richest_neighbour(self.target_cell)

        self.points_earn = 0
        self.row_sun_day = successive_sun_day(self.target_cell)
        self.mean_day_sun = mean_sun_day(self.target_cell, )

        self.origin_cell.Tree.actions.append(self)
        ACTIONS[SEED].append(self)

    def __str__(self):
        out = SEED + " " + str(self.origin_cell.num) + " " + str(self.target_cell.num) + " | "
        out += str(self.sun_earn) + "-" + str(self.sun_cost)
        return out


class ActionGROW:
    def __init__(self, target_cell_id):
        self.type = GROW
        self.target_cell = CELLS[target_cell_id]
        self.Tree_target = self.target_cell.Tree

        self.grow_size = self.target_cell.Tree.size + 1
        self.sun_cost = (2 ** self.grow_size - 1) + len(game.levels_trees[self.grow_size])
        self.sun_earn = self.target_cell.Tree.size * (successive_sun_day(self.target_cell) >= 1)

        self.row_sun_day = successive_sun_day(self.target_cell)
        self.mean_day_sun = mean_sun_day(self.target_cell)

        self.target_cell.Tree.actions.append(self)
        ACTIONS[GROW].append(self)

    def __str__(self):
        out = GROW + " " + str(self.target_cell.num) + " | "
        out += "" + str(self.sun_earn) + "-" + str(self.sun_cost)
        return out


class ActionCOMPLETE:
    def __init__(self, target_cell_id):
        self.type = COMPLETE
        self.target_cell = CELLS[target_cell_id]
        self.Tree_target = self.target_cell.Tree

        self.sun_cost = 4
        self.sun_earn = 0
        self.points_earn = (self.target_cell.richness - 1) * 2 + game.nutrients

        self.row_sun_day = successive_sun_day(self.target_cell)

        self.target_cell.Tree.actions.append(self)
        ACTIONS[COMPLETE].append(self)

    def __str__(self):
        out = COMPLETE + " " + str(self.target_cell.num) + " | "
        out += "" + str(self.sun_earn) + "-" + str(self.sun_cost) + ", P:" + str(self.points_earn)
        return out


class ActionWAIT:
    def __init__(self):
        self.type = WAIT
        self.sun_cost = 0
        self.sun_earn = 0
        self.points_earn = 0
        ACTIONS[WAIT].append(self)
        BEST_ACTION[WAIT] = self

    def __str__(self):
        return "WAIT turn:" + str(TURN)


""" ---------------------------------------------------------- """


def play_BEST_from_type(action_type, min_point=-999):
    global _ACTION_SEND, LAST_ACTION, TURN_COST_LIMIT
    if _ACTION_SEND:
        return

    if BEST_ACTION[action_type] is not None:
        if BEST_ACTION[action_type].sun_cost <= TURN_COST_LIMIT:
            print(BEST_ACTION[action_type])
            debug("PLAYED (type): ", BEST_ACTION[action_type])
            LAST_ACTION = BEST_ACTION[action_type]
            TURN_COST_LIMIT -= BEST_ACTION[action_type].sun_cost
            _ACTION_SEND = True


def play_action(action):
    global _ACTION_SEND, LAST_ACTION, TURN_COST_LIMIT
    if _ACTION_SEND:
        return
    if type(action) == str:
        print(action)
        debug("PLAYED (str): ", action)
        _ACTION_SEND = True
    elif action is not None:
        if action.sun_cost <= TURN_COST_LIMIT:
            print(action)
            debug("PLAYED (a): ", action)
            LAST_ACTION = action
            TURN_COST_LIMIT -= action.sun_cost
            _ACTION_SEND = True


def ombre_by_OneTree(cell, tree_size, delta_turn):
    """
    :param Cell cell:
    :param int tree_size:
    :param int delta_turn:
    :return : array of cell covered by the "Tree" shadows
    """
    _cells_ombre = []
    ombre = (TURN + delta_turn) % 6
    for i in range(tree_size):
        if i == 0:
            ombre_cell = cell.neighbors[ombre]
        else:
            ombre_cell = _cells_ombre[i - 1].neighbors[ombre]

        if ombre_cell == None:
            break
        else:
            _cells_ombre.append(ombre_cell)
    return _cells_ombre


# nombre de jour de soleil pour la case pour le nombre de tour saisit (au total)
def mean_sun_day(cell, num_turn=6, start_turn=1, simulate_grow=0):
    """
    :param Cell cell:
    :param int num_turn:
    :param float simulate_grow:
    :return:
    """
    num = num_turn

    for ombre in range(TURN + start_turn, TURN + num_turn + start_turn):
        cell_obj = cell
        for dist in range(1, 1 + 3):
            # on remonte l'ombre
            cell_obj = cell_obj.neighbors[(ombre + 3) % 6]
            if cell_obj is None:
                break
            if cell_obj.Tree:
                size = min(3, cell_obj.Tree.size + ombre * int(random.random() < simulate_grow))
                if size >= dist:
                    num -= 1
                    # next ombre:
                    break
    return num


# pareil mais compte le nombre de jours consécutifs (sans comter tour actuel)
def successive_sun_day(cell, simulate_grow=0, start_turn=None):
    if not start_turn:
        start_turn = TURN + 1
    s = 0
    for ombre in range(6):
        cell_obj = cell
        for dist in range(1, 1 + 3):
            # on remonte l'ombre
            cell_obj = cell_obj.neighbors[(start_turn + ombre + 3) % 6]
            if cell_obj is None:
                break
            if cell_obj.Tree:
                size = min(3, cell_obj.Tree.size + int(random.random() < simulate_grow))
                if size >= dist:
                    return s
        s += 1
    return s


def successive_NOTsun_day(cell, simulate_grow=0):
    beurk_day = 0
    out = 0
    for _ in range(6):
        out = successive_sun_day(cell, simulate_grow, TURN+beurk_day+1)
        if out == 0:
            beurk_day += 1
    return beurk_day


def cells_ombre(delta_turn, simulate_grow=0):
    """
    :param int delta_turn:
    :return: List[Cell], list of cell_object in the shadow for the turn specified
    """
    ombres_cells = []
    for tree in game.trees:
        size = tree.size + delta_turn * int(random.random() < simulate_grow)
        if size == 0:
            continue
        ombres_cells += ombre_by_OneTree(tree.cell, size, (TURN + delta_turn) % 6)
    return list(set(ombres_cells))


def richest_neighbour(cell_obj, cell_range=1):
    """
    :param Cell cell_obj:
    :param int cell_range:
    :return: Cell, the richest neighbors at "cell_range" around the cell_obj
    """
    voisins = cell_obj.neighbors
    max_rich = -1
    winner = None
    for neigh in voisins:
        # erreur si le voisin existe pas
        if neigh is None:
            continue
        rich = neigh.richness
        if rich > max_rich:
            max_rich = rich
            winner = neigh
    for _ in range(cell_range - 1):
        return richest_neighbour(winner, cell_range - 1)
    return winner


def income(delta_turn):
    _sum = 0
    shadow = cells_ombre(delta_turn)
    for size in range(0, 3 + 1):
        for tree in game.levels_trees[size]:
            if tree not in shadow:
                _sum += size
    return _sum


number_of_cells = int(input())
game = Game()
for i in range(number_of_cells):
    neigh = [i for i in range(6)]
    cell_index, richness, neigh[0], neigh[1], neigh[2], neigh[3], neigh[4], neigh[5] = [int(j) for j in input().split()]
    CELLS.append(Cell(cell_index, richness, neigh))

# neighbors are now cell object or None
for cell_index in range(number_of_cells):
    obj_neigh = []
    for n in CELLS[cell_index].neighbors:
        if n == -1:
            obj_neigh.append(None)
        else:
            obj_neigh.append(CELLS[n])
    CELLS[cell_index].neighbors = obj_neigh

while True:
    start = time.time()
    game.new_turn()  # très important !
    TURN = int(input())
    TURN_COST_LIMIT = 99
    MY_MINI_TURN += 1
    debug("MY_MINI_TURN:", MY_MINI_TURN)
    _ACTION_SEND = False
    nutrients = int(input())
    game.nutrients = nutrients
    sun, score = [int(i) for i in input().split()]
    game.my_sun = sun
    game.my_score = score
    opp_sun, opp_score, opp_is_waiting = [int(i) for i in input().split()]
    game.opponent_sun = opp_sun
    game.opponent_score = opp_score
    game.opponent_is_waiting = opp_is_waiting

    number_of_trees = int(input())
    for i in range(number_of_trees):
        inputs = input().split()
        cell_obj = CELLS[int(inputs[0])]
        size = int(inputs[1])
        is_mine = inputs[2] != "0"
        is_dormant = inputs[3] != "0"
        tree_obj = Tree(cell_obj, size, is_mine, is_dormant)
        cell_obj.Tree = tree_obj
        game.trees.append(tree_obj)
        if tree_obj.size == 3:
            game.all_level3_tree.append(tree_obj)
        if tree_obj.is_mine:
            game.levels_trees[size].append(tree_obj)
    number_of_possible_actions = int(input())

    BEST_ACTION = {WAIT: None, SEED: None, GROW: None, COMPLETE: None}
    for i in range(number_of_possible_actions):
        split = input().split(' ')
        if split[0] == WAIT:
            ActionWAIT()
        elif split[0] == SEED:
            a = ActionSEED(int(split[2]), int(split[1]))
        elif split[0] == GROW:
            ActionGROW(int(split[1]))
        elif split[0] == COMPLETE:
            ActionCOMPLETE(int(split[1]))
    for t, actions in ACTIONS.items():
        if t != SEED:
            for a in actions:
                debug(a)

    # best SEED action
    if ACTIONS[SEED]:
        SEED_a = []
        ACTIONS[SEED].sort(key=lambda a: mean_sun_day(a.target_cell), reverse=True)
        b = mean_sun_day(ACTIONS[SEED][0].target_cell)
        for a in ACTIONS[SEED]:
            if a.origin_cell.Tree.size == 1:  # les arbres de taille 1 ne plante pas
                continue

            if mean_sun_day(a.target_cell) >= min(b, 6):
                SEED_a.append(a)
            else:
                break
        SEED_a.sort(key=lambda a: a.target_cell.richness, reverse=True)
        if SEED_a:
            BEST_ACTION[SEED] = SEED_a[0]

    # best GROW action:
    if ACTIONS[GROW]:
        ACTIONS[GROW].sort(key=lambda a: min(2, a.row_sun_day) * a.grow_size, reverse=True)
        BEST_ACTION[GROW] = ACTIONS[GROW][0]
        for a in ACTIONS[GROW]:
            if a.grow_size == 3:
                out = successive_NOTsun_day(a.target_cell)
                if out >= 2:
                    BEST_ACTION[GROW] = ACTIONS[GROW][0]
                    break

    # best COMPLETE action
    if ACTIONS[COMPLETE]:
        if TURN == LAST_TURN or TURN >= LAST_TURN-5:
            ACTIONS[COMPLETE].sort(key=lambda a: a.points_earn, reverse=True)
            # si on gagne moins de 1 point c'est mieux de juste garder les soleils (qui sont des points à la fin)
            if ACTIONS[COMPLETE][0].points_earn >= 1:
                BEST_ACTION[COMPLETE] = ACTIONS[COMPLETE][0]
        else:
            ACTIONS[COMPLETE].sort(key=lambda a: successive_NOTsun_day(a.target_cell), reverse=True)
            choose = []
            b = successive_NOTsun_day(ACTIONS[COMPLETE][0].target_cell)
            # au moins 2 jour sans soleil pour le vendre
            if b >= 1:
                for a in ACTIONS[COMPLETE]:
                    if successive_NOTsun_day(ACTIONS[COMPLETE][0].target_cell) >= b:
                        choose.append(a)
                choose.sort(key=lambda a: a.points_earn, reverse=True)
                BEST_ACTION[COMPLETE] = choose[0]

    # the first 2 actions:
    if MY_MINI_TURN == 0:
        play_action("WAIT")

    if MY_MINI_TURN == 1:
        ACTIONS[GROW].sort(key=lambda a: richest_neighbour(a.target_cell, 2).richness, reverse=True)
        play_action(ACTIONS[GROW][0])

    if TURN == LAST_TURN:
        play_BEST_from_type(COMPLETE)
        # sinon on garde les soleils ca fait tjr ca de gagner en point
        play_BEST_from_type(WAIT)

    if TURN >= LAST_TURN - 5:
        if game.my_sun < 4 * len(game.levels_trees[3]):
            play_BEST_from_type(WAIT)
        else:
            TURN_COST_LIMIT = game.my_sun - 4 * len(game.levels_trees[3])
            play_BEST_from_type(GROW)

    if LAST_ACTION:
        if LAST_ACTION.type == COMPLETE and len(game.levels_trees[0]) < 2:
            # on essaye de replanter l'arbre qu"on a vendu
            play_BEST_from_type(SEED)

    if len(game.levels_trees[3]) > 2:
        play_BEST_from_type(COMPLETE)

    # logique la plus basique:
    if len(game.levels_trees[0]) > 0 or len(game.levels_trees[1]) >= 2:
        play_BEST_from_type(GROW)
    else:
        play_BEST_from_type(SEED)


    play_action("WAIT SLEEPING !")
    debug("FINAL turn %s:"%TURN, int((time.time() - start) * 1000), "/ 100")
