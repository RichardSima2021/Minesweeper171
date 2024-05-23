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
		#
		self.frontierQueue = Queue()
		self.moveQueue = Queue()
		self.secondFrontier = Queue()

		self.enqueuedInFrontier = set()
		self.visitedTiles = set()

		self.uncoveredQueue = Queue()
		self.frontierSet = {(startX,startY)}
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
			# self.frontierQueue.put(coord)
			self.frontierSet.add(coord)
			# prevents duplicates
			self.enqueuedInFrontier.add(coord)
			
	def solve(self):
		# print(list(self.frontierQueue.queue))
		recheckQueue = Queue()
		
		solvedWithRuleOfThumb = False

		if self.getTotalMinesLeft() == 0:
			# if no mines left uncover all tiles
			for row in range(len(self.gameBoard)):
				for col in range(len(self.gameBoard[row])):
					if self.gameBoard[row][col] is None:
						# self.moveQueue.put((row, col, AI.Action.UNCOVER))
						# prevent duplicates						
						self.moveSet.add((row, col, AI.Action.UNCOVER))
						# prevent frontierSet key not found bug
						self.frontierSet.add((row,col))

		# if rule of thumb can't be applied now, check it again later		
		while not self.uncoveredQueue.empty():
			x, y = self.uncoveredQueue.get()
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
					recheckQueue.put((x,y))
		self.uncoveredQueue = recheckQueue

		if not solvedWithRuleOfThumb:
			# need to invoke this 
			# if len(list(self.moveQueue.queue)) > 0:
			# 	return
			if len(list(self.moveSet)) > 0:
				return

			# if theres no more moves to make
			# choose the least risky move
			self.chooseLeastRiskyMove()
			
	
	def chooseLeastRiskyMove(self):
		def nCk(n, k):
			f = math.factorial
			return f(n) // (f(k) * f(n - k))

		print('Use probability')

		effectiveEdgeTiles = {tile: self.effectiveLabel(tile[0], tile[1]) for tile in self.uncoveredQueue.queue}

		possibleMineSpace = set()
		neighboursOfTile = {}

		for tile in effectiveEdgeTiles.keys():
			x, y = tile
			neighbours = self.getUnflaggedNeighbours(x, y)
			possibleMineSpace.update(neighbours)
			neighboursOfTile[(x, y)] = neighbours

		connectedComponents = self.getConnectedComponents(possibleMineSpace, max_size=10)

		allMineProbabilities = {}
		for component in connectedComponents:
			componentList = list(component)
			componentMineConfigs = self.generateMineConfigs(componentList, effectiveEdgeTiles)
			tileMineCounts = {tile: 0 for tile in componentList}
			totalPossibilities = 0
			totalMinesLeft = self.getTotalMinesLeft()

			for config in componentMineConfigs:
				remainingMines = totalMinesLeft - len(config)
				remainingTiles = self.unknownTilesLeft - len(possibleMineSpace)

				if remainingTiles >= remainingMines >= 0:
					numPossibilities = nCk(remainingTiles, remainingMines)
					for tile in config:
						tileMineCounts[tile] += numPossibilities
					totalPossibilities += numPossibilities

			for tile in tileMineCounts:
				if totalPossibilities > 0:
					allMineProbabilities[tile] = tileMineCounts[tile] / totalPossibilities
				else:
					allMineProbabilities[tile] = 0

		if not allMineProbabilities:
			return

		least_risky_tile = min(allMineProbabilities, key=allMineProbabilities.get)
		x, y = least_risky_tile

		self.frontierSet.add((x, y))
		self.moveSet.add((x, y, AI.Action.UNCOVER))

	def getConnectedComponents(self, possibleMineSpace, max_size=10):
		def bfs(start, graph, visited):
			queue = [start]
			component = set()
			while queue:
				node = queue.pop(0)
				if node not in visited:
					visited.add(node)
					component.add(node)
					queue.extend(graph[node] - visited)
			return component

		def split_large_component(component, graph, max_size):
			component_list = list(component)
			subcomponents = []
			visited = set()

			def dfs(node, current_component):
				stack = [node]
				while stack and len(current_component) < max_size:
					v = stack.pop()
					if v not in visited:
						visited.add(v)
						current_component.add(v)
						stack.extend(graph[v] - visited)

			for node in component_list:
				if node not in visited:
					current_component = set()
					dfs(node, current_component)
					subcomponents.append(current_component)

			return subcomponents

		graph = {tile: set() for tile in possibleMineSpace}
		for tile in possibleMineSpace:
			x, y = tile
			for dx in [-1, 0, 1]:
				for dy in [-1, 0, 1]:
					if dx == 0 and dy == 0:
						continue
					nx, ny = x + dx, y + dy
					if (nx, ny) in possibleMineSpace:
						graph[tile].add((nx, ny))

		visited = set()
		components = []
		for tile in graph:
			if tile not in visited:
				component = bfs(tile, graph, visited)
				if len(component) > max_size:
					components.extend(split_large_component(component, graph, max_size))
				else:
					components.append(component)

		return components
	

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
						# self.moveQueue.put((nx, ny, AI.Action.FLAG))
						self.moveSet.add((nx, ny, AI.Action.FLAG))
						numMarkedNeighbors += 1

						if (nx, ny, AI.Action.UNCOVER) in self.moveSet:
							self.moveSet.remove((nx, ny, AI.Action.UNCOVER))
						# for move in self.moveQueue.queue:
						# 	if (move[0], move[1]) == (nx, ny) and move[2] != AI.Action.FLAG:
						# 		# sometimes the probability gets invoked when it isn't supposed to and adds a wrong move
						# 		# if we can confirm with 100% certainty that move is wrong, we should remove it
						# 		self.moveQueue.queue.remove(move)
						# 		self.moveSet.remove(move)
						# 		break
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
						# print('Enqueuing uncover', nx, ny)
						# self.moveQueue.put((nx, ny, AI.Action.UNCOVER))
						enqueuedSafeMoves += 1
						# prevent duplicates						
						self.moveSet.add((nx, ny, AI.Action.UNCOVER))

						if (nx, ny, AI.Action.FLAG) in self.moveSet:
							self.moveSet.remove((nx, ny, AI.Action.FLAG))

						# for move in self.moveQueue.queue:
						# 	if (move[0], move[1]) == (nx, ny) and move[2] != AI.Action.UNCOVER:
						# 		# sometimes the probability gets invoked when it isn't supposed to and adds a wrong move
						# 		# if we can confirm with 100% certainty that move is wrong, we should remove it
						# 		self.moveQueue.queue.remove(move)
						# 		self.moveSet.remove(move)
						# 		break
		
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

		self.uncoveredQueue.put((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.frontierSet.remove((self.lastActionCoord[0], self.lastActionCoord[1]))
		# self.frontierQueue.put((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.visitedTiles.add((self.lastActionCoord[0], self.lastActionCoord[1]))
		self.enqueueAllUnexploredNeighbors(self.lastActionCoord[0], self.lastActionCoord[1])

		# print(f'Uncovered Frontier: {sorted(list(self.uncoveredQueue.queue))}')
		# print(f'Covered Frontier: {sorted(list(self.frontierSet))}')

		self.solve()

		# print(f'After going through uncovered and ruling out all moves solvable with rule of thumb: {list(self.uncoveredQueue.queue)}')
		# print(f'Safe moves:')
		# for move in self.moveSet:
		# 	print(move)

		# self.debugPrintBoard()
		
		# while not self.moveQueue.empty():
		while len(self.moveSet) > 0:
			# nx, ny, action = self.moveQueue.get()
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
