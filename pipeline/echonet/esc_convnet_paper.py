#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Environmental Sound Classification with Convolutional Neural Networks.

Paper source code ported to Keras with some small adjustments.

# Reference:

- [Environmental Sound Classification with Convolutional Neural Networks -
    paper replication data](https://github.com/karoldvl/paper-2015-esc-convnet)

"""

import argparse
import functools
import os
import sys

import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', help='Theano device used for computations')
    args = parser.parse_args()

    RANDOM_SEED = 20161013
    np.random.seed(RANDOM_SEED)

    DEVICE = args.device if args.device else 'gpu0'
    THEANO_FLAGS = ('device={},'
                    'floatX=float32,'
                    'dnn.conv.algo_bwd_filter=deterministic,'
                    'dnn.conv.algo_bwd_data=deterministic').format(DEVICE)
    os.environ['THEANO_FLAGS'] = THEANO_FLAGS
    os.environ['KERAS_BACKEND'] = 'theano'

    sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/..')

    import keras
    keras.backend.set_image_dim_ordering('th')
    from keras.layers.convolutional import Convolution2D as Conv
    from keras.layers.convolutional import MaxPooling2D as Pool
    from keras.layers.core import Activation, Dense, Dropout, Flatten

    from echonet.models import EchoNet
    from echonet.datasets.esc_original import OriginalESC


    def uniform(scale):
        return functools.partial(keras.initializations.uniform, scale=scale)

    def normal(stdev):
        return functools.partial(keras.initializations.normal, scale=stdev)

    TRAIN_FOLDS = [2, 3, 4]
    VALIDATION_FOLDS = [5]
    TEST_FOLDS = [1]

    print('\nLoading ESC-50 dataset from ../data/ESC-50/')
    esc50 = OriginalESC('../data/ESC-50/', '../data/.ESC-50.cache', TRAIN_FOLDS, VALIDATION_FOLDS,
                        TEST_FOLDS)


    input_shape = esc50.input_shape
    L2 = keras.regularizers.l2

    layers = [
        Conv(80, 57, 6, init=uniform(0.001), W_regularizer=L2(0.001), input_shape=input_shape),
        Activation('relu'),
        Pool((4, 3), (1, 3)),
        Dropout(0.5),
        Conv(80, 1, 3, init=uniform(0.1), W_regularizer=L2(0.001)),
        Activation('relu'),
        Pool((1, 3), (1, 3)),
        Flatten(),
        Dense(5000, init=normal(0.01), W_regularizer=L2(0.001)),
        Activation('relu'),
        Dropout(0.5),
        Dense(5000, init=normal(0.01), W_regularizer=L2(0.001)),
        Activation('relu'),
        Dropout(0.5),
        Dense(esc50.class_count, init=normal(0.01), W_regularizer=L2(0.001)),
        Activation('softmax')
    ]

    optimizer = keras.optimizers.SGD(lr=0.01, momentum=0.9, nesterov=True)

    print('\nCompiling Keras model')
    model = EchoNet('esc_convnet_paper', layers=layers, optimizer=optimizer)

    # Initialize biases of the first convolutional layer
    conv_weights = model.layers[0].get_weights()
    conv_weights[1][:] = 0.1
    model.layers[0].set_weights(conv_weights)

    print('\nTraining... (batch size of 1 000 | 30 batches per epoch)')
    epoch_size = esc50.train_size * 25    # Approximation of the original paper
    model.fit(esc50, batch_size=1000, epochs=150, epoch_size=epoch_size)

    model.net.save('esc_convnet_paper.h5')
