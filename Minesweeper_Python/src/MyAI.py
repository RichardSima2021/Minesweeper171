# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

from AI import AI
from Action import Action
from queue import Queue
import math

class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		self.totalMines = totalMines
		self.totalMinesLeft = totalMines
		self.coveredTilesLeft = rowDimension*colDimension - 1
		self.unknownTilesLeft = rowDimension*colDimension - 1

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		self.rowDimension = rowDimension
		self.colDimension = colDimension
		self.startX = startX
		self.startY = startY
		self.gameBoard = [[None for _ in range(colDimension)] for _ in range(rowDimension)]
		self.lastActionCoord = None
		self.lastActionCoord = self.startX, self.startY
		# queue of moves based on game board
		#
		self.frontierQueue = Queue()
		self.moveQueue = Queue()
		self.secondFrontier = Queue()
        
		self.enqueuedCoords = set()

		self.debugPrints = False
		pass
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

	def debugPrintBoard(self):
		for row in self.gameBoard:
			rowStr = ''
			for tile in row:
				if tile is None:
					rowStr += '. '
				elif tile == -1:
					rowStr += '! '
				else:
					rowStr += f'{tile} '
			print(rowStr)



	def label(self, x, y):
		return self.gameBoard[x][y]

	def numUnMarkedNeighbors(self,x, y):
		result = 0
		for changeX in [-1, 0, 1]:
			for changeY in [-1, 0, 1]:
				if changeX == 0 and changeY == 0:
					continue
				indexX, indexY = x + changeX, y + changeY
				if 0 <= indexX < self.rowDimension and 0 <= indexY < self.colDimension:
					if self.gameBoard[indexX][indexY] is None:
						result += 1
		return result
		
	def numMarkedNeighbors(self,x,y):
		result = 0
		for changeX in [-1, 0, 1]:
			for changeY in [-1, 0, 1]:
				if changeX == 0 and changeY == 0:
					continue
				indexX, indexY = x + changeX, y + changeY
				if 0 <= indexX < self.rowDimension and 0 <= indexY < self.colDimension:
					if self.gameBoard[indexX][indexY] == -1:
						result += 1
		return result
		
	def effectiveLabel(self, x, y):
		if self.gameBoard[x][y] is None:
			return -1
		return self.label(x, y) - self.numMarkedNeighbors(x, y)

	def enqueueAllUnexploredNeighbors(self, x, y):
		temp_queue = []
		for changeX in [-1, 0, 1]:
			for changeY in [-1, 0, 1]:
				if changeX == 0 and changeY == 0:
					continue  # Skip the current tile itself
				indexX, indexY = x + changeX, y + changeY
				if 0 <= indexX < self.rowDimension and 0 <= indexY < self.colDimension:
					if self.gameBoard[indexX][indexY] is None:  # Check if the tile is unexplored
						# Create a unique identifier for the coordinate
						coord = indexX, indexY
						temp_queue.append(coord)
		# Enqueue all unique and valid neighbors found
		for coord in temp_queue:
			self.frontierQueue.put(coord)
			
	def solve(self):
		# print(list(self.frontierQueue.queue))
		recheckFrontier = Queue()
		
		solvedWithRuleOfThumb = False

		# if rule of thumb can't be applied now, check it again later        
		while not self.frontierQueue.empty():
			x, y = self.frontierQueue.get()
			effective_label = self.effectiveLabel(x, y)
			num_unmarked_neighbors = self.numUnMarkedNeighbors(x, y)
			if effective_label == num_unmarked_neighbors:
				# All unmarked neighbors are mines
				self.markAllNeighborsAsMines(x, y)
				solvedWithRuleOfThumb = True
			elif effective_label == 0:               
				self.enqueueSafeMoves(x, y)
				solvedWithRuleOfThumb = True
			else:
				if effective_label > 0:
					# if the tile has been uncovered before
					# print(f'{x+1},{y+1} could not have rule of thumb applied, re check later')                
					recheckFrontier.put((x,y))
		self.frontierQueue = recheckFrontier

		if not solvedWithRuleOfThumb:
			if len(list(self.moveQueue.queue)) > 1:
				# if there are more moves to make keep performing moves in the move queue
				return
			# choose the least risky move
			self.chooseLeastRiskyMove()
			
	
	def chooseLeastRiskyMove(self):

		def nCk(n, k):
			f = math.factorial
			return (f(n)/(f(k)*f(n-k)))

		if self.debugPrints: print('Use probability')
		# right now frontier contains the edgemost uncovered tiles with labels, we need to use these to estimate

		# set frontier tiles to their effective labels
		effectiveFrontier = dict()
		for tile in self.frontierQueue.queue:
			x, y = tile
			effectiveFrontier[(x,y)] = self.effectiveLabel(x,y)
		
		if self.debugPrints: print('Effective frontier', effectiveFrontier)

		possibleMineSpace = set()
		neighboursOfTile = dict()
		# get tile space where mines could be places
		for tile in effectiveFrontier.keys():
			(x,y) = tile
			neighbours = self.getUnflaggedNeighbours(x,y)
			for coord in neighbours:
				possibleMineSpace.add(coord)
			
			# remember where each tiles neighbours are so we can use it to check the mine arrangements
			neighboursOfTile[(x,y)] = neighbours


		if self.debugPrints: print('Possible Mine locations: ', possibleMineSpace)

		# the rest of the board is all uncovered tiles minus possibleMineSpce
		possibleMineConfigs = self.generateMineConfigs(list(possibleMineSpace), effectiveFrontier)
		# this generates all possible valid mine configs based on the current board

		if self.debugPrints: print(possibleMineConfigs)

		tileMineCounts = {tile: 0 for tile in possibleMineSpace}
		# maps each tile to the number of times a mine could be on it

		totalPossibilities = 0

		totalMinesLeft = self.getTotalMinesLeft()


		for config in possibleMineConfigs:
			if self.debugPrints: print(f'Assuming config: {config}')
			remainingMines = totalMinesLeft - len(config)
			remainingTiles = self.unknownTilesLeft - len(possibleMineSpace)

			if self.debugPrints: print('remaining mines: ',remainingMines)
			if self.debugPrints: print('remaining tiles: ',remainingTiles)

			if remainingTiles >= remainingMines and remainingMines >= 0:
				numPossibilities = nCk(remainingTiles, remainingMines)
				for tile in config:
					tileMineCounts[tile] += numPossibilities
				totalPossibilities += numPossibilities

		tileMineProbabilities = {}
		for tile in tileMineCounts:
			if totalPossibilities > 0:  # Ensure don't divide by zero
				tileMineProbabilities[tile] = tileMineCounts[tile] / totalPossibilities
			else:
				tileMineProbabilities[tile] = 0
		
		if self.debugPrints: print('Probabilities that a mine is in each tile: ', tileMineProbabilities)

		if tileMineProbabilities == {}:
			# if last action in move queue is an unflag we're done
			return

		least_risky_tile = None
		min_probability = float('inf')

		for tile, probability in tileMineProbabilities.items():
			if probability < min_probability:
				min_probability = probability
				least_risky_tile = tile
		
		x,y = least_risky_tile
		if self.debugPrints: print(f'Uncovering least risky tile: {least_risky_tile}')
		self.moveQueue.put((x, y, AI.Action.UNCOVER))
		# prevent duplicates                        
		self.enqueuedCoords.add((x,y))

	

	def generateMineConfigs(self, possibleMineSpace, effectiveFrontier):
		def recursivelyGenerateMineConfig(possibleMineSpace, currentConfig, allConfigs, index):
			if index == len(possibleMineSpace):
				# base case no more possible mine spaces
				if fullConfigValid(currentConfig):
					allConfigs.append(currentConfig.copy())
				# print(currentConfig, 'is a valid full mine config')
				return
			
			# recursive case: test if mine is placed there and also if it is not
			currentConfig.append(possibleMineSpace[index])
			# print('trying', currentConfig, 'as a partial mine config with index',index)
			if placementValid(currentConfig):
				# print('valid placement, trying add one more mine')
				currentConfigCopy = []
				for mine in currentConfig:
					currentConfigCopy.append(mine)
				recursivelyGenerateMineConfig(possibleMineSpace, currentConfigCopy, allConfigs, index + 1)
			currentConfig.pop()

			currentConfigCopy = []
			for mine in currentConfig:
				currentConfigCopy.append(mine)
			# print('Adding one didnt work, trying', currentConfigCopy, ' with the next mine')
			recursivelyGenerateMineConfig(possibleMineSpace, currentConfigCopy, allConfigs, index + 1)

			
		def placementValid(config):
			dupEffecetiveFrontier = effectiveFrontier.copy()	

			# if len(config) > self.getTotalMinesLeft():
			# 	return False

			for mine in config:
			# for every mine
				x, y = mine
				for tile in self.getUncoveredNeighbours(x,y):
					# find its neighbours in the effectiveFrontier and reduce by one
					if tile in dupEffecetiveFrontier:
						dupEffecetiveFrontier[tile] -= 1
						if dupEffecetiveFrontier[tile] < 0:
							return False
			# print(config, 'is a valid partial mine config')
			return True
		

		def fullConfigValid(config):
			dupEffecetiveFrontier = effectiveFrontier.copy()	
			for mine in config:
			# for every mine
				x, y = mine
				for tile in self.getUncoveredNeighbours(x,y):
					# find its neighbours in the effectiveFrontier and reduce by one
					if tile in dupEffecetiveFrontier:
						dupEffecetiveFrontier[tile] -= 1


			# for tile in dupEffecetiveFrontier.keys():
			# 	# everything in frontier should have effective 0 now
			# 	if dupEffecetiveFrontier[tile] != 0:
			# 		return False
			return True



		allConfigs = []
		currentConfig = []

		recursivelyGenerateMineConfig(possibleMineSpace, currentConfig, allConfigs, 0)

		return allConfigs

		
		
	def getTotalMinesLeft(self):
		totalMinesFlagged = 0
		for x in self.gameBoard:
			for y in x:
				if y == -1:
					totalMinesFlagged += 1

		totalMinesLeft = self.totalMines - totalMinesFlagged
		return totalMinesLeft

	
			
		

	def getUnflaggedNeighbours(self, x, y):
		unflaggedNeighbours = set()
		for dx in [-1,0,1]:
			for dy in [-1,0,1]:
				if dx == 0 and dy == 0:
					continue
				else:
					nx, ny = x + dx, y + dy
					if 0 <= nx < self.rowDimension and 0 <= ny < self.colDimension:
						# print((nx, ny), 'is a valid neighbour of', (x,y))
						if self.gameBoard[nx][ny] is None:
							unflaggedNeighbours.add((nx,ny))
		return unflaggedNeighbours
			
	def getUncoveredNeighbours(self, x, y):
		unflaggedNeighbours = set()
		for dx in [-1,0,1]:
			for dy in [-1,0,1]:
				if dx == 0 and dy == 0:
					continue
				else:
					nx, ny = x + dx, y + dy
					if 0 <= nx < self.rowDimension and 0 <= ny < self.colDimension:
						# print((nx, ny), 'is a valid neighbour of', (x,y))
						if self.gameBoard[nx][ny] is not None and self.gameBoard[nx][ny] >= 0:
							unflaggedNeighbours.add((nx,ny))
		return unflaggedNeighbours
			


	def markAllNeighborsAsMines(self, x, y):
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				nx, ny = x + dx, y + dy
				if 0 <= nx < self.rowDimension and 0 <= ny < self.colDimension:
					# print("?")					
					if self.gameBoard[nx][ny] is None:
						self.moveQueue.put((nx, ny, AI.Action.FLAG))
						# self.unknownTilesLeft -= 1
						# self.totalMinesLeft -= 1

	def enqueueSafeMoves(self, x, y):
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				nx, ny = x + dx, y + dy
				if 0 <= nx < self.rowDimension and 0 <= ny < self.colDimension:
					if self.gameBoard[nx][ny] is None and (nx,ny) not in self.enqueuedCoords: 
						# print('Enqueuing uncover', nx, ny)
						self.moveQueue.put((nx, ny, AI.Action.UNCOVER))
						# prevent duplicates                        
						self.enqueuedCoords.add((nx,ny))
						# self.unknownTilesLeft -= 1
						
	def getAction(self, number: int) -> "Action Object":
		########################################################################
		#							YOUR CODE BEGINS						   #
		# execute the next move in the move queue
		# print('debug')
		# return Action(AI.Action.UNCOVER, 0, 0)
		########################################################################
		# print(list(self.moveQueue.queue))
		# check the number returned, update gameBoard accordingly, if it is -1, check if existing is None(unflagged) or -1(flagged), update accordingly
		if number != -1:
			self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] = number
		else:
			if self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] == -1:
				self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] = None
			else:
				self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] = -1
		self.frontierQueue.put((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.enqueueAllUnexploredNeighbors(self.lastActionCoord[0], self.lastActionCoord[1])
		# print(f'Frontier: {list(self.frontierQueue.queue)}')
		self.solve()
		# print(f'After going through frontier and ruling out all moves solvable with rule of thumb: {list(self.frontierQueue.queue)}')
		if self.debugPrints: print(f'Safe moves:')
		for move in self.moveQueue.queue:
			if self.debugPrints: print(move)

		# self.debugPrintBoard()
		
		while not self.moveQueue.empty():
			nx, ny, action = self.moveQueue.get()
			if self.gameBoard[nx][ny] != None:
				continue
			self.lastActionCoord = nx, ny
			self.unknownTilesLeft -= 1
			return Action(action, nx, ny)
		# default action
		return Action(AI.Action.LEAVE)	
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################
