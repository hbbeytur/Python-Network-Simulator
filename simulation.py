import Network, analyze
import numpy as np


num_source = 1
num_packet = 10000
# arrivalRate = np.linspace(0.1,0.99,99)
arrivalRate = [0.8]
ages = []
for rate in arrivalRate:
	print(rate)
	net = Network.Network(num_source=num_source,
						  num_packet=num_packet,
						  arrival=("poisson",[rate]),
						  service=("exponential",[1]),
						  queue="FCFS",
						  preemption=False)
	net.run()

	average_age = []
	for record in net.freshstory:
		average_age.append(analyze.calculate_average_age(record))

	print(average_age)
	ages.append(average_age)