from subprocess import run
from sys import executable
from math import floor
from time import time
from os import path
from random import randint, shuffle, choice

print("Loading libraries. . . Please wait")

# Installs pygame (if it isn't already on your computer)
run([executable, "-m", "pip", "-q", "install", "pygame"])
import pygame


# Used to hold dimensional positions and dimensions
class Vector2:
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y


# Holds all values needed to determine checker movement
class Checker:
	def __init__(self, direction=1, color=(255, 255, 255), player=1):
		self.direction = direction
		self.color = color
		self.is_king = False
		self.player = player


# Hold all values for a given space on the board
class Space:
	def __init__(self, position=Vector2(), color=(0,0,0)):
		self.color = color
		self.full = False
		self.checker = Checker()
		self.position = position
		self.clicked = False


# Manages all game states and input/output
class GameManager:
	def __init__(self):
		self.height = 720
		self.width = 640
		self.board_size = 10
		self.running = True
		self.space_size = 64
		self.spaces = []
		self.columns = []
		self.fps_cap = 60
		self.has_clicked = False
		self.selected_index = -1
		self.start_time = 0
		self.turn = 1
		self.menu_open = False
		self.wins_location = "./wins.txt"
		self.loss_location = "./losses.txt"
		self.wins = 0
		self.losses = 0
		self.playing_computer = False
		self.delta_time = 0
		self.times = []
		self.moving = False
		self.chip_pos = Vector2()
		self.fill_index = 0
		self.old_space_index = 0
		self.speed = 1.2
		self.moving_checker = None
		self.game_won = False
		self.winner = "Player 1"
		self.has_been_setup = False
		self.going_to = []
		self.last_was_jump = False
		self.double = False

	# Sets up the board
	def setup(self):
		if not self.has_been_setup:
			self.screen_height = int(pygame.display.Info().current_h * 0.9)
			self.height = self.screen_height
			self.width = self.screen_height - 160
			self.space_size = int(self.width / self.board_size)
			self.screen = pygame.display.set_mode((self.width, self.height))
			self.clock = pygame.time.Clock()
			self.font = pygame.font.SysFont("Arial", 30)
		self.spaces = []
		self.game_won = False
		self.moving = False
		self.has_been_setup = True
		self.turn = 1
		self.start_time = time()
		oddColor = (255, 255, 255)
		# Writes the wins folder if it doesn't already exist
		if not path.exists(self.wins_location):
			f = open(self.wins_location, "w")
			f.write("0")
			f.close()
		# Writes the losses folder if it doesn't already exist
		if not path.exists(self.loss_location):
			f = open(self.loss_location, "w")
			f.write("0")
			f.close()
		# Generates the board
		for i in range(self.board_size**2):
			if i % self.board_size == 0:
				if oddColor == (255, 255, 255):
					oddColor = (0, 0, 0)
				else:
					oddColor = (255, 255, 255)
			color = oddColor
			if i % 2 == 0:
				if oddColor == (255, 255, 255):
					color = (0, 0, 0)
				else:
					color = (255, 255, 255)
			y = floor(i / self.board_size)
			x = i - y * self.board_size
			space = Space(Vector2(x, y), color)
			self.spaces.append(space)
		# Sets the first 3 rows of checkers to Red
		for j in range(self.board_size*3):
			checker = Checker(1, (255, 0, 0), 1)
			if self.spaces[j].color == (0, 0, 0):
				self.spaces[j].full = True
				self.spaces[j].checker = checker
		# Sets the final 3 rows of checkers to Blue
		for k in range(self.board_size*7, self.board_size**2):
			checker = Checker(-1, (0, 0, 255), 2)
			if self.spaces[k].color == (0, 0, 0):
				self.spaces[k].full = True
				self.spaces[k].checker = checker

		# Read the wins and losses from their files
		f = open(self.wins_location, "r")
		self.wins = int(f.read())
		f.close()
		f = open(self.loss_location, "r")
		self.losses = int(f.read())
		f.close()

	# Deselects all checkers on the board
	def deselect_checkers(self):
		self.has_clicked = False
		for space in self.spaces:
			space.clicked = False

	# Converts the player's number to their checker color
	def player_to_color(self, player):
		if player == 1:
			return "red"
		return "blue"

	# Returns a space at the given position
	def get_space(self, position):
		if position.x >= 0 and position.y >= 0 and position.x <= 9 and position.y <= 9:
			_index = position.y * 10 + position.x
			return self.spaces[_index]
		return False

	# Does the movement calculations for player 2 if in singleplayer mode
	def ai_turn(self):
		found = False
		end_checker = None
		all_spaces = []
		for space in self.spaces:
			if space.full and space.checker.direction == -1:
				all_spaces.append(space)
		shuffle(all_spaces)
		for space in all_spaces:
			if space.full and space.checker.direction == -1:
				spaces = self.get_spaces(space)
				jump_spaces = []
				for space2 in spaces:
					if abs(space.position.y - space2.position.y) > 1:
						jump_spaces.append(space2)
				# Steps 1 and 2
				if len(jump_spaces) > 0:
					better_jump_spaces = []
					for space2 in jump_spaces:
						for s in self.spaces:
							if s.full and abs(s.position.y - space2.position.y) <= 1:
								if space2 not in self.get_spaces(s):
									better_jump_spaces.append(space2)
					found = True
					# If we can jump a space without ending up in a space where we can get jumped
					if len(better_jump_spaces) > 0:
						end_checker = choice(better_jump_spaces)
					# Otherwise Kamikaze
					else:
						end_checker = choice(jump_spaces)
					break
		if not found:
			for space in all_spaces:
				spaces = self.get_spaces(space)
				if len(spaces) > 0:
					better_spaces = []
					for space2 in spaces:
						for s in self.spaces:
							if s.full and abs(s.position.y - space2.position.y) <= 1:
								if space2 not in self.get_spaces(s):
									better_spaces.append(space2)
					found = True
					if len(better_spaces) > 0:
						end_checker = choice(better_spaces)
					else:
						end_checker = choice(spaces)
					break

		if found:
			self.moving_checker = space.checker
			self.fill_index = self.spaces.index(end_checker)
			self.old_space_index = self.spaces.index(space)
			self.end_index = end_checker.position
			self.moving = True
			end_checker.checker = space.checker
			space.full = False
			self.chip_pos = Vector2(space.position.x, space.position.y)

	# Makes sure every checker that is supposed to be a king is
	def check_kings(self):
		for i in range(10):
			if self.spaces[i].full and not self.spaces[i].checker.is_king and self.spaces[i].checker.direction == -1:
				self.spaces[i].checker.is_king = True
		for i in range(90, 100):
			if self.spaces[i].full and not self.spaces[i].checker.is_king and self.spaces[i].checker.direction == 1:
				self.spaces[i].checker.is_king = True

	# Called whenever the user clicks
	def manage_click(self):
		# If the current game is complete, calls the setup function so we can begin a new game
		if self.game_won:
			self.game_won = False
			self.setup()
			return
		# If we're playing against a computer, we don't want the user to be able to control it
		if self.playing_computer and self.turn == 2:
			return
		# Makes sure the user can't move a chip while another one is moving
		if self.moving:
			return

		found = False
		mouse_pos = Vector2(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
		# Iterates over every space on the board
		for space in self.spaces:
			# If our mouse is over this given space when we clicked
			if box_collides(mouse_pos, Vector2(space.position.x * self.space_size, space.position.y * self.space_size), Vector2(1,1), Vector2(self.space_size, self.space_size)):
				# If the space has a checker, and the checker does not belong to the current player
				if space.full and space.checker.player != self.turn:
					return
				# If the space has a checker on it
				if space.full:
					# Selects the checker so we can move it next click
					if self.double and self.spaces.index(space) != self.end_index.y * 10 + self.end_index.x:
						return
					space.clicked = True
					self.has_clicked = True
					self.selected_index = self.spaces.index(space)
					found = True
				else:
					# Check to see if it was a moveable space
					if space in self.get_spaces(self.spaces[self.selected_index]):
						if abs(space.position.y - self.spaces[self.selected_index].position.y) == 2:
							self.last_was_jump = True
						else:
							self.last_was_jump = False
						# All of these variables are used for the animation
						self.moving_checker = self.spaces[self.selected_index].checker
						self.fill_index = self.spaces.index(space)
						self.old_space_index = self.selected_index * 1
						self.end_index = space.position
						self.moving = True
						space.full = False
						space.checker = self.spaces[self.selected_index].checker
						self.spaces[self.selected_index].full = False
						self.chip_pos = Vector2(self.spaces[self.selected_index].position.x, self.spaces[self.selected_index].position.y)
						self.selected_index = -1
						found = False
				break
		if not found:
			self.deselect_checkers()

	# Returns all spaces a given checker can move to
	def get_spaces(self, _space, checker=None, max_count=10):
		if max_count == 0:
			return []
		if not checker:
			checker = _space.checker
		spaces = []
		for space in self.spaces:
			# A checker can't jump left/right, so if it's the same Y position, we ignore the space
			if space.position.y == _space.position.y or abs(space.position.y - _space.position.y) > 1:
				continue
			# If the space's Y position is 1 away from the current checker, and it's in the correct direction
			if space.position.y == _space.position.y + checker.direction and abs(space.position.x - _space.position.x) == 1:
				if space.full:
					# If that space is full
					if space.checker.direction != checker.direction:
						x_pos = space.position.x - _space.position.x + space.position.x
						y_pos = space.position.y - _space.position.y + space.position.y
						# Checks to see if it's possible to jump the chip
						if self.get_space(Vector2(x_pos, y_pos)) != False and not self.get_space(Vector2(x_pos, y_pos)).full:
							spaces.append(self.get_space(Vector2(x_pos, y_pos)))
				else:
					spaces.append(space)
			# If the checker is a king, do the opposite of the above
			elif checker.is_king and space.position.y == _space.position.y - checker.direction and abs(space.position.x - _space.position.x) == 1:
				if space.full:
					if space.checker.direction != checker.direction:
						x_pos = space.position.x - _space.position.x + space.position.x
						y_pos = space.position.y - _space.position.y + space.position.y
						if self.get_space(Vector2(x_pos, y_pos)) != False and not self.get_space(Vector2(x_pos, y_pos)).full:
							spaces.append(self.get_space(Vector2(x_pos, y_pos)))
				else:
					spaces.append(space)

		return spaces

	# Returns the current number of losses
	def get_losses(self):
		return self.losses

	# Returns the current number of wins
	def get_wins(self):
		return self.wins

	# Writes to the losses/wins file and sets the game's state to won
	def player_won(self, player):
		self.game_won = True
		if player == 2:
			self.winner = "Player 2"
			self.losses += 1
			#Add to the losses file
			f = open(self.loss_location, "w+")
			f.write(str(self.losses))
			f.close()
		elif player == 1:
			self.winner = "Player 1"
			self.wins += 1
			#Add to the wins file
			f = open(self.wins_location, "w+")
			f.write(str(self.wins))
			f.close()

	# Checks to see if any player has won
	def check_wins(self):
		if self.game_won:
			return
		ones = []
		twos = []
		# Adds a number to ones/twos depending on which player a given checker belongs to
		for space in self.spaces:
			if space.full and space.checker.direction == 1:
				ones.append(1)
			elif space.full and space.checker.direction == -1:
				twos.append(1)
		# If we couldn't find any of player 1's checkers
		if len(ones) == 0:
			self.player_won(2)
		# If we couldn't find any of player 2's checkers
		elif len(twos) == 0:
			self.player_won(1)
		else:
			return

	# Draws the provided text variable at a given positon onto the screen
	def draw_text(self, text, position, color=(255, 255, 255)):
		# Draws the text shadow
		textsurface = self.font.render(text, True, (0, 0, 0))
		self.screen.blit(textsurface, (position.x + 2, position.y + 2))
		# Draws the actual text
		textsurface = self.font.render(text, True, color)
		self.screen.blit(textsurface, (position.x, position.y))

	def turn_to_direction(self, turn):
		if turn == 1:
			return 1
		else:
			return -1

	# Starts the game
	def start(self):
		self.setup()
		self.start_time = time()
		# Sets the space and checker size based on the user's screen size
		space_size = self.space_size
		checker_size = round(self.space_size * 0.85)
		# Runs until the user presses the X
		while self.running:
			if len(self.times) > 0:
				self.delta_time = time() - self.times[len(self.times) - 1]
			self.times.append(time())
			while(time() - self.times[0] > 1):
				self.times.pop(0)
			self.screen.fill((30, 30, 30))
			# Iterates once for each key press, mouse click, window resize etc. . .
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					break
				elif event.type == pygame.MOUSEBUTTONUP:
					self.manage_click()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.menu_open = not self.menu_open
					elif event.key == pygame.K_t:
						self.playing_computer = not self.playing_computer
						if self.turn == 2 and not self.moving:
							self.ai_turn()
					elif event.key == pygame.K_s and self.double:
						self.double = False
						if self.turn == 1:
							self.turn = 2
							if self.playing_computer:
								self.ai_turn()
						else:
							self.turn = 1
			for space in self.spaces:
				pygame.draw.rect(self.screen, space.color, (space.position.x * space_size, space.position.y * space_size, space_size, space_size))
				if space.full:
					circle_pos = Vector2(space.position.x * space_size + round(space_size * 0.5), space.position.y * space_size + round(space_size * 0.5))
					if space.checker.is_king:
						pygame.draw.circle(self.screen, (255, 255, 0), (circle_pos.x, circle_pos.y), round(checker_size * 0.55))
					pygame.draw.circle(self.screen, space.checker.color, (circle_pos.x, circle_pos.y), round(checker_size * 0.5))
			if self.has_clicked:
				spaces = self.get_spaces(self.spaces[self.selected_index])
				for space in spaces:
					circle_pos = Vector2(space.position.x * space_size + round(space_size * 0.5), space.position.y * space_size + round(space_size * 0.5))
					pygame.draw.circle(self.screen, (0, 255, 0), (circle_pos.x, circle_pos.y), round(checker_size * 0.5))
					circle_pos = Vector2(space.position.x * space_size + round(space_size * 0.5), space.position.y * space_size + round(space_size * 0.5))
					pygame.draw.circle(self.screen, (0, 255, 0), (circle_pos.x, circle_pos.y), round(checker_size * 0.5))

			if self.moving:
				self.double = False
				if abs(self.spaces[self.old_space_index].position.y - self.get_space(self.end_index).position.y) == 2:
					self.last_was_jump = True
				else:
					self.last_was_jump = False
				for space in self.spaces:
					if box_collides(space.position, Vector2(self.chip_pos.x + 0.5, self.chip_pos.y + 0.5), Vector2(1,1), Vector2(0.1, 0.1)):
						if space.full:
							space.full = False
							space.checker.direction = -1
				if abs(self.chip_pos.x - self.end_index.x) < self.delta_time * 0.6:
					self.chip_pos.x = self.end_index.x
				if abs(self.chip_pos.y - self.end_index.y) < self.delta_time * 0.6:
					self.chip_pos.y = self.end_index.y


				if self.chip_pos.x == self.end_index.x and self.chip_pos.y == self.end_index.y:
					found = False
					self.moving = False
					self.spaces[self.fill_index].full = True
					self.spaces[self.fill_index].checker = self.spaces[self.old_space_index].checker
					c = None
					if self.last_was_jump:
						for c in self.get_spaces(self.spaces[self.fill_index]):
							if abs(c.position.y - self.spaces[self.fill_index].position.y) == 2:
								found = True
								break
					if found:
						if self.turn == 2 and self.playing_computer:
							space = self.spaces[self.fill_index]
							self.moving_checker = space.checker
							self.fill_index = self.spaces.index(c)
							self.old_space_index = self.spaces.index(space)
							self.end_index = c.position
							self.moving = True
							c.checker = space.checker
							space.full = False
							self.chip_pos = Vector2(space.position.x, space.position.y)
						else:
							self.double = True
							self.moving = False

					else:
						self.check_wins()
						if not self.game_won:
							if self.turn == 1:
								self.turn = 2
								enough = False
								for s in self.spaces:
									if s.full:
										if s.checker.direction == self.turn_to_direction(self.turn):
											if len(self.get_spaces(s)) > 0:
												enough = True
												break
								if not enough:
									self.turn = 1
								else:
									if self.playing_computer:
										self.ai_turn()
							else:
								self.turn = 1
								enough = False
								for s in self.spaces:
									if s.full:
										if s.checker.direction == self.turn_to_direction(self.turn):
											if len(self.get_spaces(s)) > 0:
												enough = True
												break
								if not enough:
									self.turn = 2
									if self.playing_computer:
										self.ai_turn()
					

				if self.end_index.x > self.chip_pos.x:
					self.chip_pos.x += self.delta_time * self.speed
				elif self.end_index.x < self.chip_pos.x:
					self.chip_pos.x -= self.delta_time * self.speed

				if self.end_index.y > self.chip_pos.y:
					self.chip_pos.y += self.delta_time * self.speed
				elif self.end_index.y < self.chip_pos.y:
					self.chip_pos.y -= self.delta_time * self.speed
				circle_pos = Vector2(self.chip_pos.x * space_size + round(space_size * 0.5), self.chip_pos.y * space_size + round(space_size * 0.5))
				if self.spaces[self.old_space_index].checker.is_king:
						pygame.draw.circle(self.screen, (255, 255, 0), (round(circle_pos.x), round(circle_pos.y)), round(checker_size * 0.55))
				pygame.draw.circle(self.screen, self.moving_checker.color, (round(circle_pos.x), round(circle_pos.y)), round(checker_size * 0.5))
			else:
				self.check_wins()

			text = f"{self.player_to_color(self.turn).upper()}'s Turn"
			if self.double:
				text += " (You can double jump. Press 'S' to skip)"
			self.draw_text(text, Vector2(30, self.screen_height - 160))
			_time = round(time() - self.start_time)
			minutes = floor(_time / 60) 
			seconds = _time - minutes * 60
			if seconds < 10:
				seconds = "0" + str(seconds)
			if minutes < 10:
				minutes = "0" + str(minutes)
			self.draw_text(f"TIME: {minutes}:{seconds}", Vector2(30, self.screen_height - 120))
			game_mode = "Singleplayer"
			if self.playing_computer:
				game_mode = "Multiplayer  "
			self.draw_text(f"GameMode: {game_mode} (press 'T' to toggle)", Vector2(30, self.screen_height - 40));
			self.draw_text("Press Escape to view stats", Vector2(30, self.screen_height - 80))
			self.draw_text(f"FPS: {len(self.times)}", Vector2(30, 30), (0, 255, 0))
			if self.game_won:
				pygame.draw.rect(self.screen, (30, 30, 30), (0, int((self.height - 160) / 2) - round(self.height * 0.05), self.width, round(self.height * 0.1)))
				text = self.font.render(f"{self.winner} won the game!", True, (0, 0, 0))
				text_rect = text.get_rect(center=(int(self.width*0.5 + 3), int((self.height - 160)*0.5 + 3)))
				self.screen.blit(text, text_rect)
				text = self.font.render(f"{self.winner} won the game!", True, (255, 255, 255))
				text_rect = text.get_rect(center=(int(self.width*0.5), int((self.height - 160)*0.5)))
				self.screen.blit(text, text_rect)
			if self.menu_open:
				pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.width, self.height))
				self.draw_text(f"Player 1 Wins: {self.get_wins()}", Vector2(30, 30))
				self.draw_text(f"Player 2 Wins: {self.get_losses()}", Vector2(30, 70))
				self.draw_text(f"Games Played: {self.get_wins() + self.get_losses()}", Vector2(30, 110))
			pygame.display.flip()
			self.check_kings()
			self.clock.tick(int(self.fps_cap * 1.015))

def collides(x, y, r, b, x2, y2, r2, b2):
	return not (r <= x2 or x > r2 or b <= y2 or y > b2);

# Returns True if 2 boxes collide
def box_collides(pos, pos2, size1, size2):
	return collides(pos.x, pos.y,
		pos.x + size1.x, pos.y + size1.y,
		pos2.x, pos2.y,
		pos2.x + size2.x, pos2.y + size2.y);


# Initializes pygame
pygame.init()
# Starts the game
game = GameManager()
game.start()