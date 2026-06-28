from databaseUtil import databaseAccess

class Baseline():

	def __init__(self, table, month):
		self.db = databaseAccess()
		self.table = table 
		self.loans = self.db.get_loans_issued_in(table,month)
		self.columnNames = self.db.getColumnNames(self.table)

	def dictRow(self,row):
		#Converts a row from sql from a list to a dict
		return {c:r for c,r in zip(self.columnNames,row)} 

	def percentReturn(self):
		return sum(self.dictRow(loan)["total_pymnt"]/self.dictRow(loan)["funded_amnt"]\
		       for loan in self.loans)/len(self.loans)

		for loan in self.loans: 
			loanDict = self.dictRow(loan)
			total_pymnt = laon["total_pymnt"]
			funded_amnt = self.db.col_name_list["funded_amnt"]

		return sum(map(lambda l : (l[total_pymnt] / l[funded_amnt]) / numLoans, self.loans))
		# return totalPayments / totalFunded

if __name__ == "__main__":
	for year in ["2011","2012","2013","2014","2015"]:
		for month in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]: 
			date = "{}-{}".format(month,year)
			b = Baseline("TestSixty",date)
			print date, b.percentReturn()





