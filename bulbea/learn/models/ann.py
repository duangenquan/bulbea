from __future__ import absolute_import
from six import with_metaclass

from keras.models import Sequential
from keras.layers import recurrent
from keras.layers import core
import numpy as np
from bulbea.entity.share import _get_cummulative_return

from bulbea.learn.models import Supervised

class ANN(Supervised):
    pass

class RNNCell(object):
    RNN  = recurrent.SimpleRNN
    GRU  = recurrent.GRU
    LSTM = recurrent.LSTM

class RNN(ANN):
    def __init__(self, sizes,
                 cell       = RNNCell.LSTM,
                 dropout    = 0.2,
                 activation = 'linear',
                 loss       = 'mse',
                 optimizer  = 'rmsprop'):
        self.model = Sequential()
        self.model.add(cell(
            input_dim        = sizes[0],
            output_dim       = sizes[1],
            return_sequences = True
        ))

        for i in range(2, len(sizes) - 1):
            self.model.add(cell(sizes[i], return_sequences = False))
            self.model.add(core.Dropout(dropout))

        self.model.add(core.Dense(output_dim = sizes[-1]))
        self.model.add(core.Activation(activation))

        self.model.compile(loss = loss, optimizer = optimizer)

    def fit(self, X, y, *args, **kwargs):
        return self.model.fit(X, y, *args, **kwargs)

    def predict(self, X):
        return self.model.predict(X)
        
    def sequence(self, x, num):
        h, w = x.shape
        x = np.reshape(x, (h*w))
        
        predicted = []
        predictedNorm = []
        
        for i in range(num):
            xnew = np.reshape(_get_cummulative_return(x), (1, h, w))
            
            datanew = self.model.predict(xnew)            
            datanewNorm = x[0]*(datanew+1)
            
            predicted.append(datanew)
            predictedNorm.append(datanewNorm)
            
            x = x[1:]
            x = np.append(x, datanewNorm)
            
        return np.reshape(np.array(predicted), num), np.reshape(np.array(predictedNorm), num)
            
            
    
    
