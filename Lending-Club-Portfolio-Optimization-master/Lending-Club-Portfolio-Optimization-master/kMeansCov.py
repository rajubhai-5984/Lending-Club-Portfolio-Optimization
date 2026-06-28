from databaseUtil import databaseAccess
from collections import defaultdict
from datetime import date
import cPickle as pickle
from util.zipDist import Zip_Codes
from util.pyzipcode import ZipCodeDatabase
import numpy
import random
PICKLE_DIRECTORY = "data/"
YEARS = ["2011","2012","2013","2014","2015"]
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
NUM_CLUSTERS = 10
MAX_ITERS = 2

class kMeans():
	def dictRow(self, table, row):
	#Converts a row from sql from a list to a dict
		return {c:r for c,r in zip(self.db.getColumnNames(table),row)} 

	def __init__(self, db, table, usePickle=True):

		def calculate_group_cov():
			'''
			Builds covariance map in the form:
				{loangroup1: {loangroup1: cov(1,1), loangroup2: cov(1,2)}, loangroup2: {etc}}
			Requires numpy.
			'''
			covariances = {}
			for k, v in self.cash_flow_dict.iteritems():
				covariances[k] = {}

			for k1, v1 in self.cash_flow_dict.iteritems():
				for k2, v2 in self.cash_flow_dict.iteritems():
					cov = numpy.cov(numpy.vstack((v1, v2)))
					print cov
					covariances[k1][k1] = cov[0][0]
					covariances[k1][k2] = cov[0][1] 
					covariances[k2][k1] = cov[1][0]
					covariances[k2][k2] = cov[1][1]
			return covariances


		def contribution_to_month(l, curr_date):
			'''
			Determines if loan is active during given month/year. Takes in a loan
			and a date to compare it against in the form 'Jan-2015'.  

			It extracts the issue date, last payment date, term length, and then 'add_months'
			to generate what the last payment date should be given there is no default.  So if 
			last payment date and this projected date do not align, we know we have default so 
			we are actually losing money in those months.
			'''
			def add_months(d, months_to_add):
				month = d.month - 1 + months_to_add
				year = int(d.year + month / 12)
				month = month % 12 + 1
				return date(year, month, 1)


			loan_term = int(l[self.columns.index('term')].split()[0])
			loan_issue_date = l[self.columns.index('issue_d')]
			loan_last_pymnt_date = l[self.columns.index('last_pymnt_d')]
			# print loan_issue_date, loan_last_pymnt_date
			if loan_last_pymnt_date == "None": return l[self.columns.index('installment')]

			issue_month = MONTHS.index(loan_issue_date[: loan_issue_date.index('-')]) + 1
			issue_year = int(loan_issue_date[loan_issue_date.index('-') + 1:])
			issue_date = date(issue_year, issue_month, 1)

			last_month = MONTHS.index(loan_last_pymnt_date[: loan_last_pymnt_date.index('-')]) + 1
			last_year = int(loan_last_pymnt_date[loan_last_pymnt_date.index('-') + 1:])
			last_date = date(last_year, last_month, 1)
			projected_end_date = add_months(issue_date, loan_term)
			if issue_date < curr_date and curr_date < last_date:
				return l[self.columns.index('installment')] # installment
			if issue_date < curr_date and curr_date == last_date:
				return l[self.columns.index('last_pymnt_amnt')] # last_pymnt_amnt instead of installment.
			if last_date < curr_date and curr_date <= projected_end_date:
				return -l[self.columns.index('installment')] # -installment because default
			return 0 # loan not active

		def generate_cash_flow_vectors():
			'''
			For each cluster: 
				Creates a vector of cash flows for every month by adding up all of the installments of
				the loans in group.
			Returns a map of cluster => cash_flow_vector[] 
			'''
			d = defaultdict(list)
			for k, v in self.clusters.iteritems():
				cash_flow = []
				for year in YEARS:
					for month in range(1, len(MONTHS) + 1):
						monthly_cash_flow = 0
						for loan in v:
							monthly_cash_flow += contribution_to_month(loan, date(int(year), month, 1)) # if contributing to monthly cash flow.
						cash_flow.append(monthly_cash_flow/len(v))
				d[k] = cash_flow				
			return d

		def kmeans(examples, K, maxIters):

			def dotProduct(d1, d2):
				if len(d1) < len(d2):
					return dotProduct(d2, d1)
				else:
					return sum(d1.get(f, 0) * v for f, v in d2.items())

			def reevaluate_centers(centers, clusters):
				newcenters = []
				for i in range(len(centers)):
					new = {}
					data = clusters[i] #list of maps
					for p in data: #a map
						for pKey, pValue in p.iteritems():
							if pKey not in new:
								new[pKey] = 0
							new[pKey] += pValue
					for k,v in new.iteritems():
						new[k] = v/(len(data)+1)
					newcenters.append(new)
				return newcenters

			def zipCodeDistance(centerZip, exampleZip):
				if len(centerZip) == 2: centerZip = "0" + centerZip 
				if len(exampleZip) == 2: exampleZip = "0" + exampleZip
				centerZip = centerZip[:3]
				exampleZip = exampleZip[:3]

				if centerZip not in zipSetCache:
					zipCodeSet1 = [k for k in zipcodes if centerZip in k.zip]
					if len(zipCodeSet1) == 0:
						zipCodeSet1 = [k for k in zipcodes if centerZip[:2] in k.zip]
					zipSetCache[centerZip] = zipCodeSet1
				else:
					zipCodeSet1 = zipSetCache[centerZip]

				if exampleZip not in zipSetCache:
					zipCodeSet2 = [k for k in zipcodes if exampleZip in k.zip]
					if len(zipCodeSet2) == 0:
						zipCodeSet2 = [k for k in zipcodes if exampleZip[:2] in k.zip]
					zipSetCache[exampleZip] = zipCodeSet2
				else:
					zipCodeSet2 = zipSetCache[exampleZip]

				dist = 0
				for x in zipCodeSet1:
					for y in zipCodeSet2:
						dist += zipDist.get_distance(x.zip, y.zip)
				return dist/(len(zipCodeSet1) * len(zipCodeSet2))

			def calculateDistance(center, currExample):
				res = {}
				for k, v in center.iteritems():
					if k == "zip_code":
						res[k] = zipCodeDistance(str(center[k]), str(currExample[k]))
					else:
						res[k] = abs(center[k] - currExample[k])#homeOwnershipDistance(center[k], currExample[k])
				return dotProduct(res, res)

			def classify(centers, currExample):
				bestmukey = 0
				bestmukeyDist = float("inf")

				for i in range(len(centers)):
					center = centers[i]
					distance = calculateDistance(center, currExample)
					if distance < bestmukeyDist:
						bestmukey = i
						bestmukeyDist = distance
				return bestmukey

			def stringify(dictToString):
				return str(dictToString["zip_code"]) + str(dictToString["home_ownership"])

			# Initialize to K random centers
			oldcenters = random.sample(examples, K)
			centers = random.sample(examples, K)
			assignments = range(len(examples))
			zipSetCache = {}

			#while not has_converged(centers, oldcenters) and i < MAX_ITERS:
			for j in range(MAX_ITERS):
				oldcenters = centers
				# Assign all points in examples to clusters
				clusters  = {}
				for init in range(len(centers)):
					clusters[init] = []

				cache = {}
				for i in range(len(examples)):
					currExample = examples[i]
					if stringify(currExample) in cache:
						assignments[i] = cache[stringify(currExample)]
					else:
						assignmentNum = classify(centers, currExample)
						assignments[i] = assignmentNum
						cache[stringify(currExample)] = assignmentNum
					if assignmentNum not in clusters: clusters[assignmentNum] = []
					clusters[assignmentNum].append(examples[i])
				# Reevaluate centers
				centers = reevaluate_centers(oldcenters, clusters)
				j += 1
			return centers, assignments

		def formulateExamples(loans):
			examples = []
			exampleIndexes = []
			for l in loans:
				zc = l[self.columns.index('zip_code')][:3]
				h_o = l[self.columns.index('home_ownership')]
				if h_o == "RENT":
					ho = 0
				else:
					ho = 1
				examples.append({"zip_code": int(zc), "home_ownership": ho})
				exampleIndexes.append(l) 
			return examples, exampleIndexes

		def update_table_kclusters(table, assignments):
			clusters = {}
			for i in range(len(assignments)):
				clusterNum = assignments[i]
				l = self.loanIndexes[i]
				loanDict = self.dictRow(table, l)
				self.db.updateTableValue(table, loanDict, "cluster", clusterNum)
				if clusterNum not in clusters: clusters[clusterNum] = []
				clusters[clusterNum].append(l)
			return clusters

		def term(table):
			if table.find("ThirtySix") > -1: return 36
			return 60


		self.db = db
		zcdb = ZipCodeDatabase()
		zipcodes = zcdb.find_zip()
		zipDist = Zip_Codes() 
		self.termLength = term(table)
		if usePickle:
			self.clusters = pickle.load(open(PICKLE_DIRECTORY+str(self.termLength)+"clusters.p", 'rb'))
			self.covariances = calculate_group_cov()
			self.covariances = pickle.load(open(PICKLE_DIRECTORY+str(self.termLength)+"covariances.p",'rb'))
		else:
			self.loans = db.extract_table_loans(table)
			self.columns = db.getColumnNames(table)
			examples, self.loanIndexes = formulateExamples(self.loans)
			centers, assignments = kmeans(examples, NUM_CLUSTERS, MAX_ITERS)

			self.clusters = update_table_kclusters(table, assignments)
			pickle.dump(self.clusters, open(PICKLE_DIRECTORY+str(self.termLength)+"clusters.p","wb"))

			self.cash_flow_dict = generate_cash_flow_vectors()
			self.covariances = calculate_group_cov()
			pickle.dump(self.covariances, open(PICKLE_DIRECTORY+str(self.termLength)+"covariances.p","wb"))

if __name__ == "__main__":
	db = databaseAccess()
	kmeans = kMeans(db, "TestSixty", False)


		



