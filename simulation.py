import Network, analyze
import numpy as np
import itertools


# num_source = 2
num_packet = 10000
num_sources = range(4,10)
# arrivalRate = np.linspace(0.1,0.9,9)
arrivalRate = [1]
ages = []

for rate, num_source in itertools.product(arrivalRate,num_sources):
	print(rate,num_source)
	net = Network.Network(num_source=num_source,
						  num_packet=num_packet,
						  arrival=("poisson",[rate]*num_source),
						  service=("exponential",[1*num_source]*num_source),
						  queue="LCFS",
						  preemption=True,
						  scheduler="Normal")
	net.run()

	average_age = []
	for record in net.freshstory:
		average_age.append(analyze.calculate_average_age(record))

	print(average_age)
	ages.append(average_age)