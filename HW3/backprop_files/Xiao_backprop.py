#!/usr/bin/env python3
import numpy as np
from io import StringIO

NUM_FEATURES = 124 #features are 1 through 123 (123 only in test set), +1 for the bias
DATA_PATH = "/u/cs246/data/adult/" #TODO: if doing development somewhere other than the cycle server, change this to the directory where a7a.train, a7a.dev, and a7a.test are
#DATA_PATH = "/Users/Robert/Desktop/ML/adult/"

#returns the label and feature value vector for one datapoint (represented as a line (string) from the data file)
def parse_line(line):
    tokens = line.split()
    x = np.zeros(NUM_FEATURES)
    y = int(tokens[0])
    y = max(y,0) #treat -1 as 0 instead, because sigmoid's range is 0-1
    for t in tokens[1:]:
        parts = t.split(':')
        feature = int(parts[0])
        value = int(parts[1])
        x[feature-1] = value
    x[-1] = 1 #bias
    return y, x

#return labels and feature vectors for all datapoints in the given file
def parse_data(filename):
    with open(filename, 'r') as f:
        vals = [parse_line(line) for line in f]
        (ys, xs) = ([v[0] for v in vals],[v[1] for v in vals])
        return np.asarray([ys],dtype=np.float32).T, np.asarray(xs,dtype=np.float32) #returns a tuple, first is an array of labels, second is an array of feature vectors

def init_model(args):
    w1 = None
    w2 = None

    if args.weights_files:
        with open(args.weights_files[0], 'r') as f1:
            w1 = np.loadtxt(f1)
        with open(args.weights_files[1], 'r') as f2:
            w2 = np.loadtxt(f2)
            w2 = w2.reshape(1,len(w2))
    else:
        #TODO (optional): If you want, you can experiment with a different random initialization. As-is, each weight is uniformly sampled from [-0.5,0.5).
        w1 = np.random.rand(args.hidden_dim, NUM_FEATURES) #bias included in NUM_FEATURES
        w2 = np.random.rand(1, args.hidden_dim + 1) #add bias column

    #At this point, w1 has shape (hidden_dim, NUM_FEATURES) and w2 has shape (1, hidden_dim + 1). In both, the last column is the bias weights.
    #TODO: Replace this with whatever you want to use to represent the network; you could use use a tuple of (w1,w2), make a class, etc.
    model = (w1, w2)
    return model

def loss_func(y, y_hat):
    return 1/2 * np.sum(np.square(y - y_hat))

def sigmoid(a):
    return 1.0/(1.0+np.exp(-a))

def dsigmoid(a):
    return sigmoid(a)*(1-sigmoid(a))
    # return z*(1-z)

def forward(model, input):
    # input-hidden
    w1, w2 = extract_weights(model)
    a1 = np.dot(w1, input)
    # print(input.shape)
    try:
        z1 = sigmoid(a1).reshape(a1.shape[0], 1)
    except:
        z1 = sigmoid(a1)    
    bias = np.ones((1, z1.shape[1]))
    z1_biased = np.concatenate((z1, bias), axis = 0)

    # hidden-output
    a2 = np.dot(w2, z1_biased)
    z2 = sigmoid(a2)

    d = {"a1" : a1, "z1" : z1, "z1_biased" : z1_biased, "a2" : a2, "z2" : z2}

    return z2, d


def train_model(model, train_ys, train_xs, dev_ys, dev_xs, args):
    #TODO: Implement training for the given model, respecting args
    model = init_model(args)
    w1, w2 = model
    model_o = model
    acc_train, acc_dev = list(),list()
    best_iter, best_hid = 0,0
    max_acc = 0

    for i in range(args.iterations):
        for n in range(train_ys.shape[0]):     
            x_vector = train_xs[n].reshape(train_xs[n].shape[0], 1)

            # forward
            y_hat, dic = forward(model, x_vector)
            loss = loss_func(x_vector, y_hat)

            # backward
            delta2 = (y_hat-train_ys[n]) * dsigmoid(dic["a2"])
            dweight2 = np.dot(delta2, dic["z1_biased"].T)
            w2_reduced = w2[:, 0:w2.shape[1]-1]
            delta1 = delta2 * (w2_reduced.T * dsigmoid(dic["a1"]))
            dweight1 = np.dot(delta1, x_vector.T)
            
            #update
            w2 = w2 - args.lr * dweight2
            w1 = w1 - args.lr * dweight1
            model = (w1, w2)

        if not args.nodev:
            acc_train.append(test_accuracy(model, train_ys, train_xs))
            acc_dev.append(test_accuracy(model, dev_ys, dev_xs))
            if i == 0:
                max_acc = test_accuracy(model, dev_ys, dev_xs)
                best_iter = 0
                model_o = w1, w2
            elif (i > 0) and (acc_dev[i] > max_acc):
                best_iter = i
                model_o = w1, w2
                max_acc = acc_dev[i]

    if not args.nodev:
        print('Best number of iterations at learning rate = %s, hidden layer dimension = %s is %s' % (args.lr, args.hidden_dim, best_iter+1))
        return model_o
    
    return model

def test_accuracy(model, test_ys, test_xs):
    y_hat = forward(model, test_xs.T)[0]
    return np.sum((test_ys.T >= 0.5) == (y_hat >= 0.5)) / test_xs.shape[0]


def extract_weights(model):
    w1 = model[0]
    w2 = model[1]
    #TODO: Extract the two weight matrices from the model and return them (they should be the same type and shape as they were in init_model, but now they have been updated during training)
    return w1, w2

def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Neural network with one hidden layer, trainable with backpropagation.')
    parser.add_argument('--nodev', action='store_true', default=False, help='If provided, no dev data will be used.')
    parser.add_argument('--iterations', type=int, default=5, help='Number of iterations through the full training data to perform.')
    parser.add_argument('--lr', type=float, default=0.1, help='Learning rate to use for update in training loop.')

    weights_group = parser.add_mutually_exclusive_group()
    weights_group.add_argument('--weights_files', nargs=2, metavar=('W1','W2'), type=str, help='Files to read weights from (in format produced by numpy.savetxt). First is weights from input to hidden layer, second is from hidden to output.')
    weights_group.add_argument('--hidden_dim', type=int, default=5, help='Dimension of hidden layer.')

    parser.add_argument('--print_weights', action='store_true', default=False, help='If provided, print final learned weights to stdout (used in autograding)')

    parser.add_argument('--train_file', type=str, default=os.path.join(DATA_PATH,'a7a.train'), help='Training data file.')
    parser.add_argument('--dev_file', type=str, default=os.path.join(DATA_PATH,'a7a.dev'), help='Dev data file.')
    parser.add_argument('--test_file', type=str, default=os.path.join(DATA_PATH,'a7a.test'), help='Test data file.')


    args = parser.parse_args()

    """
    At this point, args has the following fields:

    args.nodev: boolean; if True, you should not use dev data; if False, you can (and should) use dev data.
    args.iterations: int; number of iterations through the training data.
    args.lr: float; learning rate to use for training update.
    args.weights_files: iterable of str; if present, contains two fields, the first is the file to read the first layer's weights from, second is for the second weight matrix.
    args.hidden_dim: int; number of hidden layer units. If weights_files is provided, this argument should be ignored.
    args.train_file: str; file to load training data from.
    args.dev_file: str; file to load dev data from.
    args.test_file: str; file to load test data from.
    """
    train_ys, train_xs = parse_data(args.train_file)
    dev_ys = None
    dev_xs = None
    if not args.nodev:
        dev_ys, dev_xs= parse_data(args.dev_file)
    test_ys, test_xs = parse_data(args.test_file)

    model = init_model(args)
    model = train_model(model, train_ys, train_xs, dev_ys, dev_xs, args)
    accuracy = test_accuracy(model, test_ys, test_xs)
    print('Test accuracy: {}'.format(accuracy))
    if args.print_weights:
        w1, w2 = extract_weights(model)
        with StringIO() as weights_string_1:
            np.savetxt(weights_string_1,w1)
            print('Hidden layer weights: {}'.format(weights_string_1.getvalue()))
        with StringIO() as weights_string_2:
            np.savetxt(weights_string_2,w2)
            print('Output layer weights: {}'.format(weights_string_2.getvalue()))


if __name__ == '__main__':
    main()



