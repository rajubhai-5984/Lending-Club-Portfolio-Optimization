#Series of classes/functions for accesing the database
import sqlite3 as lite
import sys,csv,re, random
import sys,csv
import string
import re
from tfidf import TFIDF_Extractor
from tqdm import tqdm

TABLE = 'loan'
DB_NAME = 'database.sqlite'

DESC_WORDS = ["credit", "lower", "payment", "month", "interest", "bills", "thank", "current", "start", \
"person", "medic", "higher", "great", "always", "about", "business", "card", "never", "other", "lower"]
STR_TYPES = ['CHARACTER(20)', 'VARCHAR(255)', 'VARYING CHARACTER(255)', 'NCHAR(55)', 'NATIVE CHARACTER(70)', 'NVARCHAR(100)', 'TEXT']
def set_up_db():
	'''
	Accesses the sql database
	@return: 
		- returns cursor and connection 
	'''
	con = None
	try:
	    con = lite.connect(DB_NAME)    
	    cur = con.cursor()
	    return cur,con
	except lite.Error, e:	    
	    print "Error %s:" % e.args[0]
	    sys.exit(1)	    

class databaseAccess():
	# Class that allows easy access to database functionality 
	def __init__(self):
		self.cur, self.con = set_up_db()
		res = self.con.execute("select * from loan")
		self.col_name_list = {t[0]:i for i,t in enumerate(res.description)}
		self.tables = ["TestThirtySix", "TrainThirtySix", "TestSixty", "TrainSixty"]

	# Extracting loans based on loan_status -- Fully Paid, Charged Off, Current.
	def extract_loans_with_status(self, status):
		execute_string = "SELECT * FROM loan WHERE loan_status = '{}' ".format(status)
		self.cur.execute(execute_string)
		return self.cur.fetchall()

	def extract_loans_with_zip(self, zip):
		execute_string = "SELECT * FROM loan WHERE zip_code = '{}' ".format(zip)
		self.cur.execute(execute_string)
		return self.cur.fetchall()

	def extract_table_loans(self, table_name):
		execute_string = ("SELECT * FROM {}").format(table_name)
		self.cur.execute(execute_string)
		return self.cur.fetchall()

	# Extracting loans based on term -- 36 or 60.
	def extract_term_loans(self, term,table):
		execute_string = ("SELECT * FROM {} WHERE term = ' {} months'").format(table,term)
		self.cur.execute(execute_string)
		return self.cur.fetchall()

	# Randomly distributes data amongst the test and train data.
	def partition_data(self, features):
		def populate_table(table_name, loan_set):

			def clean_html(desc): # eliminates html tags.
  				cleanr = re.compile('<.*?>')
  				cleantext = re.sub(cleanr, '', desc)
  				return cleantext

			for loan in tqdm(loan_set, desc="Copying Loans"):
				query = "INSERT OR IGNORE INTO {} VALUES ({},".format(table_name, loan[0])
				for k in features.keys():
					if features[k] in STR_TYPES: query += '\''
					if k == 'desc':
						d = loan[self.col_name_list[k]]
						if d is None:
							query += "{}".format(d)
						else:
							d = clean_html(d)
							for char in string.punctuation:
								d = d.replace(char, ' ')
							if d is not None: d = d.encode('ascii', 'ignore')
  						query += "{}".format(d)
					elif k in DESC_WORDS:
						d = loan[self.col_name_list['desc']]
						if not d or k not in d:
							query += "0"
						else:
							query += "1"  
					else:
						query += "{}".format(loan[self.col_name_list[k]])
					if features[k] in STR_TYPES: query += '\''
					query += ","
				query = query[:-1] + ")"
				self.cur.execute(query)
				self.con.commit()


		loans = self.extract_term_loans(36,"loan")
		n = len(loans) / 2
		random.shuffle(loans)
		populate_table("TestThirtySix", loans[:n])
		populate_table("TrainThirtySix", loans[n:])
		
		loans = self.extract_term_loans(60,"loan")
		n = len(loans) / 2
		random.shuffle(loans)
		populate_table("TestSixty", loans[:n])
		populate_table("TrainSixty", loans[n:])
		
	# Features dict => { "column_name": DATA_TYPE } 
	# Refer to data/data_types.txt.
	def add_columns(self, features):
		for i in self.tables:
			for k, v in features.items():
				query = "ALTER TABLE {} ADD COLUMN {} {}".format(i, k, v)
				self.cur.execute(query)
				self.con.commit()

	# Features dict => { "column_name": DATA_TYPE } 
	# Refer to data/data_types.txt.
	def update_table_features(self, features):
		for i in self.tables:
			self.cur.execute("DROP TABLE IF EXISTS {}".format(i))
			self.cur.execute("CREATE TABLE {} (id INT PRIMARY KEY)".format(i))
		self.add_columns(features)
		self.partition_data(features)


	def updateTableValue(self,table,dictRow,colName,val):
		#Updates a particular value in the table
		#NOTE: need to commit for changes to take place
		idNum = dictRow["id"]
		query = "UPDATE {} SET {} = {} WHERE id = {}".format(table,colName,val,idNum)
		self.con.execute(query)


	def get_loans_issued_in(self, table, month, use_term = False, term=36):
		'''
		Returns a list of all the loans issued in @month
		@params: 
			table: the table to access info from
			month: The month the loan was issued in eg "Mar-2011"
			use_term: if you want to filter on term or not
			term: if you do filter on term, which terms to return
			return: a list of tuples, where each tuple is a single loan
		'''
		if use_term: #If table has both terms 
			execute_string = ("SELECT * FROM {} WHERE issue_d = '{}' AND term = ' {} months'").format(table,month,term)
		else:
			execute_string = ("SELECT * FROM {} WHERE issue_d = '{}'").format(table,month)
		self.cur.execute(execute_string)
		return self.cur.fetchall()


	def getColumnNames(self,table):
		#Matches the name of every column to its column number 
		res = self.con.execute(("select * from {}").format(table))
		return [t[0] for t in res.description]

	@staticmethod
	def stringToDate(dateString):
		#Converts a LC string eg "Jan-2012" into (month (int),year(int)) tuple
		if dateString == "None": 
			return None
		monthsInt = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6, \
				  "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
		m,y = dateString.split("-")
		return monthsInt[m],int(y)

	def dateToString(self,date):
		#Converts a (month,year) tuple back to string
		month,year = date
		monthsInt = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
		return monthsInt[month-1]+'-'+str(year)

	@staticmethod
	def monthsDifference(t1,t2):
		#Calculates the number of months between two
		if t1 == None or t2 == None: return None
		return abs(12*(t1[1]-t2[1])+t1[0]-t2[0])

	@staticmethod
	def subgradeToInt(subgrade):
		#LC ranks from A1-G5 - converted to a linear scale 1-35
		if(subgrade == "None"): return None
		letterToInt = {"A":0,"B":5,"C":10,"D":15,"E":20,"F":25,"G":30}
		score = letterToInt[subgrade[0]] + int(subgrade[1])
		return score

	@staticmethod
	def numYearsEmployedToInt(text):
		#Converts 10+years to 10
		years = [int(x) for x in re.findall(r'\d+', text)]
		if(len(years)>0): return max(years)
		return 0

def setUpDatabase():
	#Sets up the database for use after it has been downloaded  

	def createSubTables(db,cols):
		#Creates the subtables that will hold test and training data 
		
		for t in db.tables:
			db.cur.execute("DROP TABLE IF EXISTS {}".format(t))

		#Sets up the approporiate columns for copying over
		colString = ""
		for name,cType in cols.iteritems(): 
			colString+= " " + name
			colString+= " " + cType + ","
		colString = colString[:-1]
		#colString+= "PRIMARY KEY (ID)"
		
		for t in db.tables:
			query = "CREATE TABLE {} ( {})".format(t,colString)
			db.cur.execute(query)


	db = databaseAccess()
	#List of columns that will be copied from test/train 
	columnsToCopy = {
			 		 "issue_d":"VARCHAR(255)",
					 "total_pymnt" : "INT",
					 "zip_code": "TEXT",
					 "installment":"FLOAT",
					 "grade": "TEXT",
					 "sub_grade" :"TEXT",
					 "emp_length":"TEXT",
					 "home_ownership":"TEXT",
					 "dti":"FLOAT",
					 "loan_status":"TEXT",
					 "last_pymnt_d":"TEXT",
					 "last_pymnt_amnt":"FLOAT",
					 "funded_amnt":"INT",
					 "desc":"TEXT",
					 "term":"TEXT",

			 		}
	for d in DESC_WORDS: columnsToCopy[d] = "TEXT"
			 		#List of columns 
	columnsToCreate = { "exp_r":"FLOAT",
						"var": "FLOAT",
						"cluster":"INT"
					  }

	db.update_table_features(columnsToCopy)
	db.add_columns(columnsToCreate)
	print "Database Set Up Complete! \n"

	

	

if __name__ == "__main__":
	setUpDatabase()

