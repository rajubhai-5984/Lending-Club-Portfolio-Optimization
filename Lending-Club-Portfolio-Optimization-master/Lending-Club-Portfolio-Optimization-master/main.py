'''
Allows the user to run everything from start to finish
'''
import sys, loansMDP,csv, optimalPortfolio, pickle
from expectedReturns import expectedReturn
from kMeansCov import kMeans
from optimalPortfolio import optimalPortfolio as op
from databaseUtil import databaseAccess
from loansMDP import optimalMDPAnalysis
from baseline import Baseline
from oracle import oracle
import pickle
from tqdm import tqdm

PICKLE_DIRECTORY = "/data"


def learnExpRVar(loanTerm):
	#Learns the expected return and variance for each of the loans 
	if loanTerm == '60':
		e = expectedReturn(60,"TrainSixty","TestSixty")
	else:
		e = expectedReturn(36,"TrainThirtySix","TestThirtySix")
	e.calculateAllExpReturnAndVar(e.leastSquares,10,0.0001,100,False)

def learnCov(loanTerm):
	#Learns the covariance for every loan
	db = databaseAccess()
	if loanTerm == '60':k = kMeans(db,"TestSixty", False)
	else: k = kMeans(db,"TestThirtySix", False)

def outputReturnsCSV(loanTerm):
	'''
	Creates a csv with month by month returns for all of the different methods we have created
	@params:
		-loanTerm: Either 36 or 60 depending on how long you want the loans to be
	'''

	if loanTerm is "36": 
		table = "TestThirtySix"
		termLength = 36
	else: 
		table = "TestSixty"
		termLength = 60
	covariances = pickle.load(open(PICKLE_DIRECTORY+str(termLength)+"covariances.p",'rb'))                 
	with open("results.csv","wb") as csvfile:
		writer = csv.writer(csvfile,delimiter=",")
		headers = ["Date","Baseline","MDP","Optimal Sharpe","Oracle","Expected Sharpe"]
		writer.writerow(headers)
		for year in tqdm(["2011","2012","2013","2014","2015"],desc = "Calculating Returns"):
			for i,month in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]): 
				date = "{}-{}".format(month,year)
				starting_cash = 1 #Set cash equal to one so no need to worry about investing $1000 in a $100 loan

				#Calculate Baseline
				b = Baseline(table,date)
				bReturn = b.percentReturn()
				
				#Calculate sharpes optimal
				possLoans = optimalPortfolio.getLoansFromTable(table,date)
				p = op(possLoans,covariances,0)	
				p.findOptimalPortfolio(10,0.01)
				pReturn = p.calculateActualReturn()
				expP = p.expectedReturn()

				#Calculate Oracle
				o = oracle(date,table)
				portfolio = o.choose_best_portfolio(1)
				oReturn = oracle.average_return(portfolio)

				#Calculate MDP
				startDate = (i+1,int(year)) #i+1 to have Jan = 1, not Jan = 0 
				termYears = int(loanTerm)/12
				if int(year)+termYears>2015: endDate = (12,2015)
				else: endDate = (i+1,int(year)+termYears)
				mReturn = optimalMDPAnalysis.optimalReturn(starting_cash,startDate,endDate,table)

				row = (date, bReturn,mReturn,pReturn,oReturn,expP)
				writer.writerow(row)


def getUserInput():
	args = sys.argv[1:]
	if len(args) == 0: return "36"
	if  not args[0] in ["36","60"]:
		raise Exception("First argument must be term length - 36 or 60")
	return args[0]

if __name__ == "__main__":
	term =  getUserInput()
	learnExpRVar(term)
	learnCov(term)
	outputReturnsCSV(term)



