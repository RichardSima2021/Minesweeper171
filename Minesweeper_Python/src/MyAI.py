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
import concurrent.futures

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

		self.enqueuedInFrontier = set()
		self.visitedTiles = set()

		self.uncoveredFrontier = set()
		self.coveredFrontier = {(startX,startY)}
		self.moveSet = set()

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
		
		print('---------------------------------------')



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
					# if self.gameBoard[indexX][indexY] is not None and (indexX,indexY) not in self.visitedTiles:  # Check if the tile is unexplored
					if self.gameBoard[indexX][indexY] is None: 
						# Create a unique identifier for the coordinate
						coord = indexX, indexY
						# print(f'Add {coord} to frontier')
						if coord not in self.enqueuedInFrontier:
							# prevents duplicates
							temp_queue.append(coord)
		# Enqueue all unique and valid neighbors found
		for coord in temp_queue:
			self.coveredFrontier.add(coord)
			# prevents duplicates
			self.enqueuedInFrontier.add(coord)
			
	def solve(self):
		recheckSet = set()
		
		solvedWithRuleOfThumb = False

		if self.getTotalMinesLeft() == 0:
			# if no mines left uncover all tiles
			for row in range(len(self.gameBoard)):
				for col in range(len(self.gameBoard[row])):
					if self.gameBoard[row][col] is None:
						# prevent duplicates                        
						self.moveSet.add((row, col, AI.Action.UNCOVER))
						# prevent coveredFrontier key not found bug
						self.coveredFrontier.add((row,col))

		# if rule of thumb can't be applied now, check it again later        
		while len(self.uncoveredFrontier):
			x, y = self.uncoveredFrontier.pop()
			# print(f'Try to apply rule of thumb to {x,y}')
			effective_label = self.effectiveLabel(x, y)
			num_unmarked_neighbors = self.numUnMarkedNeighbors(x, y)
			if effective_label == num_unmarked_neighbors:
				# All unmarked neighbors are mines
				numMarkedNeighbors = self.markAllNeighborsAsMines(x, y)
				# print(f'All neighbors rule applied to {x,y}')
				solvedWithRuleOfThumb = (numMarkedNeighbors > 0)
			elif effective_label == 0:               
				numEnqueuedSafe = self.enqueueSafeMoves(x, y)
				# print(f'Effective Label 0 rule applied to {x,y}')
				solvedWithRuleOfThumb = (numEnqueuedSafe > 0)
			else:
				if effective_label > 0:
					# if the tile has been uncovered before
					# print(f'{x,y} could not have rule of thumb applied, re check later')                
					recheckSet.add((x,y))
		self.uncoveredFrontier = recheckSet

		if not solvedWithRuleOfThumb:
			# need to invoke this 
			if len(list(self.moveSet)) > 0:
				return

			# if theres no more moves to make
			# choose the least risky move
			# self.chooseLeastRiskyMove()
			self.chooseLeastRiskyTileset()

	def chooseLeastRiskyTileset(self):
		
		
		# generate effective edge tiles
		effectiveEdgeTiles = dict()
		for tile in self.uncoveredFrontier:
			x, y = tile
			effectiveEdgeTiles[(x,y)] = self.effectiveLabel(x,y)
		
		print('Possible Mine Spaces: ', sorted(self.coveredFrontier))
		print('Effective edge tiles', sorted(effectiveEdgeTiles.items()))
		tileSets = dict()
		maxMinesPerTileSet = dict()
		# go through covered frontier
		for tile in self.coveredFrontier:
		# for each tile, find its uncovered neighbors
			x,y = tile
			neighbours = tuple(self.getUncoveredNeighbours(x,y))
			# print(f'{(x,y)}s uncovered neighbors: {neighbours}')
			if len(neighbours) > 0:
				if neighbours not in tileSets.keys():
					# if this is actually a covered tile adjacent to an uncovered tile
					tileSets[neighbours] = []
				tileSets[neighbours].append((x,y))
		
		for tileSet in tileSets.keys():
			# find largest number of mines this tileset can have

			# this is whichever is smaller between number of tiles in the tileset, and the lowest labelled tile its adjacent to

			maxMines = 0
			numTiles = len(tileSet)
			lowestLabel = effectiveEdgeTiles[tileSet[0]]
			for neighbor in tileSet:
				if effectiveEdgeTiles[neighbor] < lowestLabel:
					lowestLabel = effectiveEdgeTiles[neighbor]
			maxMines = min(numTiles, lowestLabel)
			maxMinesPerTileSet[tileSet] = maxMines

		# each unique set of uncovered neighbors is a tileSet



		
		pass

	def generateMineConfigs_TileSet(self, tileSets, maxMinesPerTileSet, effectiveFrontier):
		pass


	
	def chooseLeastRiskyMove(self):

		def nCk(n, k):
			f = math.factorial
			return (f(n)/(f(k)*f(n-k)))

		print('Use probability')
		# right now uncovered contains the edgemost uncovered tiles with labels, we need to use these to estimate

		# set frontier tiles to their effective labels
		effectiveEdgeTiles = dict()
		for tile in self.uncoveredFrontier:
			x, y = tile
			effectiveEdgeTiles[(x,y)] = self.effectiveLabel(x,y)
		
		# print('Effective edge tiles', effectiveEdgeTiles)

		possibleMineSpace = set()
		neighboursOfTile = dict()
		# get tile space where mines could be places
		for tile in effectiveEdgeTiles.keys():
			(x,y) = tile
			neighbours = self.getUnflaggedNeighbours(x,y)
			for coord in neighbours:
				possibleMineSpace.add(coord)
			
			# remember where each tiles neighbours are so we can use it to check the mine arrangements
			neighboursOfTile[(x,y)] = neighbours


		# print('Possible Mine locations: ', possibleMineSpace)

		# the rest of the board is all uncovered tiles minus possibleMineSpce
		possibleMineConfigs = self.generateMineConfigs(list(possibleMineSpace), effectiveEdgeTiles)
		# this generates all possible valid mine configs based on the current board

		# print(possibleMineConfigs)

		tileMineCounts = {tile: 0 for tile in possibleMineSpace}
		# maps each tile to the number of times a mine could be on it

		totalPossibilities = 0

		totalMinesLeft = self.getTotalMinesLeft()


		for config in possibleMineConfigs:
			# print(f'Assuming config: {config}')
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
		
		# print('Probabilities that a mine is in each tile: ', tileMineProbabilities)

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

		# print(f'Uncovering least risky tile: {least_risky_tile}')

		self.coveredFrontier.add((x,y))
		# prevent duplicates                        
		self.moveSet.add((x, y, AI.Action.UNCOVER))

	

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
		numMarkedNeighbors = 0
		# we use this to keep track of whether this rule of thumb did anything, if not we don't count it as solved with rule of thumb
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				nx, ny = x + dx, y + dy
				if 0 <= nx < self.rowDimension and 0 <= ny < self.colDimension:
					# print("?")					
					if self.gameBoard[nx][ny] is None and (nx, ny, AI.Action.FLAG) not in self.moveSet:
						self.moveSet.add((nx, ny, AI.Action.FLAG))
						numMarkedNeighbors += 1

						if (nx, ny, AI.Action.UNCOVER) in self.moveSet:
							self.moveSet.remove((nx, ny, AI.Action.UNCOVER))
		return numMarkedNeighbors



	def enqueueSafeMoves(self, x, y):
		enqueuedSafeMoves = 0
		# we use this to keep track of whether this rule of thumb did anything, if not we don't count it as solved with rule of thumb
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				nx, ny = x + dx, y + dy
				if 0 <= nx < self.rowDimension and 0 <= ny < self.colDimension:
					if self.gameBoard[nx][ny] is None and (nx, ny, AI.Action.UNCOVER) not in self.moveSet: 
						enqueuedSafeMoves += 1
						# prevent duplicates                        
						self.moveSet.add((nx, ny, AI.Action.UNCOVER))

						if (nx, ny, AI.Action.FLAG) in self.moveSet:
							self.moveSet.remove((nx, ny, AI.Action.FLAG))
		
		return enqueuedSafeMoves
						


	def getAction(self, number: int) -> "Action Object":
		########################################################################
		#							YOUR CODE BEGINS						   #
		# execute the next move in the move queue
		# print('debug')
		# return Action(AI.Action.UNCOVER, 0, 0)
		########################################################################
		# check the number returned, update gameBoard accordingly, if it is -1, check if existing is None(unflagged) or -1(flagged), update accordingly
		if number != -1:
			self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] = number
		else:
			if self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] == -1:
				self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] = None
			else:
				self.gameBoard[self.lastActionCoord[0]][self.lastActionCoord[1]] = -1

		self.uncoveredFrontier.add((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.coveredFrontier.remove((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.visitedTiles.add((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.enqueueAllUnexploredNeighbors(self.lastActionCoord[0], self.lastActionCoord[1])

		# print(f'Uncovered Frontier: {sorted(list(self.uncoveredFrontier))}')
		# print(f'Covered Frontier: {sorted(list(self.coveredFrontier))}')

		self.solve()

		# print(f'After going through uncovered and ruling out all moves solvable with rule of thumb: {list(self.uncoveredFrontier)}')
		# print(f'Safe moves:')
		# for move in self.moveSet:
		# 	print(move)

		# self.debugPrintBoard()
		
		while len(self.moveSet) > 0:
			nx, ny, action = self.moveSet.pop()
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
