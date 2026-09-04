import cProfile
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from fractions import Fraction
from itertools import permutations

BOARD_SIZE = 8
PROFILING = True

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

def count_symmetry(coords:set[tuple[int, ...]]) -> int:
    total = 0
    for coord in coords:
        total += len(set(permutations(coord)))
    return total

def calculate_leapers_mobility_and_coverage(
    moves: tuple[tuple[int, ...], ...], dimensions: int
) -> tuple[int, Fraction]:
    origin = tuple([0 for _ in range(dimensions)])
    steps = 0
    stack = {origin}
    investigated: set[tuple[int, ...]] = set()
    while True:
        start_len = len(investigated)
        steps += 1
        new_stack: set[tuple[int, ...]] = set()
        for coord in stack:
            if coord in investigated:
                continue
            for move in moves:
                new_coord = list(coord)
                not_valid = False
                needs_sorting = False
                for i, n in enumerate(move):
                    new_coord[i] += n
                    if new_coord[i] < 0 or new_coord[i] >= BOARD_SIZE:
                        not_valid = True
                        break
                    if i > 0 and new_coord[i] < new_coord[i - 1]:
                        needs_sorting = True
                if not_valid:
                    continue
                if needs_sorting:
                    new_coord.sort()
                coord_tuple = tuple(new_coord)
                if coord_tuple not in investigated:
                    new_stack.add(coord_tuple)
            investigated.add(coord)
        if len(investigated) == start_len:
            return steps - 2, count_symmetry(
                investigated
            ) / BOARD_SIZE**dimensions * 100
        stack = new_stack


def calculate_sliders_mobility_and_coverage(
    moves_by_directions: tuple[tuple[tuple[int, ...], ...], ...], dimensions: int
) -> tuple[int, Fraction]:
    origin = tuple([0 for _ in range(dimensions)])
    steps = 0
    stack = {origin}
    investigated: set[tuple[int, ...]] = set()
    while True:
        start_len = len(investigated)
        steps += 1
        new_stack: set[tuple[int, ...]] = set()
        for coord in stack:
            if coord in investigated:
                continue
            for direction in moves_by_directions:
                for move in direction:
                    new_coord = list(coord)
                    not_valid = False
                    needs_sorting = False
                    for i, n in enumerate(move):
                        new_coord[i] += n
                        if new_coord[i] < 0 or new_coord[i] >= BOARD_SIZE:
                            not_valid = True
                            break
                        if i > 0 and new_coord[i] < new_coord[i - 1]:
                            needs_sorting = True
                    if not_valid:
                        break
                    if needs_sorting:
                        new_coord.sort()
                    coord_tuple = tuple(new_coord)
                    if coord_tuple not in investigated:
                        new_stack.add(coord_tuple)
            investigated.add(coord)
        if len(investigated) == start_len:
            return steps - 2, count_symmetry(
                investigated
            ) / BOARD_SIZE**dimensions * 100
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
    mobility, coverage = calculate_leapers_mobility_and_coverage(moves, dimension)
    print(f"{base_moves} | {mobility} | {coverage}%")
    return moves


def calculate_sliders(
    dimension: int, piece_dimension: int
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    base_moves = tuple((dimension - piece_dimension) * [0] + (piece_dimension) * [1])
    moves = make_sliders_moves(base_moves)
    mobility, coverage = calculate_sliders_mobility_and_coverage(moves, dimension)
    print(f"{base_moves} | {mobility} | {coverage}%")
    return moves


def main() -> None:
    dimensions = 6
    for dimension in range(1, dimensions + 1):
        queen_moves: list[tuple[tuple[int, ...], ...]] = []
        jester_moves: list[tuple[int, ...]] = []
        if PROFILING:
            for piece_dimension in range(1, dimension):
                queen_moves.extend(calculate_sliders(dimension, piece_dimension))
            for piece_dimension in range(1, dimension):
                for index in range(1, piece_dimension):
                    jester_moves.extend(
                        calculate_leaper(dimension, piece_dimension, index)
                    )
        else:
            with ProcessPoolExecutor(max_workers=12) as pool:
                futures_slider = [
                    pool.submit(calculate_sliders, dimension, piece_dimension)
                    for piece_dimension in range(1, dimension)
                ]
                for future_slider in as_completed(futures_slider):
                    queen_moves.extend(future_slider.result())
                futures_leapers: list[Future[tuple[tuple[int,...],...]]] = []
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
        mobility, coverage = calculate_sliders_mobility_and_coverage(
            tuple(queen_moves), dimension
        )
        print(f"Queen | {mobility} | {coverage}%")
        mobility, coverage = calculate_leapers_mobility_and_coverage(
            tuple(jester_moves), dimension
        )
        print(f"Jester | {mobility} | {coverage}%")


if __name__ == "__main__":
    if PROFILING:
        cProfile.run("main()")
    else:
        main()
