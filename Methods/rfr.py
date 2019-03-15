from __future__ import print_function
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from tools import statistics
import math
import time
import operator as op
from matplotlib.font_manager import FontProperties
from sklearn.externals import joblib
from tools import statistics

# define a function to convert a vector of time series into a 2D matrix
def convertSeriesToMatrix(vectorSeries, sequence_length):
    matrix=[]
    for i in range(len(vectorSeries)-sequence_length+1):
        matrix.append(vectorSeries[i:i+sequence_length])
    return matrix

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
train_row = matrix_load.shape[0] - 48
print('train:',train_row,'test:',48)
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

# rfr
model = RandomForestRegressor(n_estimators = 100, max_features=5)
model.fit(X_train, y_train)
joblib.dump(model, '../rfr.model')
model =joblib.load('../rfr.model')

feature_importance = model.feature_importances_
X = [' Lag_24 ',' Lag_23 ',' Lag_22 ',' Lag_21 ',' Lag_20 ',' Lag_19 ',' Lag_18 ',' Lag_17 ',' Lag_16 ',
     ' Lag_15 ',' Lag_14 ',' Lag_13 ',' Lag_12 ',' Lag_11 ',' Lag_10 ',' Lag_9 ',' Lag_8 ',' Lag_7 ',
     ' Lag_6 ',' Lag_5 ',' Lag_4 ',' Lag_3 ',' Lag_2 ',' Lag_1 ']
s = 0
for i in range(len(feature_importance)):
    s += feature_importance[i]

plt.figure()
plt.bar(np.arange(1, len(feature_importance) + 1), feature_importance/s, color='lightsteelblue')
plt.plot(np.arange(1, len(feature_importance) + 1), feature_importance/s)
plt.xticks(np.arange(1, len(feature_importance) + 1),X)
plt.xlabel('Feature')
plt.ylabel('Feature importance')
plt.grid(True)
plt.show()

# get the predicted values
start = time.clock()
predicted_values = model.predict(X_test)
# evaluation
mape = statistics.mape((y_test + shifted_value) * 1000, (predicted_values + shifted_value) * 1000)
print('MAPE is ', mape)
mae = statistics.mae((y_test + shifted_value) * 1000, (predicted_values + shifted_value) * 1000)
print('MAE is ', mae)
mse = statistics.meanSquareError((y_test + shifted_value) * 1000, (predicted_values + shifted_value) * 1000)
print('MSE is ', mse)
rmse = math.sqrt(mse)
print('RMSE is ', rmse)
nrmse = statistics.normRmse((y_test + shifted_value) * 1000, (predicted_values + shifted_value) * 1000)
print('NRMSE is ', nrmse)
# plot the results
fig = plt.figure()
plt.plot(y_test + shifted_value, label="$Observed$", c='green')
plt.plot(predicted_values + shifted_value, label="$Predicted$", c='red')
plt.xlabel('Hour')
plt.ylabel('Electricity load, kW')
plt.legend()
plt.show()
