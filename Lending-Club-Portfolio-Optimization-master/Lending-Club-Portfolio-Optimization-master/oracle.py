import csv,sys, Queue
import sqlite3 as lite 
import  databaseUtil
from tqdm import tqdm

TERMS = [36,60] #Possible lengths of loans

class oracle():
	db = databaseUtil.databaseAccess()
	def __init__(self,month,table):	
		self.loans = oracle.db.get_loans_issued_in(table,month)
		self.table = table
		self.columnNames = self.db.getColumnNames(self.table)

	def dictRow(self,row):
		#Converts a row from sql from a list to a dict
		return {c:r for c,r in zip(self.columnNames,row)}
	
	def choose_best_portfolio(self,initial_investment):
		'''
		Chooses the optimal portfolio of loans for a chosen issue date and term
		@params: 
			initial_investment: the $value of the initial investment (float)
			issue_date: the issue date of the loans (string) eg "Mar-2011"
			term: how long the loan is (36 or 60) in months
			return: a list of the loans invested in. [(return to date, funded amount, loan row)]
		'''
		pq = Queue.PriorityQueue()
		for l in self.loans:
			l = self.dictRow(l)
			total_payment = l["total_pymnt"]
			funded_amnt = l["funded_amnt"]
			percent_return_td  = total_payment/funded_amnt
			pq.put((-percent_return_td,l)) #negative to put highest returns at front of queue
		
		invested_loans = []
		invested = 0
		while invested<initial_investment:
			
			percent_return_td,l = pq.get()
			funded_amnt = l["funded_amnt"]
			#invest in part of loan to reach initial investment
			if funded_amnt+invested>initial_investment:
				funded_amnt = initial_investment - invested
			invested+=funded_amnt
			invested_loans.append((-percent_return_td,funded_amnt, l))
			if pq.qsize == 0: return None
		return invested_loans

	@staticmethod
	def average_return(investments):
		#Works out the overall return to date of a portfolio in the form [(return to date, funded amount, loan)] 
		return sum(x[0]*x[1] for x in investments)/sum(x[1] for x in investments)

if __name__ == "__main__":
	for year in ["2011","2012","2013","2014","2015"]:
		for month in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]: 
			date = "{}-{}".format(month,year)
			o = oracle(date,"TestSixty")
			portfolio = o.choose_best_portfolio(1)
			print date,oracle.average_return(portfolio)

