#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 19:43:56 2019

@author: rajs
"""
############### Load Libraries
from __future__ import print_function
from __future__ import division
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler

import numpy as np
import torchvision
import time
import os
import copy
print("PyTorch Version: ",torch.__version__)
print("Torchvision Version: ",torchvision.__version__)

# Init
data_dir = "../UCF-101_video_classification-master/data"
features = 2048
batch_size = 32
seq_len = 40

num_epochs = 100
learning_rate = 0.0005
weight_decay  = 0.0005
# Detect if we have a GPU available
#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
device = 'cpu'


#Train module
def train_model(model, dataloaders_dict,criterion, optimizer, scheduler, 
                num_epochs = 25,
                steps_per_epoch = 100,
                val_steps = 100,
                stateful = False):
    
    since = time.time()
    val_acc_history = []
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)
    
        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode
    
            running_loss = 0.0
            running_corrects = 0
    
            # Iterate over data.
            itercnt = 0
    
            for inputs, labels in dataloaders_dict[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)
                # zero the parameter gradients
                optimizer.zero_grad()
                
                if stateful:
                    model.hidden = model.init_hidden()
                
                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    
                    _, preds = torch.max(outputs, 1)
    
                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()                    
                    
                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                
                itercnt+=1
                if(phase == 'train'):                    
                    if(itercnt > steps_per_epoch):                                            
                        break
                else:
                    if(itercnt > val_steps):                                            
                        break                    
                
    #            epoch_loss = running_loss / len(dataloaders[phase].dataset)
    #            epoch_acc = running_corrects.double() / len(dataloaders[phase].dataset)
            if(phase == 'train'):  
                epoch_loss = running_loss / (itercnt * batch_size)
                epoch_acc = running_corrects.double() / (itercnt * batch_size)
            else:
                epoch_loss = running_loss / (itercnt * batch_size)
                epoch_acc = running_corrects.double() / (itercnt * batch_size)
    
    
            print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))
    
            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
            if phase == 'val':
                val_acc_history.append(epoch_acc)
    
        print()
    
        time_elapsed = time.time() - since
        print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
        print('Best val Acc: {:4f}'.format(best_acc))

    
    # load best model weights
    model.load_state_dict(best_model_wts)
    return model, val_acc_history


# Dataloaders
import glob
train_seq = sorted(glob.glob( data_dir + '/train-full/[A-B]**/*.avi', recursive = True))
val_seq   = sorted(glob.glob( data_dir + '/val-full/[A-B]**/*.avi', recursive = True))
features_seq  = sorted(glob.glob(data_dir + '/sequences/*.npy'))

print( len(train_seq))
print( len(val_seq))
print( len(features_seq))

import csv
with open( data_dir + '/data_file.csv', 'r') as fin:
    reader = csv.reader(fin)
    data = list(reader)

classes = []
for item in data:
    if item[1] not in classes:
        classes.append(item[1])
classes = sorted(classes)
num_classes = len(classes)

data_clean = []
max_frames = 300
for item in data:
    if int(item[3]) >= seq_len and int(item[3]) <= max_frames \
            and item[1] in classes:
        data_clean.append(item)
print(len(data))
data = data_clean
print(len(data))

train = []
val = []
for item in data:
    if item[0] == 'train':
        train.append(item)
    else:
        val.append(item)


#def get_all_sequences_in_memory(batch_Size, train_test):    
#    data = train if train_test == 'train' else val
#    print("Getting %s data with %d samples." % (train_test, len(data)))
#    
#    X, ye, y = [], [], []
#    for row in data:
#        
#        path = data_dir + '/sequences/'+ row[2] + '-' + str(seq_len) + '-' \
#                + 'features.npy'        
#            
#        if os.path.isfile(path):
#            sequence = np.load(path)            
#        else:
#            sequence = None
#                
#        if sequence is None:
#            print(row)
#            print(path)
#            print("Can't find sequence. Did you generate them?")
#            return [],[]
#    
#        X.append(sequence)
#        
#        label_encoded = classes.index(row[1])
#        label_hot = np.eye(len(classes), dtype='float32')[label_encoded]              
#        y.append(label_hot)
#        ye.append(label_encoded)
#        
#    ye = np.array(ye)
#    y  = np.array(y)
#    
#    y1 = np.expand_dims(y,0)
##    y2 = y1.repeat(seq_len,0)
#    
#    X = np.array(X)
#    X = X.squeeze(2)
#    
#    return X.transpose(1,0,2), y1

import random
def frame_generator(batch_Size, train_test):
    data = train if train_test == 'train' else val

    while 1:
        X, ye = [], []

        for _ in range(batch_size):
            sequence = None        
            row = random.choice(data)
            
            path = '../UCF-101_video_classification-master/data/sequences/'+ \
                    row[2] + '-' + str(seq_len) + '-' + 'features.npy'        
                
            if os.path.isfile(path):
                sequence = np.load(path)            
            else:
                sequence = None
                    
            if sequence is None:
                print(row)
                print(path)
                print("Can't find sequence. Did you generate them?")
                return [],[]


            X.append(sequence)
            label_encoded = classes.index(row[1])
#            label_hot = np.eye(len(classes), dtype='float32')[label_encoded]              
#            y.append(label_hot)
            ye.append(label_encoded)
            
        ye = np.array(ye)
        
        X = np.array(X)
        X = X.squeeze(2)
        X = X.transpose(1,0,2)
        
        X = torch.tensor(X)
        ye = torch.tensor(ye)
                
        yield X,ye

#Xtrain, ytrain = get_all_sequences_in_memory(batch_size, 'train')
#Xval, yval = get_all_sequences_in_memory(batch_size, 'val')
     

dataloaders_dict = {x: frame_generator(batch_size, x) 
                    for x in ['train', 'val']
                    }

########## MODEL
class Model(nn.Module):
    def __init__(self, features, batch_size, classes, seq_length, dropout = 0.5):
        super(Model, self).__init__()
        self.features = features
        self.batch_size = batch_size
        self.num_layers = 1
        self.classes = classes 
        self.seq_length = seq_length
        self.dropout = dropout
        self.hidden_dim = 64
        self.lstm1 = nn.LSTM(features, self.hidden_dim, self.num_layers)
#        self.lstm2 = nn.LSTM(512, classes, 1)
        self.linear = nn.Linear(self.hidden_dim, classes)
        
#        self.lstm3 = nn.LSTM(features, classes, 2)
        
    def forward(self, x):
        o1, self.hidden = self.lstm1(x) 
#        o2, (h2,c2) = self.lstm2(o1) 
#        o2, (h1,c1) = self.lstm3(x) 
        outputs = self.linear(o1[-1])
        return outputs

    def init_hidden(self):
       return (torch.zeros(self.num_layers, self.batch_size, self.hidden_dim),
                torch.zeros(self.num_layers, self.batch_size, self.hidden_dim))
      
model = Model(features, batch_size, num_classes, seq_len)
print(model)

## Training and Validation
params_to_update = model.parameters()

count = 0
for name,param in model.named_parameters():
    if param.requires_grad == True:        
        print("\t",name)

model_parameters = filter(lambda p: p.requires_grad, model.parameters())
params = sum([np.prod(p.size()) for p in model_parameters])
print('No of trainable parameters', params)

optimizer = optim.Adam(params_to_update,
                 lr = learning_rate,
                 betas = (0.9, 0.999), 
                 eps = 1e-08, 
                 weight_decay = weight_decay, 
                 amsgrad=False)

scheduler = lr_scheduler.ReduceLROnPlateau(optimizer, 'min')
criterion = nn.CrossEntropyLoss().to(device)



model_best, hist = train_model(model, dataloaders_dict,
                             criterion, optimizer, scheduler, 
                             num_epochs = num_epochs,
                             steps_per_epoch = int(len(train)/batch_size),
                             val_steps = int(len(val)/batch_size),
                             stateful = False
                             )


