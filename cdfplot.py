import numpy as np 
from matplotlib import pyplot as plt

plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True 

N = 500
data = np.random.randn(N) 
count, bins_count = np.histogram(data, bins=10) 
pdf = count/ sum(count) 
cdf = np.cumsum(pdf)
print(bins_count)
plt.plot(bins_count[1:], cdf, label="CDF")
plt.legend()
plt.show()
