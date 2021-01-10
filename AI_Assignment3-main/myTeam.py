# myTeam.py
# ---------
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


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

from util import nearestPoint
import distanceCalculator


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveMyAgent', second = 'MixedMyAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########


class MyAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.initPosition = gameState.getAgentState(self.index).getPosition()
        self.presentCoordinates = gameState.getAgentState(self.index).getPosition()
        self.legalActions = gameState.getLegalActions(self.index)
        self.legalActions.remove(Directions.STOP)

        self.centre_x = (gameState.data.layout.width - 2) // 2   if self.red else (gameState.data.layout.width - 2) // 2 +1
        self.centre_y = (gameState.data.layout.height - 2) // 2
        self.width = gameState.data.layout.width
        self.height = gameState.data.layout.height

        self.boundary_gates = [(self.centre_x, i) for i in range(1, self.height-1) if not gameState.hasWall(self.centre_x, i) ] 
        total_entry_points = len(self.boundary_gates)
        entry_point = (total_entry_points//2) if total_entry_points%2==0 else (total_entry_points-1)//2
        self.initialTarget = [self.boundary_gates[entry_point]]
        self.mid_boundary=entry_point

    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action) 
        position = successor.getAgentState(self.index).getPosition() 
        foodList = self.getFood(successor).asList() 
        features['nextStateScore'] = self.getScore(successor) 
        features['UNKNOWN']= 1 if successor.getAgentState(self.index).isPacman else 0
        features['howFarIsFood'] = min([self.getMazeDistance(position, food) for food in foodList]) if foodList else 0
        disToGhost = [self.getMazeDistance(position , successor.getAgentState(e).getPosition()) for e in self.getOpponents(successor) if not successor.getAgentState(e).isPacman and successor.getAgentState(e).getPosition() != None]     
        if len(disToGhost)==0:
            return features
        minDisToGhost = min(disToGhost)
        features['howFarIsGhost'] = 0 if minDisToGhost>=5 else  minDisToGhost + features['nextStateScore']
        features['goBack']=0
        return features
    
    def getWeights(self, gameState, action):
        weights = {'distancesToGhost' :2150, 'UNKNOWN' :0, 'capsule': 50, 'howFarIsFood': -8, 'nextStateScore': 202, 'goBack': -500}

        successor = self.getSuccessor(gameState, action) 
        enemyIndices = self.getOpponents(successor)
        enemyAgents = [successor.getAgentState(enemyIndex) for enemyIndex in enemyIndices]
        enemyScared = [enemy.scaredTimer > 0 for enemy in enemyAgents if not enemy.isPacman]        
        if (len(enemyScared) > 0 and all(enemyScared)) or successor.getAgentState(self.index).isPacman == False:
        # if len(enemyScared) > 0 and all(enemyScared):   
            weights['distancesToGhost'] = 0

        if self.attack and self.shouldReturn:
            weights['UNKNOWN'] = 3010            

        return weights 



class OffensiveMyAgent(MyAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)        
        self.presentCoordinates = (-5 ,-5)
        # self.idleTime = 0
        self.attack = False
        # self.lastFood = []
        self.presentFoodList = []
        self.shouldReturn = False
        self.capsulePower = False
        self.targetMode = None
        self.foodConsumed = 0
        self.initialTarget = []
        self.flag = 0
        self.currentCapsule = 0
        self.lastCapsule = 0
        
        self.currentCapsule = []
        self.lastCapsule = []
        self.currentFood = []
        self.lastFood = []
        self.currentEnemies = []
        self.foodConsumed = 0
        self.idleTime = 0
        self.hasCapsule = 0

        #old
        self.prevCapsuleLeft =0
        self.capsuleLeft=0
        self.eatenFood=0
        self.counter=0       

    def chooseAction(self, gameState):      
        self.presentCoordinates = gameState.getAgentState(self.index).getPosition()
        self.legalActions = gameState.getLegalActions(self.index)
        self.legalActions.remove(Directions.STOP)
        
        if self.presentCoordinates == self.initPosition:
            self.flag = 1
            self.idleTime=0
            self.boundary_target = random.choice(self.boundary_gates)
            if self.mid_boundary>0 : self.boundary_target = random.choice(self.boundary_gates[:self.mid_boundary])

            # self.boundary_target = random.choice(self.boundary_gates[:self.mid_boundary])
            actionValues = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.boundary_target), action)for action in self.legalActions]
            bestActionVal = min(actionValues)
            finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
            ret = random.choice(finalActions)
            if ret==None:
                return Directions.STOP
            return ret

        if self.presentCoordinates in self.boundary_gates:
            self.flag = 0
            self.currentFood = self.getFood(gameState).asList()
            self.currentEnemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() != None]
            if gameState.isOnRedTeam(self.index) : 
                self.currentCapsule = gameState.getBlueCapsules()
            else : 
                self.currentCapsule = gameState.getRedCapsules()

            minFoodDistance=None
            minGhostDistance=None

            if(len(self.currentFood)) : minFoodDistance = min([ self.getMazeDistance(self.presentCoordinates, food) for food in self.currentFood])
            if(len(self.currentEnemies)) : minGhostDistance = min([self.getMazeDistance(self.presentCoordinates, a.getPosition()) for a in self.currentEnemies])
            
            if minGhostDistance==None:
                gates = [(self.getMazeDistance(self.presentCoordinates, gate), gate) for gate in self.boundary_gates]
                nearest =  min(gates)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret

            elif minFoodDistance==None:
                gates = [(self.getMazeDistance(self.presentCoordinates, gate), gate) for gate in self.boundary_gates]
                nearest =  min(gates)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret

            if minGhostDistance <=4:
                gates = [(self.getMazeDistance(self.presentCoordinates, gate), gate) for gate in self.boundary_gates]
                nearest =  min(gates)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret
            else :
                food = [pos for pos in self.currentFood if self.getMazeDistance(self.presentCoordinates, pos)==minFoodDistance][0]
                distanceToTarget = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), food), food) for action in self.legalActions]
                nearest=min(distanceToTarget)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret



        if gameState.getAgentState(self.index).isPacman :
            pass
        else :
            # self.boundary_target = random.choice(self.boundary_gates[:self.mid_boundary])
            actionValues = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.boundary_target), action)for action in self.legalActions]
            bestActionVal = min(actionValues)
            finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
            ret = random.choice(finalActions)
            if ret==None:
                return Directions.STOP
            return ret

        if self.flag==0:
            self.currentFood = self.getFood(gameState).asList()
            self.currentEnemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() != None]
            if gameState.isOnRedTeam(self.index) : 
                self.currentCapsule = gameState.getBlueCapsules()
            else : 
                self.currentCapsule = gameState.getRedCapsules()

            if len(self.lastFood) == len(self.currentFood):
                self.idleTime+=1
            if len(self.lastFood)> len(self.currentFood):
                self.foodConsumed+=1
                self.idleTime=0
                self.capsulePower = False
            if len(self.lastCapsule)> len(self.currentCapsule):
                self.capsulePower = True
                if not gameState.getAgentState(self.index).isPacman: self.foodConsumed = 0
                self.foodConsumed = 0
                self.hasCapsule=40
            if self.foodConsumed>=1 :
                self.shouldReturn = True

            self.lastFood=self.currentFood
            self.lastCapsule=self.currentCapsule
            if self.hasCapsule>0 : self.hasCapsule-=1
            if self.idleTime > 20: self.attack = True
            else: self.attack = False

            closestEnemy = float('+inf')
            enemiesGhost = [gameState.getAgentState(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() != None and gameState.getAgentState(i).scaredTimer == 0 ]
            if len(enemiesGhost) > 0: closestEnemy = min([self.getMazeDistance(self.presentCoordinates, a.getPosition()) for a in enemiesGhost])
            if closestEnemy <= 5: self.capsulePower = False

            if self.capsulePower == True:
                if len(self.currentFood )==0 or self.foodConsumed >= 5:
                    return_gates_dist = [self.getMazeDistance(self.presentCoordinates, pos) for pos in self.boundary_gates]
                    nearest = min(return_gates_dist)
                    self.targetMode = [gate for gate in return_gates_dist if self.getMazeDistance(self.presentCoordinates, gate)==nearest][0]
        
                else:
                    foods_dist = [(self.getMazeDistance(self.presentCoordinates, pos), pos) for pos in self.currentFood]
                    nearest_food = min(foods_dist)
                    self.targetMode = nearest_food[1]

                actionValues = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.targetMode), action)for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret
            else:
                self.foodConsumed = 0
                distanceToTarget = []
                maxIters = 23
                for a in self.legalActions:
                    nextState = gameState.generateSuccessor(self.index, a)
                    value = 0
                    for i in range(maxIters):
                        depth =20
                        state = nextState.deepCopy()
                        while depth>0:
                            possibleActions = state.getLegalActions(self.index)
                            possibleActions.remove(Directions.STOP)
                            oppositeDirection = Directions.REVERSE[state.getAgentState(self.index).configuration.direction]
                            if len(possibleActions) >=2 and oppositeDirection in possibleActions:
                                possibleActions.remove(oppositeDirection)
                            action = random.choice(possibleActions)
                            state = state.generateSuccessor(self.index, action)
                            depth-=1
                        value+= self.evaluate(state, Directions.STOP)
                    distanceToTarget.append((value, a))

                best = max(distanceToTarget)
                finalActions = [pair[1] for pair in distanceToTarget if best == pair]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret



class MixedMyAgent(MyAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)        
        self.presentCoordinates = (-5 ,-5)
        # self.idleTime = 0
        self.attack = False
        # self.lastFood = []
        self.presentFoodList = []
        self.shouldReturn = False
        self.capsulePower = False
        self.targetMode = None
        self.foodConsumed = 0
        self.initialTarget = []
        self.flag = 0
        self.currentCapsule = 0
        self.lastCapsule = 0
        
        self.currentCapsule = []
        self.lastCapsule = []
        self.currentFood = []
        self.lastFood = []
        self.currentEnemies = []
        self.foodConsumed = 0
        self.idleTime = 0
        self.hasCapsule = 0

        #old
        self.prevCapsuleLeft =0
        self.capsuleLeft=0
        self.eatenFood=0
        self.counter=0

        self.iter = 0
        self.targetPos = None
        self.lookOutPoints = []
        self.prevFood = []          

    def chooseAction(self, gameState):   

        enemyIndices = self.getOpponents(gameState)
        enemyAgents = [gameState.getAgentState(enemyIndex) for enemyIndex in enemyIndices] 
        enemyIsPacman = [enemy.isPacman for enemy in enemyAgents if enemy.getPosition()!=None]

        if any(enemyIsPacman):
            currPos = gameState.getAgentPosition(self.index)
            if currPos == self.targetPos:
                self.targetPos = None
            
            enemyIndices = self.getOpponents(gameState)
            enemyAgents = [gameState.getAgentState(enemyIndex) for enemyIndex in enemyIndices]
            enemyAttackingPositions = [enemy.getPosition() for enemy in enemyAgents if enemy.isPacman and enemy.getPosition()!=None]

            if len(enemyAttackingPositions)>0:
                invader_dist = [(self.getMazeDistance(enemyPos, currPos), enemyPos) for enemyPos in enemyAttackingPositions]
                self.targetPos = min(invader_dist)[1]
                agentActions = [action for action in gameState.getLegalActions(self.index) if action!=Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction] and action!=Directions.STOP]  
                
                if len(agentActions)>0:
                    self.iter += 1
                    if self.iter > 4:
                        agentActions.append(Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]) 
                else:
                    self.iter = 0  
                    agentActions.append(Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction])                     

                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.targetPos) for action in agentActions]
                bestActionVal = min(actionValues)

                finalActions = [agentActions[i] for i in range(len(agentActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret   

        self.presentCoordinates = gameState.getAgentState(self.index).getPosition()
        self.legalActions = gameState.getLegalActions(self.index)
        self.legalActions.remove(Directions.STOP)
        
        if self.presentCoordinates == self.initPosition:
            self.flag = 1
            self.idleTime=0
            self.boundary_target = random.choice(self.boundary_gates)
            if self.mid_boundary<len(self.boundary_gates) : self.boundary_target = random.choice(self.boundary_gates[self.mid_boundary:])

            # self.boundary_target = random.choice(self.boundary_gates[self.mid_boundary:])
            actionValues = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.boundary_target), action)for action in self.legalActions]
            bestActionVal = min(actionValues)
            finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
            ret = random.choice(finalActions)
            if ret==None:
                return Directions.STOP
            return ret

        if self.presentCoordinates in self.boundary_gates:
            self.flag = 0
            self.currentFood = self.getFood(gameState).asList()
            self.currentEnemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() != None]
            if gameState.isOnRedTeam(self.index) : 
                self.currentCapsule = gameState.getBlueCapsules()
            else : 
                self.currentCapsule = gameState.getRedCapsules()

            minFoodDistance=None
            minGhostDistance=None

            if(len(self.currentFood)) : minFoodDistance = min([ self.getMazeDistance(self.presentCoordinates, food) for food in self.currentFood])
            if(len(self.currentEnemies)) : minGhostDistance = min([self.getMazeDistance(self.presentCoordinates, a.getPosition()) for a in self.currentEnemies])
            
            if minGhostDistance==None:
                gates = [(self.getMazeDistance(self.presentCoordinates, gate), gate) for gate in self.boundary_gates]
                nearest =  min(gates)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret

            elif minFoodDistance==None:
                gates = [(self.getMazeDistance(self.presentCoordinates, gate), gate) for gate in self.boundary_gates]
                nearest =  min(gates)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret

            if minGhostDistance <=4:
                gates = [(self.getMazeDistance(self.presentCoordinates, gate), gate) for gate in self.boundary_gates]
                nearest =  min(gates)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret
            else :
                food = [pos for pos in self.currentFood if self.getMazeDistance(self.presentCoordinates, pos)==minFoodDistance][0]
                distanceToTarget = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), food), food) for action in self.legalActions]
                nearest=min(distanceToTarget)
                actionValues = [self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearest[1])for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret

        if gameState.getAgentState(self.index).isPacman :
            pass
        else :
            actionValues = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.boundary_target), action)for action in self.legalActions]
            bestActionVal = min(actionValues)
            finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
            ret = random.choice(finalActions)
            if ret==None:
                return Directions.STOP
            return ret
        if self.flag==0:
            self.currentFood = self.getFood(gameState).asList()
            self.currentEnemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() != None]
            if gameState.isOnRedTeam(self.index) : 
                self.currentCapsule = gameState.getBlueCapsules()
            else : 
                self.currentCapsule = gameState.getRedCapsules()

            if len(self.lastFood) == len(self.currentFood):
                self.idleTime+=1
            if len(self.lastFood)> len(self.currentFood):
                self.foodConsumed+=1
                self.idleTime=0
                self.capsulePower = False
            if len(self.lastCapsule)> len(self.currentCapsule):
                self.capsulePower = True
                if not gameState.getAgentState(self.index).isPacman: self.foodConsumed = 0
                self.foodConsumed = 0
                self.hasCapsule=40
            if self.foodConsumed>=2 :
                self.shouldReturn = True

            self.lastFood=self.currentFood
            self.lastCapsule=self.currentCapsule
            if self.hasCapsule>0 : self.hasCapsule-=1
            if self.idleTime > 20: self.attack = True
            else: self.attack = False

            closestEnemy = float('+inf')
            enemiesGhost = [gameState.getAgentState(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() != None and gameState.getAgentState(i).scaredTimer == 0 ]
            if len(enemiesGhost) > 0: closestEnemy = min([self.getMazeDistance(self.presentCoordinates, a.getPosition()) for a in enemiesGhost])
            if closestEnemy <= 5: self.capsulePower = False

            if self.capsulePower == True:
                if len(self.currentFood )==0 or self.foodConsumed >= 5:
                    return_gates_dist = [self.getMazeDistance(self.presentCoordinates, pos) for pos in self.boundary_gates]
                    nearest = min(return_gates_dist)
                    self.targetMode = [gate for gate in return_gates_dist if self.getMazeDistance(self.presentCoordinates, gate)==nearest][0]
        
                else:
                    foods_dist = [(self.getMazeDistance(self.presentCoordinates, pos), pos) for pos in self.currentFood]
                    nearest_food = min(foods_dist)
                    self.targetMode = nearest_food[1]

                actionValues = [(self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), self.targetMode), action)for action in self.legalActions]
                bestActionVal = min(actionValues)
                finalActions = [self.legalActions[i] for i in range(len(self.legalActions)) if actionValues[i]==bestActionVal]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret
            else:
                
                self.foodConsumed = 0
                distanceToTarget = []
                maxIters = 23
                for a in self.legalActions:
                    nextState = gameState.generateSuccessor(self.index, a)
                    value = 0
                    for i in range(maxIters):
                        depth = 20
                        state = nextState.deepCopy()
                        while depth>0:
                            possibleActions = state.getLegalActions(self.index)
                            possibleActions.remove(Directions.STOP)
                            oppositeDirection = Directions.REVERSE[state.getAgentState(self.index).configuration.direction]
                            if len(possibleActions) >=2 and oppositeDirection in possibleActions:
                                possibleActions.remove(oppositeDirection)
                            action = random.choice(possibleActions)
                            state = state.generateSuccessor(self.index, action)
                            depth-=1
                        value+= self.evaluate(state, Directions.STOP)
                    distanceToTarget.append((value, a))

                best = max(distanceToTarget)
                finalActions = [pair[1] for pair in distanceToTarget if best == pair]
                ret = random.choice(finalActions)
                if ret==None:
                    return Directions.STOP
                return ret