# imports - compatibility packages
from __future__ import absolute_import

# imports - third-party packages
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# module imports
from bulbea._util import (
    _check_type,
    _check_int,
    _check_real,
    _check_iterable,
    _check_sequence,
    _validate_in_range
)
from bulbea.entity.share import _get_cummulative_return
import bulbea as bb

def split(sharedata,
          attrs     = 'Close',
          window    = 0.01,
          train     = 0.60,
          shift     = 1,
          normalize = False):
    '''
    :type attrs: :obj: `str`, :obj:`list`
    '''
    _check_iterable(attrs, raise_err = True)
    _check_int(shift, raise_err = True)
    _check_real(window, raise_err = True)
    _check_real(train, raise_err = True)

    _validate_in_range(train, 0, 1, raise_err = True)

    data   = sharedata[attrs]

    length = len(sharedata)
    
    if window >=0 and window <= 1:
        window = int(np.rint(length * window))
        
    print('====Actual window is ' + str(window))
        
    offset = shift - 1

    splits = np.array([data[i if i is 0 else i + offset: i + window] for i in range(length - window)])
    normsplit = np.array([ [split[0],split[len(split)-1]] for split in splits])

    if normalize:
        splits = np.array([_get_cummulative_return(split) for split in splits])

    size   = len(splits)
    split  = int(np.rint(train * size))

    train  = splits[:split,:]
    test   = splits[split:,:]

    Xtrain, Xtest = train[:,:-1], test[:,:-1]
    XtrainNorm, XtestNorm = normsplit[:split,:],normsplit[split:,:]
    ytrain, ytest = train[:, -1], test[:, -1]

    return (Xtrain, Xtest, ytrain, ytest, XtrainNorm, XtestNorm)
