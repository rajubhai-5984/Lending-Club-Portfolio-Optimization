# Lending Club Portfolio Optimization

##Goal
Lending Club is an online peer-to-peer lending platform, matching borrowers and lenders. Since its foundation in 2006, Lending Club has issued over $22Bn in loans to individuals and small businesses. As an investor, you can choose which loans to finance, and whether to finance as little as $25 or the full loan. Each investor is trying to build the best portfolio of loans. Our project utilizes Artificial Intelligence techniques in order to try and build the optimal portfolio of Lending Club loans. In particular, our algorithms try to build the optimal portfolio from loans offered by Lending Club in any given month.

##Steps to run:

(i) Download dataset from kaggle:

\- https://www.kaggle.com/wendykan/lending-club-loan-data

(ii) Set up virtual environment:
  
 \- $source venv/bin/activate
 
 
 (iii) Install requirements: 
 
 \- $pip install -r requirements.txt
 
 (iv) Set up database:
 
 \- $python databaseUtil.py
 
 (iv) See what the returns from the optimal portfolio would be! 
 
 \- $python $main.py -l 
 
 \- include option l to relearn weights
 
 See what your returns would have been in a particular month in FIND CORRECT FOLDER
 
 


##File Descriptions

main.py: Ouputs a CSV containing your returns for Oracle, Sharpe Ratio, MDP and Baseline

expectedReturns.py; Uses machine learning to calculate transition probabilities, expected return for each loan, and expected variance 

baseline.py: Computes baseline returns (invest in everythign equally)

oracle.py: Computes oracle returns (invest with perfect future knowledge)

optimalPortfolio.py: Given a set of loans expected returns and variance, calculates the optimal portfolio using Sharpe Ratio

tfidf.py: Calculates the twenty most meaningful words in the descriptions

kMeansCov.py: Uses kmeans to calculate covariance

databaseUtil.py: Useful for accessing database

requirements.txt: pip install -r requirements.txt 

/util - a series of helper functions/classes



