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

class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		self.totalMines = totalMines
		self.coveredTilesLeft = rowDimension*colDimension - 1

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
        
		self.enqueuedCoords = set()
		pass
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

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
			
	def applyRulesOfThumb(self):
		# print(list(self.frontierQueue.queue))
		recheckFrontier = Queue()
		# if rule of thumb can't be applied now, check it again later        
		while not self.frontierQueue.empty():
			x, y = self.frontierQueue.get()
			effective_label = self.effectiveLabel(x, y)
			num_unmarked_neighbors = self.numUnMarkedNeighbors(x, y)
			if effective_label == num_unmarked_neighbors:
				# All unmarked neighbors are mines
				self.markAllNeighborsAsMines(x, y)
			elif effective_label == 0:               
				self.enqueueSafeMoves(x, y)
			else:
				if effective_label > 0:
					# if the tile has been uncovered before
					# print(f'{x+1},{y+1} could not have rule of thumb applied, re check later')                
					recheckFrontier.put((x,y))
		self.frontierQueue = recheckFrontier

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
		self.applyRulesOfThumb()
		
		while not self.moveQueue.empty():
			nx, ny, action = self.moveQueue.get()
			if self.gameBoard[nx][ny] != None:
				continue
			self.lastActionCoord = nx, ny
			return Action(action, nx, ny)
		# default action
		return Action(AI.Action.LEAVE)	
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################
