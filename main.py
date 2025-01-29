import curses
from curses import wrapper
import random
import time
import pygame
import threading

shapes = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "L": [[1, 0], [1, 0], [1, 1]],
    "J": [[0, 1], [0, 1], [1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]]
}

shape_colors = {
    "I": 1,
    "O": 2,
    "T": 3,
    "L": 4,
    "J": 5,
    "S": 6,
    "Z": 7 
}

music_path = r"MUSIC_PATH"

def rotate_shape(shape):
    return [list(reversed(col)) for col in zip(*shape)]

def draw_shape(window, shape, top, left, color_pair):
    for row_idx, row in enumerate(shape):
        for col_idx, block in enumerate(row):
            if block == 1:
                window.addstr(top + row_idx, left + col_idx * 2, "[]", color_pair)

def check_collision(shape, top, left, grid):
    shape_height = len(shape)
    shape_width = len(shape[0]) * 2

    if top + shape_height > len(grid):
        return True

    for row_idx, row in enumerate(shape):
        for col_idx, block in enumerate(row):
            if block == 1:
                if top + row_idx >= len(grid) or left // 2 + col_idx < 0 or left // 2 + col_idx >= len(grid[0]):
                    return True
                if grid[top + row_idx][left // 2 + col_idx] is not None:
                    return True
    return False

def lock_shape_in_grid(shape, top, left, grid, color_pair):
    for row_idx, row in enumerate(shape):
        for col_idx, block in enumerate(row):
            if block == 1:
                grid[top + row_idx][left // 2 + col_idx] = color_pair

def draw_grid(window, grid):
    for row_idx, row in enumerate(grid):
        for col_idx, block in enumerate(row):
            if block is not None:
                window.addstr(row_idx, col_idx * 2, "[]", block)

def clear_full_lines(grid):
    new_grid = [row for row in grid if any(block is None for block in row)]
    full_lines = len(grid) - len(new_grid)
    for _ in range(full_lines):
        new_grid.insert(0, [None for _ in range(len(grid[0]))])
    return new_grid, full_lines

def game_over(stdscr, score):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    game_over_message = f"Game Over! Your score: {score}"
    stdscr.addstr(height // 2, (width // 2) - len(game_over_message) // 2, game_over_message, curses.color_pair(4))
    stdscr.refresh()
    time.sleep(3)   
    
def play_music(music):
    pygame.mixer.init()
    pygame.mixer.music.load(music)
    pygame.mixer.music.play(-1)


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)  
    stdscr.timeout(100)

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx()

    game_height = 25
    game_width = 15

    start_y = (height - game_height - 2) // 2
    start_x = (width - (game_width * 2 + 2)) // 2
    game_window = curses.newwin(game_height + 2, game_width * 2 + 2, start_y, start_x)
    game_window.box()
    grid = [[None for _ in range(game_width)] for _ in range(game_height)]

    stdscr.addstr(height // 2, (width // 2) - len("Press 'q' to exit") // 2, "Press 'q' to exit", curses.color_pair(4))
    stdscr.refresh()
    time.sleep(2)
    shape_type = random.choice(list(shapes.keys()))
    current_shape = shapes[shape_type]
    current_color = curses.color_pair(shape_colors[shape_type])
    top = 0
    left = (game_width - len(current_shape[0])) * 2 // 2
    
    score = 0

    fall_speed = 0.5
    last_fall_time = time.time()

    while True:
        game_window.clear()
        game_window.box()
        stdscr.addstr(0, 0, f"Score: {score}", curses.color_pair(4))
        stdscr.refresh()
        draw_grid(game_window, grid)

        draw_shape(game_window, current_shape, top, left, current_color)
        game_window.refresh()
        key = stdscr.getch()

        if key == curses.KEY_RIGHT:
            if not check_collision(current_shape, top, left + 2, grid):
                left += 2
        elif key == curses.KEY_LEFT:
            if not check_collision(current_shape, top, left - 2, grid):
                left -= 2
        elif key == curses.KEY_DOWN:
            if not check_collision(current_shape, top + 1, left, grid):
                top += 1
        elif key == curses.KEY_UP:
            rotated_shape = rotate_shape(current_shape)
            if not check_collision(rotated_shape, top, left, grid):
                current_shape = rotated_shape

        if key == ord('q'):
            break

        current_time = time.time()
        if current_time - last_fall_time > fall_speed:
            if not check_collision(current_shape, top + 1, left, grid):
                top += 1
            else:
                lock_shape_in_grid(current_shape, top, left, grid, current_color)
                grid, cleared_lines = clear_full_lines(grid)
                score += cleared_lines * 10
                shape_type = random.choice(list(shapes.keys()))
                current_shape = shapes[shape_type]
                current_color = curses.color_pair(shape_colors[shape_type])
                top = 0
                left = (game_width - len(current_shape[0])) * 2 // 2
                if check_collision(current_shape, top, left, grid):
                    game_over(stdscr, score)
                    break
            last_fall_time = current_time
            
wrapper(lambda stdscr: threading.Thread(target=play_music, args=(music_path,)).start() or main(stdscr))
