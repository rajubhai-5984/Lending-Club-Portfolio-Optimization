#Util files taken from the sentiment assignment

import os, random, operator, sys, collections, math
from collections import Counter
from tqdm import tqdm

class gradientDescent():
    #class for learning the weights of a certain vector
    
    @staticmethod   
    def stochasticGradientDescent(trainExamples,featureExtractor,updateWeights,numIters,eta):
        '''
        Learns the weight vector using stochastic gradient descent
        @params: 
            - trainExamples: Examples to train on list of rows from tuple
            - featureExtractor: converts x to (f1,f2,...,fn) func - featureExtractor(x)
            - numIters: the number of iterations to run the gradient descent
            - eta: the step size
            - updateWeights: the function to update the weights updateWeights(weights,phiX,y,eta)
        '''
        def extractInfo(examples):
            #Returns the information in a list: [(xi_vals,yi_val)] where x vals is a list
            return [(featureExtractor(x),y) for y,x in trainExamples]

        weights = collections.defaultdict(int) #feature->weight
        formattedTrain = extractInfo(trainExamples)
        for step in tqdm(range(numIters),desc="Gradient Descent"):
                if updateWeights!=gradientDescent.logisticLoss:
                    for phiX, y in formattedTrain:
                        if None not in phiX: #Don't analyze if missing data
                            updateWeights(weights,phiX,y,eta)
                else: 
                    updateWeights(weights,formattedTrain,eta)
        return weights


    @staticmethod
    def evaluateWeights(formattedTrain,weights):
        '''
        Tests whether the loss
        '''
        totalLoss = 0
        for phiX,y in formattedTrain:
            predY = dotProduct(phiX,weights)
            totalLoss+=y-predY
        return totalLoss/len(formattedTrain)

    ###############################
    #    UpdateWeights Functions  #

    @staticmethod
    def hingeLoss(weights,phiX,y,eta):
        #Updates weights according to hinge loss
        if(dotProduct(weights,phiX)*y<1):
            increment(weights,y*eta,phiX)

    @staticmethod
    def leastSquares(weights,phiX,y,eta):
        #Updates weights according to least squares
        predMinusTarget = dotProduct(weights,phiX)-y
        increment(weights,-eta*2*predMinusTarget,phiX)

    @staticmethod
    def logisticLoss(weights,formattedTrain,eta):
        #Updates weights according to logistic loss 

        def sigmoid(z):
            return 1.0/(1+math.e**-z)

        def dLL_dTheta(formattedTrain,weights):
            dLL_dTheta = None
            for phiX,y in formattedTrain:
                if dLL_dTheta is None: dLL_dTheta = {i:0 for i in phiX}
                xDotTheta = dotProduct(weights,phiX)
                for j in phiX:
                    dLL_dTheta[j] += (y - sigmoid(xDotTheta))*phiX[j]
            return dLL_dTheta

        dLL_dTheta = dLL_dTheta(formattedTrain,weights)
        for j in dLL_dTheta:
            weights[j] -=eta * dLL_dTheta[j]

    ###############################

def dotProduct(d1, d2):
    """
    @param dict d1: a feature vector represented by a mapping from a feature (string) to a weight (float).
    @param dict d2: same as d1
    @return float: the dot product between d1 and d2
    """
    if len(d1) < len(d2):
        return dotProduct(d2, d1)
    else:
        return sum(d1.get(f, 0) * v for f, v in d2.items())

def increment(d1, scale, d2):
    """
    Implements d1 += scale * d2 for sparse vectors.
    @param dict d1: the feature vector which is mutated.
    @param float scale
    @param dict d2: a feature vector.
    """
    for f, v in d2.items():
        d1[f] = d1.get(f, 0) + v * scale

def readExamples(path):
    '''
    Reads a set of training examples.
    '''
    examples = []
    for line in open(path):
        # Format of each line: <output label (+1 or -1)> <input sentence>
        y, x = line.split(' ', 1)
        examples.append((x.strip(), int(y)))
    print 'Read %d examples from %s' % (len(examples), path)
    return examples

def binaryClassify(x):
    #Returns -1 if x<0, and 1 if x>0
    if(x>=0): return 1
    return -1

def evaluatePredictor(examples, predictor):
    '''
    predictor: a function that takes an x and returns a predicted y.
    Given a list of examples (x, y), makes predictions based on |predict| and returns the fraction
    of misclassiied examples.
    '''
    error = 0
    for x, y in examples:
        if predictor(x) != y:
            error += 1
    return 1.0 * error / len(examples)

def outputWeights(weights, path):
    print "%d weights" % len(weights)
    out = open(path, 'w')
    for f, v in sorted(weights.items(), key=lambda (f, v) : -v):
        print >>out, '\t'.join([f, str(v)])
    out.close()

def verbosePredict(phi, y, weights, out):
    yy = 1 if dotProduct(phi, weights) > 0 else -1
    if y:
        print >>out, 'Truth: %s, Prediction: %s [%s]' % (y, yy, 'CORRECT' if y == yy else 'WRONG')
    else:
        print >>out, 'Prediction:', yy
    for f, v in sorted(phi.items(), key=lambda (f, v) : -v * weights.get(f, 0)):
        w = weights.get(f, 0)
        print >>out, "%-30s%s * %s = %s" % (f, v, w, v * w)
    return yy

def outputErrorAnalysis(examples, featureExtractor, weights, path):
    out = open('error-analysis', 'w')
    for x, y in examples:
        print >>out, '===', x
        verbosePredict(featureExtractor(x), y, weights, out)
    out.close()

def interactivePrompt(featureExtractor, weights):
    while True:
        print '> ',
        x = sys.stdin.readline()
        if not x: break
        phi = featureExtractor(x) 
        verbosePredict(phi, None, weights, sys.stdout)

if __name__ == "__main__":
    weights = {1:1,2:2}
    x = {1:0.1,2:0.2}
    formattedTrain = [(x,1),(x,0)]
    
