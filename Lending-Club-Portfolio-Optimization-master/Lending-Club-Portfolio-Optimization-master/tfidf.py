import sqlite3 as lite
import math
from util.porter import stem
import re, string

class TFIDF_Extractor():
	def tf(self, word, doc):
		return float(doc.split().count(word)) / float(len(doc.split()))

	def n_containing(self, word, doclist):
		return sum(1 for doc in doclist if word in doc.split())

	def idf(self, word, doclist):
		return math.log(len(doclist) / float((1 + self.n_containing(word, doclist))))

	def tfidf(self, word, doc, doclist):
		return self.tf(word, doc) * self.idf(word, doclist)

	def __init__(self, db):
		'''
		Class for TF-IDF Analysis. Handles basic text sanitization across all loans.
		Creates two documents -- one for defaulted loan descriptions and one for non-defaulted
		and current loan descriptions.
		'''

		def compileDescriptions(loan_set):
			def sanitize_desc(desc):
				clean_desc = ""
				for word in desc.split():
					word = stem(word.lower())
					if len(word) >= 5 and word in self.engDict:
						clean_desc += word + " "
				return clean_desc

			doc_arr = []
			doc_string = ""
			for loan in loan_set:
				description = loan[self.columns.index('desc')]
				if description != None: 
					d = sanitize_desc(description)
					doc_arr.append(d)
					doc_string += d + " "
			return (doc_arr, doc_string)

		def computeScores(docArr, docString):
			'''
			Computes the TF-IDF score for each word in each document. 
			TF-IDF Class returns an array where array[0] is an array of the top scoring words
			for defaulted loans and array[1] is an array of top scoring words for nondefaulting loans.
			'''
			
			scores = {}
			for word in docString.split():
				if word not in scores:
					scores[word] = self.tfidf(word, docString, docArr)
			sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse = True)
			for word, score in sorted_words[:20]:
				print("\tWord: {}, TF-IDF: {}".format(word, round(score, 5)))
			return sorted_words

		self.db = db
		self.columns = self.db.getColumnNames("loan")
		with open("engDict.txt", "r") as f:
			self.engDict = {line.strip() for line in f}

		defaulted_loans = self.db.extract_loans_with_status("Charged Off")
		nondefaulted_loans = self.db.extract_loans_with_status("Fully Paid") + self.db.extract_loans_with_status("Current")
		# documentList = [compileDescriptions(defaulted_loans), compileDescriptions(nondefaulted_loans)]
		defaultDocList = compileDescriptions(defaulted_loans)
		nonDefaultDocList = compileDescriptions(nondefaulted_loans)
		self.defaultWords = computeScores(defaultDocList[0], defaultDocList[1] + nonDefaultDocList[1])
		self.nondefaultWords = computeScores(nonDefaultDocList[0], nonDefaultDocList[1] + defaultDocList[1])

		

