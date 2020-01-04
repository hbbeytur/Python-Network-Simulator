import json
import numpy as np
from matplotlib import pyplot as plt

def calculate_average_age(record):
	sumQ = 0
	for i in range(1,len(record)):
		Q = np.divide(np.square(record[i][1]-record[i-1][0]) - np.square(record[i][1]-record[i][0]),2)
		sumQ = Q + sumQ
		# print(sumQ)
	return sumQ /(record[-1][1] - record[1][1])

