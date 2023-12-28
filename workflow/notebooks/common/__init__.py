
import numpy as np
import sys as sys
import os as os
basepath = os.path.normpath(os.path.join(os.getcwd(), "..\\"))
sys.path.append(basepath)
import mixturemapping as mm
from sklearn.mixture import GaussianMixture as _skGM
# add the parent directory to the basepath to have mixturemapping without installing

from . import quality

def shuffle_along_axis(a, axis):
    idx = np.random.rand(*a.shape).argsort(axis=axis)
    return np.take_along_axis(a,idx,axis=axis)

def __getSamples(mapFunc,
                 mixN,
                 inputMixM,
                 outputMixM,
                 sampleSize,
                 shuffle=True
                 ):

    totalSamplesN = 100

    # compute an array of weights of the different mixture components
    w = np.random.uniform(low=0, high=1, size=(totalSamplesN, mixN))
    w = w / np.expand_dims(np.sum(w, axis=1), 1)

    # fill the initial values of the distributions
    trainFeatures = {
        "InputMean": np.random.uniform(high=10.0, size=(totalSamplesN, 1, inputMixM)) + np.random.uniform(high=5.0, size=(totalSamplesN, mixN, inputMixM)),
        "InputStdDev": np.random.uniform(high=.3, size=(totalSamplesN, 1, inputMixM)) + np.random.uniform(high=.2, size=(totalSamplesN, mixN, inputMixM)),
        "InputWeights": w,
    }

    # create a mapped set of training and validation samples
    TrainMeanSamplesArray = []
    TrainStdDevSamplesArray = []
    TrainWeightsSamplesArray = []
    OutputMeanSamplesArray = []
    OutputCovsSamplesArray = []
    OutputWeightsSamplesArray = []

    TrainSamplesArray = []
    InputSamplesArray = []

    for i in range(totalSamplesN):

        mix = mm.utils.getSkleanGM(
            trainFeatures["InputWeights"][i], trainFeatures["InputMean"][i], trainFeatures["InputStdDev"][i])

        # copy the input to make the right length
        TrainMeanSamplesArray.append(np.transpose(
            [trainFeatures["InputMean"][i] for x in range(sampleSize)]))
        TrainStdDevSamplesArray.append(np.transpose(
            [trainFeatures["InputStdDev"][i] for x in range(sampleSize)]))
        TrainWeightsSamplesArray.append(np.transpose(
            [trainFeatures["InputWeights"][i] for x in range(sampleSize)]))

        samples = mix.sample(sampleSize)[0]
        if shuffle:
            InputSamplesArray.append(np.transpose(shuffle_along_axis(samples, 0)))
        else:
            InputSamplesArray.append(np.transpose(samples))
        
        transformed_samples = [mapFunc(x) for x in samples]
        TrainSamplesArray.append(np.transpose(transformed_samples))

        outMix = _skGM(mixN, covariance_type='full')
        outMix.fit(transformed_samples)

        OutputMeanSamplesArray.append(outMix.means_)
        OutputCovsSamplesArray.append(outMix.covariances_)
        OutputWeightsSamplesArray.append(outMix.weights_)        
       


    trainFeatures["TrainSamples"] = np.reshape(np.transpose(
        TrainSamplesArray, [0, 2, 1]), [sampleSize*totalSamplesN, outputMixM])
    trainFeatures["InputSamples"] = np.reshape(np.transpose(
        InputSamplesArray, [0, 2, 1]), [sampleSize*totalSamplesN, inputMixM])

    trainFeatures["TrainMean"] = np.reshape(np.transpose(TrainMeanSamplesArray, [
                                            0, 3, 2, 1]), [sampleSize*totalSamplesN, mixN, inputMixM])
    trainFeatures["TrainStdDev"] = np.reshape(np.transpose(TrainStdDevSamplesArray, [
        0, 3, 2, 1]), [sampleSize*totalSamplesN, mixN, inputMixM])
    trainFeatures["TrainWeights"] = np.reshape(np.transpose(
        TrainWeightsSamplesArray, [0, 2, 1]), [sampleSize*totalSamplesN, mixN])
    
    trainFeatures["OutputMean"] = np.stack(OutputMeanSamplesArray)
    trainFeatures["OutputCovs"] = np.stack(OutputCovsSamplesArray)
    trainFeatures["OutputWeights"] = np.stack(OutputWeightsSamplesArray)

    trainFeatures["GroupedSamples"] = np.array(TrainSamplesArray)
    trainFeatures["GroupedInputSamples"] = np.array(InputSamplesArray)
    return trainFeatures


def getSimpleLinearA(mixN,
                     inputMixM,
                     outputMixM,
                     sampleSize,
                     shuffle=True
                     ):
    def mapFunc(x):
        """
        we assume x to be a single sample vec, which is transformed to a point in the output distribution
        """
        return np.array([x[0]*0.9 + .9, -x[1]*0.9 - 0.3, -x[0]*0.5 + .2]) + np.random.normal(scale=.1, size=3)
    return {
        **__getSamples(mapFunc,
                                      mixN,
                                      inputMixM,
                                      outputMixM,
                                      sampleSize,
                                      shuffle=shuffle
                                      ),
                                      "testFeatures": {
                                          "mapping_kernel": [[0.9, 0, -0.5], [0.0, -0.9, 0]],
                                          "mapping_bias": [0.9, -0.3, 0.2],
                                          "cov_std": [.1, 0.1, 0.1],
                                      }

    }


def getSinSamples(mixN,
                  inputMixM,
                  outputMixM,
                  sampleSize,
                  shuffle=True
                  ):
    def mapFunc(x):
        """
        we assume x to be a single sample vec, which is transformed to a point in the output distribution
        """
        return np.array([x[0]*0.9 + .9, 2.3*np.sin(-x[1]*0.35) + 0.3, -x[0]*0.5 + .2]) + np.random.normal(scale=0.1, size=3)
    return __getSamples(mapFunc,
                        mixN,
                        inputMixM,
                        outputMixM,
                        sampleSize,
                        shuffle=shuffle
                        )