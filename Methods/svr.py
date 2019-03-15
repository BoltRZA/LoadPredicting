import math
from tools import statistics
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm

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
train_row = matrix_load.shape[0] - 24*7
print('train:',train_row,'test:',24*7)
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
time_test = [df_raw_array[i,0] for i in range(train_row+23, len(df_raw))]
# svr
kernelList = ["rbf"]
names = ["Observed","Predicted"]
preds = []
preds.append(y_test)
for i in range(len(kernelList)):
    clf = svm.SVR(C=2.0, kernel=kernelList[i])
    clf.fit(X_train, y_train)
    predicted_values = clf.predict(X_test)
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
    preds.append(predicted_values)
# show
fig = plt.figure()
colors = ["g","r","b","c","m","y","k","w"]
legendVars = []
for j in range(len(preds)):
    print(j)
    x, = plt.plot(preds[j]+shifted_value, color=colors[j])
    legendVars.append(x)
plt.xlabel('Hour')
plt.ylabel('Electricity load, kW')
plt.legend(legendVars, names)
plt.show()
