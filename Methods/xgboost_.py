from __future__ import print_function
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from tools import statistics
import math
import time
import operator as op
from matplotlib.font_manager import FontProperties


def convertSeriesToMatrix(vectorSeries, sequence_length):
    matrix=[]
    for i in range(len(vectorSeries)-sequence_length+1):
            matrix.append(vectorSeries[i:i+sequence_length])
    return matrix


def create_feature_map(before):
    outfile = open('../xgb.fmap', 'w')
    for i in range(before):
        j = before - i
        outfile.write('{0}\t{1}\tq\n'.format(i, 'Lag_'+str(j)))
    outfile.close()

# load raw data
df_raw = pd.read_csv('../data/load.csv', header=0, usecols=[0,1])
# numpy array
df_raw_array = df_raw.values
# daily load
list_hourly_load = [df_raw_array[i,1]/1000 for i in range(0, len(df_raw))]
print ("Data shape of list_hourly_load: ", np.shape(list_hourly_load))
k = 0
for j in range(0, len(list_hourly_load)):
    if(abs(list_hourly_load[j]-list_hourly_load[j-1])>2 and abs(list_hourly_load[j]-list_hourly_load[j+1])>2):
        k = k + 1
        list_hourly_load[j] = (list_hourly_load[j - 1] + list_hourly_load[j + 1]) / 2 + list_hourly_load[j - 24] - list_hourly_load[j - 24 - 1] / 2
    sum = 0
    num = 0
    for t in range(1,8):
        if(j - 24*t >= 0):
            num = num + 1
            sum = sum + list_hourly_load[j - 24*t]
        if(j + 24*t < len(list_hourly_load)):
            num = num + 1
            sum = sum + list_hourly_load[j + 24*t]
    sum = sum / num
    if(abs(list_hourly_load[j] - sum)>3):
        k = k + 1
        if(list_hourly_load[j] > sum): list_hourly_load[j] = sum + 3
        else: list_hourly_load[j] = sum - 3
# print(k)
# plt.plot(list_hourly_load)
# plt.show()
# shift all data by mean
list_hourly_load = np.array(list_hourly_load)
shifted_value = list_hourly_load.mean()
list_hourly_load -= shifted_value
# the length of the sequnce for predicting the future value
sequence_length = 25
# convert the vector to a 2D matrix
matrix_load = convertSeriesToMatrix(list_hourly_load, sequence_length)
matrix_load = np.array(matrix_load)
print ("Data shape: ", matrix_load.shape)
# train_row = int(round(0.9 * matrix_load.shape[0]))
train_row = matrix_load.shape[0] - matrix_load.shape[0]
print('train:',train_row,'test:', 24*14)
train_set = matrix_load[:train_row, :]
# random seed
np.random.seed(1234)
# shuffle the training set (but do not shuffle the test set)
np.random.shuffle(train_set)
# the training set
X_train = train_set[:, :-1]
# the last column is the true value to compute the mean-squared-error loss
y_train = train_set[:, -1]
print(X_train[0],y_train[0])
# the test set
X_test = matrix_load[train_row:, :-1]
y_test = matrix_load[train_row:, -1]
print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)

# xgboost
create_feature_map(24)
X_train, X_test = map(lambda a: np.array(a), [X_train, X_test])
data_train = xgb.DMatrix(X_train, label=y_train)
data_test = xgb.DMatrix(X_test, label=y_test)
watch_list = [(data_test, 'eval'), (data_train, 'train')]
param = {'max_depth': 6, 'eta': 0.1, 'silent': 1, 'objective': 'reg:linear'}
bst = xgb.train(param, data_train, num_boost_round=60, evals=watch_list)
# save model
bst.save_model('../xgboost.model')
# load model
bst = xgb.Booster()
bst.load_model('../xgboost.model')

# xgb.plot_importance(bst)
importance = bst.get_fscore(fmap='../xgb.fmap')
print(importance)
importance = sorted(importance.items(), key=op.itemgetter(1))
df = pd.DataFrame(importance, columns=['feature', 'fscore'])
df['fscore'] = df['fscore'] / df['fscore'].sum()
df.plot(kind='barh', x='feature', y='fscore')
font = FontProperties(fname='C:\Windows\Fonts\simsun.ttc', size=12)
font_title = FontProperties(fname='C:\Windows\Fonts\simsun.ttc', size=14)
plt.show()
# get the predicted values
start = time.clock()
predicted_values = bst.predict(data_test)
# evaluation
mape = statistics.mape((y_test+shifted_value)*1000,(predicted_values+shifted_value)*1000)
print('MAPE is ', mape)
mae = statistics.mae((y_test+shifted_value)*1000,(predicted_values+shifted_value)*1000)
print('MAE is ', mae)
mse = statistics.meanSquareError((y_test+shifted_value)*1000,(predicted_values+shifted_value)*1000)
print('MSE is ', mse)
rmse = math.sqrt(mse)
print('RMSE is ', rmse)
nrmse = statistics.normRmse((y_test+shifted_value)*1000,(predicted_values+shifted_value)*1000)
print('NRMSE is ', nrmse)
# plot the results
fig = plt.figure()
plt.plot(y_test + shifted_value, label="$Observed$", c='green')
plt.plot(predicted_values + shifted_value, label="$Predicted$", c='red')
plt.xlabel('Hour')
plt.ylabel('Electricity load, kW')
plt.legend()
plt.show()
