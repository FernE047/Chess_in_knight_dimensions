from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
from itertools import permutations

BOARD_SIZE = 8


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
                if needs_sorting:
                    new_coord.sort()
                if not_valid:
                    continue
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
                    if needs_sorting:
                        new_coord.sort()
                    if not_valid:
                        break
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


def calculate_all_leapers(dimensions: int) -> None:
    for dimension in range(2, dimensions + 1):
        jester_moves: list[tuple[int, ...]] = []
        with ProcessPoolExecutor(max_workers=12) as pool:
            futures = []
            for piece_dimension in range(dimension + 1):
                futures.extend([
                    pool.submit(calculate_leaper, dimension, piece_dimension, index)
                    for index in range(1, piece_dimension)
                ])
            for future in as_completed(futures):
                jester_moves.extend(future.result())
        mobility, coverage = calculate_leapers_mobility_and_coverage(
            tuple(jester_moves), dimension
        )
        print(f"Jester | {mobility} | {coverage}%")


def calculate_sliders(
    dimension: int, piece_dimension: int
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    base_moves = tuple((dimension - piece_dimension) * [0] + (piece_dimension) * [1])
    moves = make_sliders_moves(base_moves)
    mobility, coverage = calculate_sliders_mobility_and_coverage(moves, dimension)
    print(f"{base_moves} | {mobility} | {coverage}%")
    return moves


def calculate_all_sliders(dimensions: int) -> None:
    for dimension in range(1, dimensions + 1):
        queen_moves: list[tuple[tuple[int, ...], ...]] = []
        with ProcessPoolExecutor(max_workers=12) as pool:
            futures = []
            for piece_dimension in range(1, dimension + 1):
                futures.extend(
                    [
                        pool.submit(calculate_sliders, dimension, piece_dimension)
                        for piece_dimension in range(1, piece_dimension)
                    ]
                )
            for future in as_completed(futures):
                queen_moves.extend(future.result())
        for piece_dimension in range(1, dimension + 1):
            queen_moves.extend(calculate_sliders(dimension, piece_dimension))
        mobility, coverage = calculate_sliders_mobility_and_coverage(
            tuple(queen_moves), dimension
        )
        print(f"Queen | {mobility} | {coverage}%")


def main() -> None:
    print("SLIDERS :\n\n")
    calculate_all_sliders(8)
    print("LEAPERS :\n\n")
    calculate_all_leapers(8)


if __name__ == "__main__":
    main()
