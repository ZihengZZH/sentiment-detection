import numpy as np
import math
from scipy import stats
import datetime
from . import text
from . import bow_feat as feat
from . import sign_test as st

import progressbar
from multiprocessing import cpu_count, Pool


# save the training model into a file for later use
def save_to_file(prob_neg_vec, prob_pos_vec, prior_sentiment):
    # NOTE THAT ONLY THE LATEST MODEL WILL BE KEPT UNLESS INTENDED
    # type prob_neg_vec: numpy array
    # type prob_pos_vec: numpy array
    # type prior_sentiment: float
    np.save("./models/prob_neg_vector", prob_neg_vec)
    np.save("./models/prob_pos_vector", prob_pos_vec)
    np.save("./models/prior_sentiment", prior_sentiment)
    readme_notes = "This model is trained on " + str(datetime.datetime.now())
    np.savetxt("./models/readme.txt", readme_notes)


# load the training model from the file 
def load_from_file():
    # type prob_neg_vec: numpy array
    # type prob_pos_vec: numpy array
    # type prior_sentiment: float
    try:
        prob_neg_vec = np.load("./models/prob_neg_vector.npy")
        prob_pos_vec = np.load("./models/prob_pos_vector.npy")
        prior_sentiment = np.load("./models/prior_sentiment.npy")
        return prob_neg_vec, prob_pos_vec, prior_sentiment

    except:
        print("\nTHE CLASSIFIER HAS NOT BEEN TRAINED YET")
    

def train_nb_classifier(train_mat, train_c, smooth_type):
    # para train_mat: matrix of data & tags
    # para train_c: R^2 sentiment (neg/0 or pos/1)
    # return para: prob_vec: R^2 vec of conditional prob
    # return para: prior_sentiment
    if (smooth_type != 'laplace') and (smooth_type != 'None'):
        return

    no_train_review = len(train_mat)
    no_words = len(train_mat[0])
    prior_sentiment = sum(train_c) / float(no_train_review)  # prob 0.5

    # check whether smoothing or not
    # numerator Tct
    prob_neg_num = np.zeros(no_words)
    prob_pos_num = np.zeros(no_words)
    # denominator sum(Tct)
    prob_neg_denom = .0
    prob_pos_denom = .0

    if smooth_type == 'laplace':
        k = 2.0  # constant for all words
    else:
        k = 0.0

    bar = progressbar.ProgressBar()

    # iteration on every training review
    for i in bar(range(no_train_review)):
        if train_c[i] == 0:
            prob_neg_num += train_mat[i]
            prob_neg_denom += (sum(train_mat[i])+k)
        else:
            prob_pos_num += train_mat[i]
            prob_pos_denom += (sum(train_mat[i])+k)
    # prob vector for negative reviews P(fi|0)
    prob_neg_vec = (prob_neg_num+k)/(prob_neg_denom)
    # prob vector for positive reviews P(fi|1)
    prob_pos_vec = (prob_pos_num+k)/(prob_pos_denom)

    save_to_file(prob_neg_vec, prob_pos_vec, prior_sentiment)


def test_nb_classifier(test_vec):
    # para prob_neg_vec: P(fi|0)
    # para prob_pos_vec: P(fi|1)
    # para prob_class: P(c=0) or P(c=1) (equal in this project)
    prob_neg_vec, prob_pos_vec, prior_class = load_from_file()
    # avoid the nan in np.log(0) calculation
    prob_neg_log = np.log(prob_neg_vec)
    prob_pos_log = np.log(prob_pos_vec)
    for i in range(len(prob_neg_log)):
        if np.isinf(prob_neg_log[i]):
            prob_neg_log[i] = 0.0
        if np.isinf(prob_pos_log[i]):
            prob_pos_log[i] = 0.0

    prob_neg = sum(test_vec*prob_neg_log) + np.log(1.0-prior_class)
    prob_pos = sum(test_vec*prob_pos_log) + np.log(prior_class)
    # binary classification argmax
    if prob_neg > prob_pos:
        # predict a negative review
        return 0
    else:
        # predict a positive review
        return 1


# write results to text file
def save_results(feat_type, vocab_length, train_size, smoothing, neg_accuracy, pos_accuracy):
    notes = "results obtained on " + str(datetime.datetime.now())
    f = open('./results/.txt', 'a+', encoding='utf-8')
    f.write("\nfeature: %s\t#feature: %d\ttraining size: %d\tsmooth: %s\tneg_accuracy: %f\tpos_accuracy: %f\tnotes: %s" % (
        feat_type, vocab_length, train_size, smoothing, neg_accuracy, pos_accuracy, notes))
    f.close()


# write results to text file
def save_results_cv(fold_type, feat_type, performances, perf_average, variance):
    notes = "results obtained on " + str(datetime.datetime.now())
    f = open('./results_cv/.txt', 'a+', encoding='utf-8')
    f.write("\nfold type: %s\nfeature: %s\t#performance: %s\taverage performance: %f\tvariance: %f\tnotes: %s" % (
        fold_type, feat_type, performances, perf_average, variance, notes))
    f.close()
