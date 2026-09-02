from fractions import Fraction
from itertools import permutations


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


def make_moves(moves_base: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    moves: list[tuple[int, ...]] = []
    for move_unsigned in {move for move in permutations(moves_base, len(moves_base))}:
        move_signed = list(move_unsigned)
        moves.extend(give_sign(move_signed, 0))
    return tuple(moves)


def calculate_mobility_and_coverage(
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
                for i, n in enumerate(move):
                    new_coord[i] += n
                    if new_coord[i] < 0 or new_coord[i] > 7:
                        not_valid = True
                        break
                if not_valid:
                    continue
                coord_tuple = tuple(new_coord)
                if coord_tuple not in investigated:
                    new_stack.add(coord_tuple)
            investigated.add(coord)
        if len(investigated) == start_len:
            return steps - 1, Fraction(len(investigated), 8**dimensions) * 100
        stack = new_stack


def main() -> None:
    for dimensions in range(2, 7):
        for piece_dimension in range(dimensions + 1):
            for index in range(1, piece_dimension):
                base_moves = tuple(
                    index * [1]
                    + (piece_dimension - index) * [2]
                    + (dimensions - piece_dimension) * [0]
                )
                moves = make_moves(base_moves)
                mobility, coverage = calculate_mobility_and_coverage(moves, dimensions)
                print(f"{base_moves} | {mobility} | {coverage}%")


if __name__ == "__main__":
    main()
