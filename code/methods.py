
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.layers import Bidirectional
from keras.models import Sequential
from keras.models import load_model

from sklearn.utils import shuffle
from sklearn.metrics import accuracy_score

import math
import time
import numpy as np
import random
from random import randint
random.seed( 3 )
import datetime, re, operator
from random import shuffle

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' #get rid of warnings
from os import listdir
from os.path import isfile, join, isdir
import pickle

from nlp_aug import *

###################################################
######### loading folders and txt files ###########
###################################################

#loading a pickle file
def load_pickle(file):
	return pickle.load(open(file, 'rb'))

#create an output folder if it does not already exist
def confirm_output_folder(output_folder):
	if not os.path.exists(output_folder):
	    os.makedirs(output_folder)

#get full image paths
def get_txt_paths(folder):
    txt_paths = [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and '.txt' in f]
    if join(folder, '.DS_Store') in txt_paths:
        txt_paths.remove(join(folder, '.DS_Store'))
    txt_paths = sorted(txt_paths)
    return txt_paths

#get subfolders
def get_subfolder_paths(folder):
    subfolder_paths = [join(folder, f) for f in listdir(folder) if (isdir(join(folder, f)) and '.DS_Store' not in f)]
    if join(folder, '.DS_Store') in subfolder_paths:
        subfolder_paths.remove(join(folder, '.DS_Store'))
    subfolder_paths = sorted(subfolder_paths)
    return subfolder_paths

#get all image paths
def get_all_txt_paths(master_folder):

    all_paths = []
    subfolders = get_subfolder_paths(master_folder)
    if len(subfolders) > 1:
        for subfolder in subfolders:
            all_paths += get_txt_paths(subfolder)
    else:
        all_paths = get_txt_paths(master_folder)
    return all_paths

###################################################
################ data processing ##################
###################################################

#get the pickle file for the vocab so you don't have to load the entire dictionary
def gen_vocab_dicts(folder, output_pickle_path, huge_word2vec):

    vocab = set()
    text_embeddings = open(huge_word2vec, 'r').readlines()
    word2vec = {}

    #get all the vocab
    all_txt_paths = get_all_txt_paths(folder)
    print(all_txt_paths)

    #loop through each text file
    for txt_path in all_txt_paths:

    	# get all the words
    	try:
    		all_lines = open(txt_path, "r").readlines()
    		for line in all_lines:
    			words = line[:-1].split(' ')
    			for word in words:
    			    vocab.add(word)
    	except:
    		print(txt_path, "has an error")
    
    print(len(vocab), "unique words found")

    # load the word embeddings, and only add the word to the dictionary if we need it
    for line in text_embeddings:
        items = line.split(' ')
        word = items[0]
        if word in vocab:
            vec = items[1:]
            word2vec[word] = np.asarray(vec, dtype = 'float32')
    print(len(word2vec), "matches between unique words and word2vec dictionary")
        
    pickle.dump(word2vec, open(output_pickle_path, 'wb'))
    print("dictionaries outputted to", output_pickle_path)

#generate more data with standard augmentation
def gen_standard_aug(train_orig, output_file):
	writer = open(output_file, 'w')
	lines = open(train_orig, 'r').readlines()
	for i, line in enumerate(lines):
		parts = line[:-1].split('\t')
		label = parts[0]
		sentence = parts[1]
		aug_sentences = standard_augmentation(sentence)
		for aug_sentence in aug_sentences:
			writer.write(label + "\t" + aug_sentence + '\n')
	writer.close()


#getting the x and y inputs in numpy array form from the text file
def get_x_y(train_txt, word2vec_len, input_size, word2vec, percent_dataset):

	#read in lines
	train_lines = open(train_txt, 'r').readlines()
	shuffle(train_lines)
	train_lines = train_lines[:int(percent_dataset*len(train_lines))]
	num_lines = len(train_lines)

	#initialize x and y matrix
	x_matrix = np.zeros((num_lines, input_size, word2vec_len))
	y_matrix = np.zeros((num_lines))

	#insert values
	for i, line in enumerate(train_lines):

		parts = line[:-1].split('\t')
		label = int(parts[0])
		sentence = parts[1]	

		#insert x
		words = sentence.split(' ')
		words = words[:x_matrix.shape[1]] #cut off if too long
		for j, word in enumerate(words):
			if word in word2vec:
				x_matrix[i, j, :] = word2vec[word]

		#insert y
		y_matrix[i] = label

	return x_matrix, y_matrix


###################################################
##################### model #######################
###################################################

#building the model in keras
def build_model(sentence_length, word2vec_len):
	model = None
	model = Sequential()
	model.add(Bidirectional(LSTM(50, return_sequences=True), input_shape=(sentence_length, word2vec_len)))
	model.add(Dropout(0.5))
	model.add(Bidirectional(LSTM(50, return_sequences=False)))
	model.add(Dropout(0.5))
	model.add(Dense(20, activation='relu'))
	model.add(Dense(1, kernel_initializer='normal', activation='sigmoid'))
	model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
	#print(model.summary())
	return model

#confidences to binary
def conf_to_pred(y):

    if type(y) == list:
        y_class = []
        for pred in y:
            if pred < 0.5:
                y_class.append(0)
            else:
                y_class.append(1)
        return y_class

    else:
        y_class = np.zeros(y.shape)
        for i in range(y.shape[0]):
            if y[i] < 0.5:
                y_class[i] = 0
            else:
                y_class[i] = 1
        return y_class




