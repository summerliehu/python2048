#-*- coding:utf-8 -*-

import curses
from random import randrange, choice 
from collections import defaultdict

letter_codes = ['W','A','S','D','R','Q','w','a','s','d','r','q']
actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
actions_dict = dict(zip(letter_codes, actions * 2))


def transpose(field):
    return [list(row) for row in zip(*field)]

def invert(field):
    return [row[::-1] for row in field]

class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.height = height
        self.width = width
        self.win_value = win
        self.score = 0
        self.highscore = 0
        self.reset()

    def get_user_action(self, keyboard):
        char = "N"  
        while char not in actions_dict:
            char = keyboard.getkey()
        return actions_dict[char]

    def reset(self):
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def move(self, direction):
        def move_row_left(row):
            def tighten(row): # squeese non-zero elements together
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row
            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left']  = lambda field:                              \
                [move_row_left(row) for row in field]
        moves['Right'] = lambda field:                              \
                invert(moves['Left'](invert(field)))
        moves['Up']    = lambda field:                              \
                transpose(moves['Left'](transpose(field)))
        moves['Down']  = lambda field:                              \
                transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    def is_win(self):
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'
        def cast(string):
            screen.addstr(string + '\n')

        def draw_hor_separator():
            line = '+' + ('+------' * self.width + '+')[1:]
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        if 0 != self.highscore:
            cast('HIGHSCORE: ' + str(self.highscore))
        for row in self.field:
            draw_hor_separator()
            draw_row(row)
        draw_hor_separator()
        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)

    def spawn(self):
        new_element = 4 if randrange(100) > 89 else 2
        (i,j) = choice([(i,j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            def change(i): # true if there'll be change in i-th tile
                if row[i] == 0 and row[i + 1] != 0: # Move
                    return True
                if row[i] != 0 and row[i + 1] == row[i]: # Merge
                    return True
                return False
            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left']  = lambda field:                              \
                any(row_is_left_movable(row) for row in field)

        check['Right'] = lambda field:                              \
                 check['Left'](invert(field))

        check['Up']    = lambda field:                              \
                check['Left'](transpose(field))

        check['Down']  = lambda field:                              \
                check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

def main(stdscr):
    def init():
        #重置游戏棋盘
        #Use the reset function to initialize the game
        game_field.reset()
        return 'Game'

    def not_game(state):
        #画出 GameOver 或者 Win 的界面
        #Function launched when the game is won or over
        game_field.draw(stdscr)
        #读取用户输入得到action，判断是重启游戏还是结束游戏
        #Waiting for the user to make an action
        action = game_field.get_user_action(stdscr)
        responses = defaultdict(lambda: state) #默认是当前状态，没有行为就会一直在当前界面循环
        #Treatment of the action writen by the user
        responses['Restart'], responses['Exit'] = 'Init', 'Exit' #对应不同的行为转换到不同的状态
        
        return responses[action]


    def game():
        #画出当前棋盘状态
        #Drawing the game field
        game_field.draw(stdscr)
        #Asking if the user push a button in order to do an action
        #读取用户输入得到action
        action = game_field.get_user_action(stdscr)


        #Treatment of the action depending on what the user want
        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action): # move successful
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'


    state_actions = {
            'Init': init,
            'Win': lambda: not_game('Win'),
            'Gameover': lambda: not_game('Gameover'),
            'Game': game
        }

    curses.use_default_colors()
    #Condition for the user to win
    # 设置终结状态最大数值为 32，可以自行修改
    game_field = GameField(win=32)


    state = 'Init'
    #状态机开始循环
    #Condition to leave the game
    while state != 'Exit':
        state = state_actions[state]()

curses.wrapper(main)

