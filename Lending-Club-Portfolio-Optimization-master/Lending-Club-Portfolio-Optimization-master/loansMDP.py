#Treats investing as an MDP, whereby each month you choose to invest in a give number of shares

from util.mdpUtil import MDP,ValueIteration
from databaseUtil import databaseAccess
import util.machineLearningUtil as mlUtil
from expectedReturns import expectedReturn as er
from tqdm import tqdm

import pickle
import copy
import random

PICKLE_DIRECTORY = "data/"
INVESTING_INCREMENT = 1 #Only allows you to invest in $1000 increments
NUM_POTENTIAL_LOANS = 20 #The constained sample of loans to examine


class portfolioState():
	#A class representing the state in the mdp
	def __init__(self,portfolio,cash,date):
		self.portfolio = portfolio 
		self.cash = cash
		self.date = date


	def strLoans(self):
		#Prints out the loans as string for easier debugging
		return tuple([(l["id"],a) for l,a in self.portfolio])

	def __hash__(self):
		#Hashes portfolioState 
		hashableLoans = tuple([(l["id"],a) for l,a in self.portfolio])
		return hash((hashableLoans,self.cash,self.date))

	def __eq__(self,other):
		#Two states are equal if they have the same portfolio, cash and date
		hashableLoansSelf = tuple([(l["id"],a) for l,a in self.portfolio])
		hashableLoansOther = tuple([(l["id"],a) for l,a in other.portfolio])
		return (hashableLoansSelf,self.cash,self.date) == (hashableLoansOther,other.cash,other.date)

	def __str__(self):
		return_string =  ("------------------------------------------------\n" 
						  + "Loans:" + str([(l["id"],a) for l,a in self.portfolio])
						  + '\n'+ "Cash: " +  str(self.cash) + '\n'
						  + "Date: " + str(self.date) + '\n' +  
						  "------------------------------------------------\n")

		return return_string

class loanPortfolioMDP(MDP):
	#An MDP for simulating 
	def __init__(self,loanTable,termLength,cash,startDate,endDate):
		self.db = databaseAccess()
		self.cash = cash
		self.sqlTable = loanTable
		self.termLength = termLength
		self.startDate = startDate
		self.endDate = endDate
		self.weights = pickle.load(open(PICKLE_DIRECTORY+'36'+"weights.p",'rb')) 
		self.columnNames = self.db.getColumnNames(self.sqlTable)
		self.loans = {}
		for i in range(self.db.monthsDifference(startDate,endDate)+1):
			dateString = self.db.dateToString(startDate)
			self.loans[startDate] = [self.dictRow(l) for l in self.db.get_loans_issued_in(self.sqlTable,dateString)][:NUM_POTENTIAL_LOANS]                 
			if startDate[0] is 12: startDate = (1,startDate[1]+1)
			else: startDate = (startDate[0]+1,startDate[1])

	def dictRow(self,row):
		#Converts a row from sql from a list to a dict
		return {c:r for c,r in zip(self.columnNames,row)} 

	def startState(self):
		#Start with no loans, starting cash and starting date
		return portfolioState([],self.cash,self.startDate)

	def discount(self):
		return 1

	def actions(self,state):
		'''
		An action represents the decision to invest in a single stock in a given month
		'''
		potentialLoans = self.loans[state.date]
		actions = [None]
		for l in potentialLoans:
			investment = INVESTING_INCREMENT
			while investment<=l['funded_amnt'] and investment<=state.cash:
				actions.append((l,investment))
				investment+=INVESTING_INCREMENT
		return actions

		
	def succAndProbReward(self,state,action):
		'''
		Returns all the possible successor states, where each successor state has the loans that 
		have defaulted removed from the domain
		'''

		if state.date == self.endDate: return []

		#Move time forward one month
		newStateTemplate = copy.deepcopy(state)
		if state.date[0] is 12: newStateTemplate.date = (1,state.date[1]+1)
		else: newStateTemplate.date = (state.date[0]+1,state.date[1])

		#If there an investment was made, add it to the portfolio
		if action !=None:
			loan,amount = action
			newStateTemplate.cash-=amount
			newStateTemplate.portfolio.append((loan,float(amount)/loan['funded_amnt']))

		def successorStatesRecursion(currIndex,reward,prob,currPortfolio,allSuccessors):
			'''
			Recursively creates all possible combinations of portfolios caused by default
			'''

			#Base Case - gone through every element in portfolio
			if currIndex == len(newStateTemplate.portfolio): 
				newState = portfolioState(currPortfolio,newStateTemplate.cash,newStateTemplate.date)
				allSuccessors.add((newState,prob,reward))
				return

			currPortfolio = copy.copy(currPortfolio)
			currLoan,percent = newStateTemplate.portfolio[currIndex]
			issue_date = currLoan["issue_d"]
			monthNum = self.db.monthsDifference(state.date,self.db.stringToDate(currLoan["issue_d"]))+1
			if monthNum > self.termLength: prob_default = 1
			else: prob_default = max(mlUtil.dotProduct(self.weights[monthNum],er.featureExtractor(currLoan)),0)
			#If loan defaults
			if prob_default>0:
				successorStatesRecursion(currIndex+1,reward,prob*prob_default,currPortfolio,allSuccessors)
			
			#If loan doesnt default and not over termlength, add to new portfolio
			if monthNum != self.termLength:
				currPortfolio = copy.copy(currPortfolio)
				currPortfolio.append((currLoan,percent))
				reward+=currLoan['installment']*percent
				successorStatesRecursion(currIndex+1,reward,prob*(1-prob_default),currPortfolio,allSuccessors)			
		
		all_successors = set()
		successorStatesRecursion(0,0,1.0,[],all_successors)
		return all_successors


class optimalMDPAnalysis():
	db = databaseAccess()

	@staticmethod 
	def actualSuccessor(state,action):
		'''
		Returns the successor that we know occured after the fact for any given state
		@params:
			- state: current state
			- action: action taken at that state
			- return: the succesor state
		'''
	
		#Add the new loan to the portfolio
		if action!=None:
			loan,amount = action
			state.cash-=amount
			state.portfolio.append((loan,float(amount)/loan['funded_amnt']))

		reward = 0 
		for loan,amount in state.portfolio:
			defDate =  optimalMDPAnalysis.db.stringToDate(loan["last_pymnt_d"])
			if defDate == state.date: 
				state.portfolio.remove((loan,amount))
			else: 
				reward += amount*loan['installment']
		if state.date[0] is 12: state.date = (1,state.date[1]+1)
		else: state.date = (state.date[0]+1,state.date[1])
		return state,reward

	@staticmethod 
	def optimalReturn(startingCash,startDate,endDate,tableName):
		"""
		Works out the optimal MDP return over a certain time period
		"""
		mdp = loanPortfolioMDP(tableName,36,startingCash,startDate,endDate)
		vi = ValueIteration()
		vi.solve(mdp,10)
		state = mdp.startState()
		total_reward = 0
		while state.date!=endDate:
			action = vi.pi[state]
			state,reward = optimalMDPAnalysis.actualSuccessor(state,action)
			total_reward+=reward
		return total_reward/startingCash

	@staticmethod 
	def optimalReturnEveryMonth(startingCash,tableName):
		'''
		Works out the optimal policy and follows that policy in the real world
		@params: 
			- startingCash: how much money you start with

		If it's runnning slowly, constrain INVESTING INCREMENT or numPotential Loans
		'''

		for year in tqdm(range(2011,2016)): 
			for month in tqdm(range(1,13)):
				startDate = (month,year)
				if year+3>2015: endDate = (12,2015)
				else: endDate = (month,year+3)
				print startDate,optimalMDPAnalysis.optimalReturn(startingCash,startDate,endDate,tableName)
			

if __name__ == "__main__":
	optimalMdpPortfolio(1)
	'''
	mdp = loanPortfolioMDP('TestThirtySix',36,1000,(1,2011),(1,2014))
	mdp.computeStates()
	vi = ValueIteration()
	vi.solve(mdp,100)
	print vi.pi[mdp.startState()]
	'''
