import cProfile
import time
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from itertools import permutations

DIMENSION_MAX = 6
QUEEN_AND_JESTER = False
BOARD_SIZE = 8
PROFILING = True

area_table: dict[int, tuple[int, int, int]] = {
    1: (8, 4, 8),
    2: (36, 20, 20),
    3: (120, 60, 40),
    4: (330, 170, 70),
    5: (792, 396, 112),
    6: (1716, 868, 168),
    7: (3432, 1716, 240),
    8: (6435, 3235, 330),
    9: (11440, 5720, 440),
    10: (19448, 9752, 572),
    11: (31824, 15912, 728),
    12: (50388, 25236, 910),
    13: (77520, 38760, 1120),
    14: (116280, 58200, 1360),
    15: (170544, 85272, 1632),
    16: (245157, 122661, 1938),
    17: (346104, 173052, 2280),
    18: (480700, 240460, 2660),
    19: (657800, 328900, 3080),
    20: (888030, 444158, 3542),
}


def give_sign(move: list[int], index: int) -> list[tuple[int, ...]]:
    if index == len(move):
        return [tuple(move)]
    moves: list[tuple[int, ...]] = []
    move_copy = move.copy()
    moves.extend(give_sign(move_copy, index + 1))
    move_copy = move.copy()
    if move_copy[index] != 0:
        move_copy[index] = -1 * move_copy[index]
        moves.extend(give_sign(move_copy, index + 1))
    return moves


def make_leapers_moves(moves_base: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    moves: list[tuple[int, ...]] = []
    for move_unsigned in {move for move in permutations(moves_base, len(moves_base))}:
        move_signed = list(move_unsigned)
        moves.extend(give_sign(move_signed, 0))
    return tuple(moves)


def make_sliders_moves(
    moves_base: tuple[int, ...],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    moves_by_directions: list[tuple[tuple[int, ...], ...]] = []
    for move_unsigned in {move for move in permutations(moves_base, len(moves_base))}:
        for direction in give_sign(list(move_unsigned), 0):
            moves: list[tuple[int, ...]] = []
            for step_size in range(1, BOARD_SIZE):
                moves.append(tuple([step_size * a for a in direction]))
            moves_by_directions.append(tuple(moves))
    return tuple(moves_by_directions)


def calculate_leapers_mobility_and_coverage(
    moves: tuple[tuple[int, ...], ...], dimensions: int, is_jester: bool = False
) -> int:
    if not moves:
        return 0
    origin = tuple(0 for _ in range(dimensions))
    steps = 0
    stack = {origin}
    investigated: set[tuple[int, ...]] = set()
    if is_jester:
        area_expected = area_table[dimensions][0]
    else:
        area_expected = area_table[dimensions][(sum(moves[0]) + 1) % 2]
    while True:
        steps += 1
        new_stack: set[tuple[int, ...]] = set()
        for coord in stack:
            if coord in investigated:
                continue
            for move in moves:
                new_coord = list(coord)
                new_coord[0] += move[0]
                current_value = new_coord[0]
                if current_value < 0 or current_value >= BOARD_SIZE:
                    continue
                not_valid = False
                for i in range(1, dimensions):
                    new_coord[i] += move[i]
                    current_value = new_coord[i]
                    if current_value < 0 or current_value >= BOARD_SIZE:
                        not_valid = True
                        break
                if not_valid:
                    continue
                new_coord.sort()
                coord_tuple = tuple(new_coord)
                if coord_tuple not in investigated:
                    new_stack.add(coord_tuple)
            investigated.add(coord)
        if investigated.__len__() >= area_expected:
            return steps - 1
        stack = new_stack


def calculate_sliders_mobility_and_coverage(
    moves_by_directions: tuple[tuple[tuple[int, ...], ...], ...],
    dimensions: int,
    is_queen: bool = False,
) -> int:
    origin = tuple(0 for _ in range(dimensions))
    steps = 0
    stack = {origin}
    investigated: set[tuple[int, ...]] = set()
    base_move = moves_by_directions[0][0]
    if is_queen:
        area_expected = area_table[dimensions][0]
    elif 0 not in base_move:
        area_expected = area_table[dimensions][2]
    else:
        area_expected = area_table[dimensions][(sum(base_move) + 1) % 2]
    while True:
        steps += 1
        new_stack: set[tuple[int, ...]] = set()
        for coord in stack:
            if coord in investigated:
                continue
            for direction in moves_by_directions:
                for move in direction:
                    new_coord = list(coord)
                    new_coord[0] += move[0]
                    current_value = new_coord[0]
                    if current_value < 0 or current_value >= BOARD_SIZE:
                        break
                    not_valid = False
                    for i in range(1, dimensions):
                        new_coord[i] += move[i]
                        current_value = new_coord[i]
                        if current_value < 0 or current_value >= BOARD_SIZE:
                            not_valid = True
                            break
                    if not_valid:
                        break
                    new_coord.sort()
                    coord_tuple = tuple(new_coord)
                    if coord_tuple not in investigated:
                        new_stack.add(coord_tuple)
            investigated.add(coord)
        if investigated.__len__() == area_expected:
            return steps - 1
        stack = new_stack


def calculate_leaper(
    dimension: int, piece_dimension: int, piece_index: int
) -> tuple[tuple[int, ...], ...]:
    base_moves = tuple(
        (dimension - piece_dimension) * [0]
        + (piece_dimension - piece_index) * [1]
        + piece_index * [2]
    )
    moves = make_leapers_moves(base_moves)
    mobility = calculate_leapers_mobility_and_coverage(moves, dimension)
    print(f"{base_moves} | {mobility}")
    return moves


def calculate_sliders(
    dimension: int, piece_dimension: int
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    base_moves = tuple((dimension - piece_dimension) * [0] + (piece_dimension) * [1])
    moves = make_sliders_moves(base_moves)
    mobility = calculate_sliders_mobility_and_coverage(moves, dimension)
    print(f"{base_moves} | {mobility}")
    return moves


def main() -> None:
    for dimension in range(1, DIMENSION_MAX + 1):
        begin = time.time()
        queen_moves: list[tuple[tuple[int, ...], ...]] = []
        jester_moves: list[tuple[int, ...]] = []
        if PROFILING:
            for piece_dimension in range(1, dimension + 1):
                queen_moves.extend(calculate_sliders(dimension, piece_dimension))
            if dimension > 1:
                for piece_dimension in range(1, dimension + 1):
                    for index in range(1, piece_dimension):
                        jester_moves.extend(
                            calculate_leaper(dimension, piece_dimension, index)
                        )
        else:
            with ProcessPoolExecutor(max_workers=12) as pool:
                futures_slider = [
                    pool.submit(calculate_sliders, dimension, piece_dimension)
                    for piece_dimension in range(1, dimension + 1)
                ]
                for future_slider in as_completed(futures_slider):
                    queen_moves.extend(future_slider.result())
                if dimension > 1:
                    futures_leapers: list[Future[tuple[tuple[int, ...], ...]]] = []
                    for piece_dimension in range(dimension + 1):
                        futures_leapers.extend(
                            [
                                pool.submit(
                                    calculate_leaper, dimension, piece_dimension, index
                                )
                                for index in range(1, piece_dimension)
                            ]
                        )
                    for future_leaper in as_completed(futures_leapers):
                        jester_moves.extend(future_leaper.result())
        if QUEEN_AND_JESTER:
            mobility = calculate_sliders_mobility_and_coverage(
                tuple(queen_moves), dimension, is_queen=True
            )
            print(f"Queen | {mobility}")
            mobility = calculate_leapers_mobility_and_coverage(
                tuple(jester_moves), dimension, is_jester=True
            )
            print(f"Jester | {mobility}")
        print(f"Dimension Total : {time.time() - begin}")


if __name__ == "__main__":
    begin = time.time()
    if PROFILING:
        cProfile.run("main()")
    else:
        main()
    print(f"Total : {time.time() - begin}")
