# multiAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattanDistance
from game import Directions
import random, util

from game import Agent

class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """


    def getAction(self, gameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices) # Pick randomly among the best

        "Add more of your code here if you want to"

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]

        "*** YOUR CODE HERE ***"
        foodDist=[manhattanDistance(newPos, food) for food in newFood.asList()]

        score = successorGameState.getScore()

        if len(foodDist)==0:
            return score

        closetFoodDist= min(foodDist)

        ghostDist=[]
        for ghost in newGhostStates:
            ghostDist.append((manhattanDistance(newPos, ghost.getPosition()), ghost.scaredTimer))

        closetGhost= min(ghostDist)
        if action=='Stop' or (closetGhost[0]==0 and closetGhost[1]==0):
            return -float('inf')

        return score + closetGhost[0]/(10*closetFoodDist)  

def scoreEvaluationFunction(currentGameState):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """

    def getAction(self, gameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.

        Here are some method calls that might be useful when implementing minimax.

        gameState.getLegalActions(agentIndex):
        Returns a list of legal actions for an agent
        agentIndex=0 means Pacman, ghosts are >= 1

        gameState.generateSuccessor(agentIndex, action):
        Returns the successor game state after an agent takes an action

        gameState.getNumAgents():
        Returns the total number of agents in the game

        gameState.isWin():
        Returns whether or not the game state is a winning state

        gameState.isLose():
        Returns whether or not the game state is a losing state
        """
        "*** YOUR CODE HERE ***"

        def minimax(agentIndex, depth, gameState):
            if gameState.isWin() or gameState.isLose() or self.depth==depth:
                return (self.evaluationFunction(gameState), Directions.WEST)
            elif agentIndex==0:
                successors = [(minimax(1, depth, gameState.generateSuccessor(0, action))[0], action) for action in gameState.getLegalActions(0)]
                return max(successors)
            else:
                nextAgentIndex = (agentIndex + 1)%gameState.getNumAgents()
                if nextAgentIndex==0:
                    depth += 1
                successors = [(minimax(nextAgentIndex, depth, gameState.generateSuccessor(agentIndex, action))[0], action) for action in gameState.getLegalActions(agentIndex)]
                return min(successors)

        minimax_val, action = minimax(0, 0, gameState)
        # print("Val:", minimax_val)
        # print("Action", action)

        return action


class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        "*** YOUR CODE HERE ***"

        def alphaBetaPruning(agentIndex, depth, gameState, a, b):
            if gameState.isWin() or gameState.isLose() or self.depth==depth:
                return (self.evaluationFunction(gameState), Directions.WEST)
        
            elif agentIndex==0:
                v = float('-inf')
                best_action = Directions.WEST

                for action in gameState.getLegalActions(0):
                    max_val = alphaBetaPruning(1, depth, gameState.generateSuccessor(0, action), a, b)[0]

                    if max_val>v:
                        v = max_val
                        best_action = action

                    if v>b:
                        return (v, best_action)

                    a = max(a, v)

                return (v, best_action)

            else:
                nextAgentIndex = (agentIndex + 1)%gameState.getNumAgents()
                if nextAgentIndex==0:
                    depth += 1

                v = float('inf')
                best_action = Directions.WEST

                for action in gameState.getLegalActions(agentIndex):
                    min_val = alphaBetaPruning(nextAgentIndex, depth, gameState.generateSuccessor(agentIndex, action), a, b)[0]

                    if v>min_val:
                        v = min_val
                        best_action = action                    

                    if v<a:
                        return (v, best_action)

                    b = min(b, v)

                return (v, best_action)

        alpha = float('-inf')
        beta = float('inf')
        alphaBetaPruning_val, action = alphaBetaPruning(0, 0, gameState, alpha, beta)
        # print(alphaBetaPruning_val)
        return action 

class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def getAction(self, gameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        "*** YOUR CODE HERE ***"

        def expectimax(agentIndex, depth, gameState):
            if gameState.isWin() or gameState.isLose() or self.depth==depth:
                return (self.evaluationFunction(gameState), Directions.SOUTH)
            elif agentIndex==0:
                successors = [(expectimax(1, depth, gameState.generateSuccessor(0, action))[0], action) for action in gameState.getLegalActions(0)]
                return max(successors)
            else:
                nextAgentIndex = (agentIndex + 1)%gameState.getNumAgents()
                if nextAgentIndex==0:
                    depth += 1
                successors = [expectimax(nextAgentIndex, depth, gameState.generateSuccessor(agentIndex, action))[0] for action in gameState.getLegalActions(agentIndex)]
                return (sum(successors)/len(successors), Directions.SOUTH)

        expectimax_val, action = expectimax(0, 0, gameState)
        # print("Val:", expectimax_val)
        # print("Action", action)
        return action


def betterEvaluationFunction(currentGameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    DESCRIPTION: <write something here so we know what you did>
    """
    "*** YOUR CODE HERE ***"

    pacmanPos = currentGameState.getPacmanPosition()
    foodList = currentGameState.getFood().asList()
    ghostStates = currentGameState.getGhostStates()
    ghostScaredTimes = [ghostState.scaredTimer for ghostState in ghostStates]
    
    def ghost_score(pacmanPos, weight):
        score = 0
        closestGhost = [util.manhattanDistance(pacmanPos, ghost.getPosition()) for ghost in currentGameState.getGhostStates()]       
        if len(closestGhost)!=0:
            closestGhostDist = min(closestGhost)
            totalScaredTime = sum(ghostScaredTimes)

            if closestGhostDist>=1:
                if totalScaredTime<0:
                    score -= float(weight/closestGhostDist)
                else:
                    score += float(weight/closestGhostDist)

        return score

    def capsule_score(pacmanPos, weight):
        score = 0
        capsules = currentGameState.getCapsules()
        if len(capsules)!=0:
            closestCapsule = min([util.manhattanDistance(pacmanPos, capsulePos) for capsulePos in capsules])
            score += float(weight/closestCapsule)

        return score

    def food_score(pacmanPos, weight):
        score = 0
        closestFood = min([util.manhattanDistance(pacmanPos, foodPos) for foodPos in foodList])
        score += float(weight/closestFood) - len(foodList) 

        return score     

    if currentGameState.isWin():
        return 100000
    
    for ghost in ghostStates:
        if ghost.getPosition()==pacmanPos and ghost.scaredTimer==0:
            return -100000        

    ghost_weight = 1
    food_weight = 1
    capsule_weight = 100

    return currentGameState.getScore() + ghost_score(pacmanPos, ghost_weight) + capsule_score(pacmanPos, capsule_weight) + food_score(pacmanPos, food_weight)


# Abbreviation
better = betterEvaluationFunction
