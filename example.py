import os
import bulbea as bb
from bulbea.learn.evaluation import split
import numpy as np
from bulbea.learn.models import RNN
from bulbea.learn.models.ann import RNNCell
from sklearn.metrics import mean_squared_error
from bulbea.entity.share import _plot_bollinger_bands
import pandas as pd
import matplotlib.pyplot as pplt

companies = ["BIDU", "AMZN", "MSFT"] #
categories = ["Close", "High", "Low"]
outputDir = "./results/"

def Predict(share, company, category, seqlen):
    #category = 'High' # 'Low', 'Close'
    # Load Data

    Xtrain, Xtest, ytrain, ytest, XtrainNorm, XtestNorm = split(share, category, window=0.01, train = 0.60, normalize = True)
    Xtrain = np.reshape(Xtrain, (Xtrain.shape[0], Xtrain.shape[1], 1))
    Xtest  = np.reshape(Xtest,  ( Xtest.shape[0],  Xtest.shape[1], 1))

    # Train
    layers      = [1, 100, 100, 1]
    nbatch      = 512              
    epochs      = 5     
    nvalidation = 0.05

    rnn = RNN(layers, cell = RNNCell.LSTM)

    rnn.fit(Xtrain, ytrain,
            batch_size       = nbatch,
            nb_epoch         = epochs,
            validation_split = nvalidation)
        
        
    # Test
    predicted = rnn.predict(Xtest)
    mean_squared_error(ytest, predicted)

    #print("Show trend")
    #pplt.plot(ytest)
    #pplt.plot(predicted)
    #pplt.show()

    #print("Show exact values")
    #pplt.plot(XtestNorm[:,1])
    #pplt.plot(XtestNorm[:,0]*(predicted[:,0] + 1))
    #pplt.show()

    #print("Show predicted sequences")
    #seq = (Xtest[len(Xtest)-1]+1)*XtestNorm[len(XtestNorm)-1,0]
    #predictednew, predictednewNorm = rnn.sequence(seq, 100)
    #pplt.plot(predictednew)
    #pplt.plot(predictednewNorm)
    #pplt.show()


    seq = (Xtest[len(Xtest)-1]+1)*XtestNorm[len(XtestNorm)-1,0]
    predictednew, predictednewNorm = rnn.sequence(seq, seqlen)
    testNorm = XtestNorm[:,0]*(predicted[:,0] + 1)
    dataNorm = np.array([*testNorm, *predictednewNorm])

    #fig = pplt.figure()
    pplt.plot(XtestNorm[:,1])
    pplt.plot(dataNorm)
    title = "{}{}(min={},max={})".format(company, category, np.amin(predictednewNorm), np.amax(predictednewNorm))
    pplt.title(title)
    #pplt.savefig(category+".png")
    #pplt.show()
    #pplt.close(fig)
    
def Process(sharedata, prefix, company, seqlen):
    fig = pplt.figure()

    pplt.subplot(311)
    Predict(sharedata, company, categories[0], seqlen)
    pplt.subplot(312)
    Predict(sharedata, company, categories[1], seqlen)
    pplt.subplot(313)
    Predict(sharedata, company, categories[2], seqlen)
        
    pplt.subplots_adjust(left=0.1, right = 0.9, bottom = 0.1, top=0.9, wspace=0.8, hspace = 0.8)
    pplt.savefig(os.path.join(outputDir, company+prefix+".png") )

    pplt.close(fig)

if __name__ == "__main__":

    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    for company in companies:
        share = bb.Share2(ticker=company)
        #Process(share.datahs, 'long', company, 50)
        Process(share.datart, 'short', company, 500)
        
        
    
    
    
    
    
