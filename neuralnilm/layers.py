from __future__ import print_function, division
import theano
import theano.tensor as T

import numpy as np

from lasagne.layers import Layer, LSTMLayer, RecurrentLayer

            
def BLSTMLayer(*args, **kwargs):
    # setup forward and backwards LSTM layers.  Note that
    # LSTMLayer takes a backwards flag. The backwards flag tells
    # scan to go backwards before it returns the output from
    # backwards layers.  It is reversed again such that the output
    # from the layer is always from x_1 to x_n.

    # If learn_init=True then you can't have multiple
    # layers of LSTM cells.
    return BidirectionalLayer(LSTMLayer, *args, **kwargs)

          
def BidirectionalRecurrentLayer(*args, **kwargs):
    # setup forward and backwards LSTM layers.  Note that
    # LSTMLayer takes a backwards flag. The backwards flag tells
    # scan to go backwards before it returns the output from
    # backwards layers.  It is reversed again such that the output
    # from the layer is always from x_1 to x_n.

    # If learn_init=True then you can't have multiple
    # layers of LSTM cells.
    return BidirectionalLayer(RecurrentLayer, *args, **kwargs)


def BidirectionalLayer(layer_class, *args, **kwargs):
    kwargs.pop('backwards', None)
    l_fwd = layer_class(*args, backwards=False, **kwargs)
    l_bck = layer_class(*args, backwards=True, **kwargs)
    return ElemwiseSumLayer([l_fwd, l_bck])


class DimshuffleLayer(Layer):
    def __init__(self, input_layer, pattern):
        super(DimshuffleLayer, self).__init__(input_layer)
        self.pattern = pattern

    def get_output_shape_for(self, input_shape):
        return tuple([input_shape[i] for i in self.pattern])

    def get_output_for(self, input, *args, **kwargs):
        return input.dimshuffle(self.pattern)


class MixtureDensityLayer(Layer):
    """
    Based on:
      amjadmahayri.wordpress.com/2014/04/30/mixture-density-networks
      github.com/aalmah/ift6266amjad/blob/master/experiments/mdn.py
    """

    def __init__(self, input_layer, n_output_features, n_components=2):
        super(MixtureDensityLayer, self).__init__(input_layer)
        n_input_features = input_layer.get_output_shape()[-1]
        self.n_output_features = n_output_features
        self.n_components = n_components

        # TODO sanity check parameters

        W_mu_values = np.asarray(
            np.random.uniform(
                low=-np.sqrt(6. / (n_input_features + n_output_features)),
                high=np.sqrt(6. / (n_input_features + n_output_features)),
                size=(n_input_features, n_output_features, n_components)),
            dtype=theano.config.floatX)

        W_values = np.asarray(
            np.random.uniform(
                low=-np.sqrt(6. / (n_input_features + n_output_features)),
                high=np.sqrt(6. / (n_input_features + n_output_features)),
                size=(n_input_features, n_components)),
            dtype=theano.config.floatX)
    
        # TODO: use Lasagne's create_params API
        # TODO: add biases
        self.W_mu = theano.shared(
            value=W_mu_values, name='W_mu', borrow=True)
        self.W_sigma = theano.shared(
            value=W_values, name='W_sigma', borrow=True)
        self.W_mixing = theano.shared(
            value=W_values.copy(), name='W_mixing', borrow=True)
    
    def get_output_for(self, input, *args, **kwargs):
        self.mu = T.tensordot(input, self.W_mu, axes = [[1],[0]])
        self.sigma = T.nnet.softplus(T.dot(input, self.W_sigma))
        self.mixing = T.nnet.softmax(T.dot(input, self.W_mixing))
        return [self.mu, self.sigma, self.mixing]

    def get_params(self):
        return [self.W_mu, self.W_sigma, self.W_mixing]

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], input_shape[1], 
                self.n_output_features * self.n_components * 3)
