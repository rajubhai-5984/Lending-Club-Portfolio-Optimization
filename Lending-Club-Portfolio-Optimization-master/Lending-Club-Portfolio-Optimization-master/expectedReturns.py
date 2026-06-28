'''
The expected returns class predicts the expected return of a loan and the 
variance of that loan. It does so by: 
	- predicting the risk of default in any given month for a loan using stochastic gradient descent
	- Using the risk of default to run multiple monte carlo simulations, thereby learning the 
	  expected return and the variance of the return
'''
DESC_WORDS = ["credit", "lower", "payment", "month", "interest", "bills", "thank", "current", "start", \
"person", "medic", "higher", "great", "always", "about", "business", "card", "never", "other", "lower"]

import collections,random, csv
import util.machineLearningUtil as mlUtil
import databaseUtil as dbUtil
import datetime
from tqdm import tqdm
import cPickle as pickle

PICKLE_DIRECTORY = "data/"
TEST_ERROR_DIRECTORY = "data/"

class expectedReturn(mlUtil.gradientDescent):

	def __init__(self, termLength, sqlTrainTable,sqlTestTable):
		self.termLength = termLength #Length of loan - 36 or 60
		self.sqlTable = sqlTrainTable #Name of sql table
		self.testTable = sqlTestTable
		self.weights = {} #weights for each month
		self.db = dbUtil.databaseAccess()
		self.columnNames = self.db.getColumnNames(self.sqlTable)
	
	def dictRow(self,row):
		#Converts a row from sql from a list to a dict
		return {c:r for c,r in zip(self.columnNames,row)} 

	def extractTrainExamples(self,monthNum):
		'''
		Extracts the relevant rows from a sql table 
		@params: 
			- monthNum: the month in which you want to predict risk of default
			- return: whether they defaulted in that month (y), all the relevant pieces of data for that month (x)
		'''
		all_rows = self.db.con.execute("SELECT * FROM {}".format(self.sqlTable))
		return_list = []
		
		for row in all_rows:
			dictRow = self.dictRow(row)
			if(dictRow["loan_status"] == "Charged Off"):	
				issDate = self.db.stringToDate(dictRow["issue_d"])
				defDate =  self.db.stringToDate(dictRow["last_pymnt_d"])
				defaultMonthNum = self.db.monthsDifference(issDate,defDate)
				if(defaultMonthNum>=monthNum): #If the loan has not already defaulted, add to trainExamples
					if defaultMonthNum == monthNum: yVal = 1
					else: yVal = 0
					return_list.append((yVal,dictRow))
			else: return_list.append((0,dictRow))
		return return_list

	@staticmethod
	def featureExtractor(dictRow):
		'''
		Converts dictRow into a series of features for machine learning
		'''
		gradeInt = dbUtil.databaseAccess.subgradeToInt(dictRow["sub_grade"]) 
		empLength = dbUtil.databaseAccess.numYearsEmployedToInt(dictRow["emp_length"])
		features = {"dti":dictRow["dti"],"grade":gradeInt,"emp_length":empLength}
		for word in DESC_WORDS:
			features[word] = int(dictRow[word])
		return features

		
	def learnWeights(self,updateWeights,numIters,eta):
		'''
		Learns the weights for probabilty of default in any given month
		@params
			- updateWeights: the function to update the weights updateWeights(weights,phiX,y,eta)
			- numIters: the number of iterations to run the gradient descent
			- eta: the step size
		'''
		for monthNum in tqdm(range(1,self.termLength+1),desc="Learning Weights"):
			trainExamples = self.extractTrainExamples(monthNum)
			#Learns weights for a particular month
			self.weights[monthNum] = self.stochasticGradientDescent(trainExamples,self.featureExtractor,\
																	updateWeights,numIters,eta)
		#Pickles the weights for later use
		pickle.dump(self.weights,open(PICKLE_DIRECTORY+str(self.termLength)+"weights.p","wb"))

	def calculateSingleExpReturnAndVar(self,row,numIters):
		'''
		By creating a Monte Carlo simulation of loan, we can estimate the expected return of the loan
		and the variance of the returns
		@params:
			- row: the row from sql table  
			- numIters: the number of iterations to simulate the loan
		'''
		#If the loan hasnt reached maturity, calculate expected returns to date
		may2016 = (5,2016)
		issDate = self.db.stringToDate(row["issue_d"])
		loanMonthsCompleted = min(self.termLength,self.db.monthsDifference(may2016,issDate))


		allReturns = []
		#Simulate the returns if the loan happened @numIters times
		for _ in range(numIters):
			curr_return = 0 #Return for current iteration
			for monthNum in range(1,loanMonthsCompleted+1):
				probDefault = mlUtil.dotProduct(self.featureExtractor(row),self.weights[monthNum])
				if(random.random()<probDefault):
					allReturns.append(curr_return)
					break
				curr_return+=row["installment"]
				if(monthNum == loanMonthsCompleted-1): allReturns.append(curr_return)
		
		#Calculate the expected return and the variance of that loan given the simulation
		if(row["funded_amnt"]==0): return None,None
		expReturn = (sum(allReturns)/row["funded_amnt"])/len(allReturns)
		variance = sum((x/row["funded_amnt"] - expReturn)**2 for x in allReturns)/(len(allReturns)-1) #-1 for sample
		return expReturn,variance

	def calculateAllExpReturnAndVar(self,updateWeights,numItersGD,eta,numItersMC,usePickle=False):
		'''
		Runs a monte carlo simulation for every single loan with term of self.termLength to calculate expected return
		and variance. Then updates the values in the sql testTable
		@params: 
			- updateWeights: the function to update the weights updateWeights(weights,phiX,y,eta)
			- numItersGD: the number of iterations to run the gradient descent
			- eta: the step size
			- numItersMC: the number of iterations for monte carlo simulation
			- use most recently pickled version or not...
		'''
		if usePickle: self.weights = pickle.load(open(PICKLE_DIRECTORY+str(self.termLength)+"weights.p",'rb'))                 
		else: self.learnWeights(updateWeights,numItersGD,eta)
		
		self.db.cur.execute("SELECT Count(*) FROM {}".format(self.testTable))
		rowNums = self.db.cur.fetchone()[0]
		all_rows = self.db.con.execute("SELECT * FROM {}".format(self.testTable))

		
		for row in tqdm(all_rows,total=rowNums,desc="Calculating Expected Return and Variance"):
			dictRow = self.dictRow(row)
			expReturn, var = self.calculateSingleExpReturnAndVar(dictRow,numItersMC)
			self.db.updateTableValue(self.testTable,dictRow,"exp_r",expReturn)
			self.db.updateTableValue(self.testTable,dictRow,"var",var)
			self.db.con.commit()

	def testError(self):
		'''
		Caclulates the test error on the machine learning algorithm. Outputs a csv where one column is chance default
		and the other is whether it actually defaulted
		'''
		try: 
			self.weights = pickle.load(open(PICKLE_DIRECTORY+str(self.termLength)+"weights.p",'rb'))                 
		except: 
			raise 
		
		errorFileName = TEST_ERROR_DIRECTORY+str(self.termLength)+'testError.csv'
		with open(errorFileName,'wb+') as csvfile:
			csvwriter = csv.writer(csvfile)
			for monthNum in tqdm(range(1,self.termLength+1),desc="FindingTestError"):
				trainExamples = self.extractTrainExamples(monthNum)
				for row in trainExamples: 
					didDefault = row[0] #1 if defaulted, 0 if didnt default
					probDefault = mlUtil.dotProduct(self.featureExtractor(row[1]),self.weights[monthNum])
					csvwriter.writerow([didDefault,probDefault])
				
				


def testMonteCarlo():
	term_5 = expectedReturn(5,'test',lambda x: (0,x["features"]))
	term_5.weights = {x:{"a":0.1,"b":0.2} for x in range(5)}
	row = {"features":{"a":0.1,"b":0.2},"installment":1}
	print term_5.calculateSingleExpReturnAndVar(row,1000)

if __name__ == "__main__":
	

	e = expectedReturn(36,"TrainThirtySix","TestThirtySix")	
	e.testError()
	#e.calculateAllExpReturnAndVar(e.leastSquares,10,0.0001,100,True)
	
