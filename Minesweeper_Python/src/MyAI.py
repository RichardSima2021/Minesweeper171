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
		self.numCols = colDimension
		self.numRows = rowDimension
		# print(f'Rows, Cols: {(numCols, numRows)}')
		self.startX = startX
		self.startY = startY
		# print(f'Start X,Y: {(startX, startY)}')
		self.gameBoard = [[None for _ in range(colDimension)] for _ in range(rowDimension)]
		# self.debugPrintBoard()
		self.lastActionCoord = None
		self.lastActionCoord = self.startX, self.startY
		# queue of moves based on game board
		#
	
		self.moveQueue = Queue()
		self.secondFrontier = Queue()

		self.enqueuedInFrontier = set()
		self.visitedTiles = set()

		self.uncoveredQueue = Queue()
		self.frontierSet = {(startY,startX)}
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



	def label(self, row, col):
		return self.gameBoard[row][col]

	def numUnMarkedNeighbors(self,row, col):
		result = 0
		for changeX in [-1, 0, 1]:
			for changeY in [-1, 0, 1]:
				if changeX == 0 and changeY == 0:
					continue
				indexRow, indexCol = row + changeY, col + changeX
				if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:
					if self.gameBoard[indexRow][indexCol] is None:
						result += 1
		return result
		
	def numMarkedNeighbors(self,row,col):
		result = 0
		for changeX in [-1, 0, 1]:
			for changeY in [-1, 0, 1]:
				if changeX == 0 and changeY == 0:
					continue
				indexRow, indexCol = row + changeY, col + changeX
				if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:
					if self.gameBoard[indexRow][indexCol] == -1:
						result += 1
		return result
		
	def effectiveLabel(self, row, col):
		if self.gameBoard[row][col] is None:
			return -1
		return self.label(row, col) - self.numMarkedNeighbors(row, col)

	def enqueueAllUnexploredNeighbors(self, row, col):
		temp_queue = []
		for changeX in [-1, 0, 1]:
			for changeY in [-1, 0, 1]:
				if changeX == 0 and changeY == 0:
					continue  # Skip the current tile itself
				indexRow, indexCol = row + changeY, col + changeX
				if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:
					# if self.gameBoard[indexX][indexY] is not None and (indexX,indexY) not in self.visitedTiles:  # Check if the tile is unexplored
					if self.gameBoard[indexRow][indexCol] is None: 
						# Create a unique identifier for the coordinate
						coord = indexRow, indexCol
						# print(f'Add {coord} to frontier')
						if coord not in self.enqueuedInFrontier:
							# prevents duplicates
							temp_queue.append(coord)
		# Enqueue all unique and valid neighbors found
		for coord in temp_queue:
			self.frontierSet.add(coord)
			# prevents duplicates
			self.enqueuedInFrontier.add(coord)
			
	def solve(self):
		recheckQueue = Queue()
		
		solvedWithRuleOfThumb = False

		if self.getTotalMinesLeft() == 0:
			# print("No more mines left")
			# if no mines left uncover all tiles
			for row in range(len(self.gameBoard)):
				for col in range(len(self.gameBoard[row])):
					if self.gameBoard[row][col] is None:
						# self.moveQueue.put((row, col, AI.Action.UNCOVER))
						# prevent duplicates
						self.moveSet.add((col, row, AI.Action.UNCOVER))
						# prevent frontierSet key not found bug
						self.frontierSet.add((row,col))
			# print(f"Remaining Frontier: {self.frontierSet}")

		# if rule of thumb can't be applied now, check it again later		
		while not self.uncoveredQueue.empty():
			row, col = self.uncoveredQueue.get()
			# print(f'Try to apply rule of thumb to {col,row}')
			effective_label = self.effectiveLabel(row, col)
			# print(f"Effective label of {col, row} is {effective_label}")
			num_unmarked_neighbors = self.numUnMarkedNeighbors(row, col)
			# print(f"Num unmarked neighbors of {col, row} is {num_unmarked_neighbors}")
			if effective_label == num_unmarked_neighbors and effective_label > 0:
				# All unmarked neighbors are mines
				numMarkedNeighbors = self.markAllNeighborsAsMines(row, col)
				# print(f'All neighbors rule applied to {col,row}')
				solvedWithRuleOfThumb = (numMarkedNeighbors > 0)
			elif effective_label == 0:			   
				numEnqueuedSafe = self.enqueueSafeMoves(row, col)
				# print(f'Effective Label 0 rule applied to {col,row}')
				solvedWithRuleOfThumb = (numEnqueuedSafe > 0)
			else:
				if effective_label > 0:
					# if the tile has been uncovered before
					# print(f'{x,y} could not have rule of thumb applied, re check later')				
					recheckQueue.put((row,col))
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

		# print('Use probability')

		uncoveredSet = set(self.uncoveredQueue.queue)

		effectiveEdgeTiles = {tile: self.effectiveLabel(tile[0], tile[1]) for tile in self.uncoveredQueue.queue}

		possibleMineSpace = set()
		neighboursOfTile = {}

		for tile in effectiveEdgeTiles.keys():
			row, col = tile
			neighbours = self.getUnflaggedNeighbours(row, col)
			possibleMineSpace.update(neighbours)
			# possibleMineSpace stores {(row,col), (row,col)}
			neighboursOfTile[(row, col)] = neighbours

		
		# max size of frontier
		connectedComponents = self.getConnectedComponents(possibleMineSpace, max_size=21)

		allMineProbabilities = {}
		for component in sorted(connectedComponents, key=lambda x:len(x)):
			componentList = list(component)
			# print("component list:", componentList)

			# find effectiveEdgeTiles of current component
			componentEffectiveEdges = dict()
			for space in component:
				row, col = space
				for neighbor in self.getUncoveredNeighbours(row, col):
					n_row, n_col = neighbor
					componentEffectiveEdges[(n_row, n_col)] = self.effectiveLabel(n_row, n_col)


			componentMineConfigs = self.generateMineConfigs(componentList, componentEffectiveEdges)
			# print("Mine configs for this component:", componentMineConfigs)
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
		

		# for mine, probability in sorted(allMineProbabilities.items(), key=lambda item: item[1]):
		# 	print(mine, probability)
		

		least_risky_tile = min(allMineProbabilities, key=allMineProbabilities.get)
		row, col = least_risky_tile

		self.frontierSet.add((row, col))
		self.moveSet.add((col, row, AI.Action.UNCOVER))
	

	def getConnectedComponents(self, possibleMineSpace, max_size=15):
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
			row, col = tile
			for dx in [-1, 0, 1]:
				for dy in [-1, 0, 1]:
					if dx == 0 and dy == 0:
						continue
					indexRow, indexCol = row + dy, col + dx
					if (indexRow, indexCol) in possibleMineSpace:
						graph[tile].add((indexRow, indexCol))

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
				# print(f"Test {currentConfig}")
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

			if len(config) > self.getTotalMinesLeft():
				return False

			for mine in config:
			# for every mine
				row, col = mine
				for tile in self.getUncoveredNeighbours(row,col):
					# find its neighbours in the effectiveFrontier and reduce by one
					if tile in dupEffecetiveFrontier:
						dupEffecetiveFrontier[tile] -= 1
						if dupEffecetiveFrontier[tile] < 0:
							return False
			return True
		

		def fullConfigValid(config):
			dupEffecetiveFrontier = effectiveFrontier.copy()	
			for mine in config:
			# for every mine
				row, col = mine
				for tile in self.getUncoveredNeighbours(row,col):
					# find its neighbours in the effectiveFrontier and reduce by one
					if tile in dupEffecetiveFrontier.keys():
						dupEffecetiveFrontier[tile] -= 1
			
			# if self.unknownTilesLeft == len(possibleMineSpace):
			for tile in dupEffecetiveFrontier.keys():
				if dupEffecetiveFrontier[tile] != 0:	
					# print(f'config failed due to not satisfying tile {tile} with now effective label {dupEffecetiveFrontier[tile]}\n config: {config}')					
					return False
			

			return True



		allConfigs = []
		currentConfig = []
		# print(f"Effective frontier: {effectiveFrontier}")

		recursivelyGenerateMineConfig(possibleMineSpace, currentConfig, allConfigs, 0)

		return allConfigs
		
		
	def getTotalMinesLeft(self):
		totalMinesFlagged = 0
		for row in self.gameBoard:
			for tile in row:
				if tile == -1:
					totalMinesFlagged += 1

		totalMinesLeft = self.totalMines - totalMinesFlagged
		return totalMinesLeft


	def getUnflaggedNeighbours(self, row, col):
		unflaggedNeighbours = set()
		for dx in [-1,0,1]:
			for dy in [-1,0,1]:
				if dx == 0 and dy == 0:
					continue
				else:
					indexRow, indexCol = row + dy, col + dx
					if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:
						# print((nx, ny), 'is a valid neighbour of', (x,y))
						if self.gameBoard[indexRow][indexCol] is None:
							unflaggedNeighbours.add((indexRow,indexCol))
		return unflaggedNeighbours
			
	def getUncoveredNeighbours(self, row, col):
		uncoveredNeighbours = set()
		for dx in [-1,0,1]:
			for dy in [-1,0,1]:
				if dx == 0 and dy == 0:
					continue
				else:
					indexRow, indexCol = row + dy, col + dx
					if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:					
						if self.gameBoard[indexRow][indexCol] is not None and self.gameBoard[indexRow][indexCol] >= 0:
							
							uncoveredNeighbours.add((indexRow,indexCol))
		
		return uncoveredNeighbours
			


	def markAllNeighborsAsMines(self, row, col):
		numMarkedNeighbors = 0
		# we use this to keep track of whether this rule of thumb did anything, if not we don't count it as solved with rule of thumb
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				indexRow, indexCol = row + dy, col + dx
				if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:
					# print("?")					
					if self.gameBoard[indexRow][indexCol] is None and (indexCol, indexRow, AI.Action.FLAG) not in self.moveSet:
						# self.moveQueue.put((nx, ny, AI.Action.FLAG))
						self.moveSet.add((indexCol, indexRow, AI.Action.FLAG))
						numMarkedNeighbors += 1

						if (indexCol, indexRow, AI.Action.UNCOVER) in self.moveSet:
							self.moveSet.remove((indexCol, indexRow, AI.Action.UNCOVER))
		return numMarkedNeighbors



	def enqueueSafeMoves(self, row, col):
		enqueuedSafeMoves = 0
		# we use this to keep track of whether this rule of thumb did anything, if not we don't count it as solved with rule of thumb
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				indexRow, indexCol = row + dy, col + dx
				if 0 <= indexRow < self.numRows and 0 <= indexCol < self.numCols:
					if self.gameBoard[indexRow][indexCol] is None and (indexCol, indexRow, AI.Action.UNCOVER) not in self.moveSet: 
						enqueuedSafeMoves += 1
						# prevent duplicates						
						self.moveSet.add((indexCol, indexRow, AI.Action.UNCOVER))

						if (indexCol, indexRow, AI.Action.FLAG) in self.moveSet:
							self.moveSet.remove((indexCol, indexRow, AI.Action.FLAG))
		
		return enqueuedSafeMoves
						


	def getAction(self, number: int) -> "Action Object":
		# check the number returned, update gameBoard accordingly, if it is -1, check if existing is None(unflagged) or -1(flagged), update accordingly
		if number != -1:			
			self.gameBoard[self.lastActionCoord[1]][self.lastActionCoord[0]] = number			
		else:
			if self.gameBoard[self.lastActionCoord[1]][self.lastActionCoord[0]] == -1:
				self.gameBoard[self.lastActionCoord[1]][self.lastActionCoord[0]] = None
			else:
				self.gameBoard[self.lastActionCoord[1]][self.lastActionCoord[0]] = -1


		

		self.uncoveredQueue.put((self.lastActionCoord[1], self.lastActionCoord[0]))
		self.frontierSet.remove((self.lastActionCoord[1], self.lastActionCoord[0]))

		self.visitedTiles.add((self.lastActionCoord[1], self.lastActionCoord[0]))
		self.enqueueAllUnexploredNeighbors(self.lastActionCoord[1], self.lastActionCoord[0])

		# print(f'Uncovered Frontier: {sorted(list(self.uncoveredQueue.queue))}')
		# print(f'Covered Frontier: {sorted(list(self.frontierSet))}')

		self.solve()

		
		# print(f'Safe moves:')
		# for move in self.moveSet:
		# 	print(move)


		
		# while not self.moveQueue.empty():
		while len(self.moveSet) > 0:
			# nx, ny, action = self.moveQueue.get()
			indexCol, indexRow, action = self.moveSet.pop()
			if self.gameBoard[indexRow][indexCol] != None:
				continue
			self.lastActionCoord = indexCol, indexRow
			self.unknownTilesLeft -= 1
			return Action(action, indexCol, indexRow)
		# default action
		return Action(AI.Action.LEAVE)	
	

		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################
