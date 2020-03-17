import myNetwork, analyze
import numpy as np
import itertools

MATLAB = False

if MATLAB:
    import matlab.engine
    eng = matlab.engine.start_matlab()

# num_source = 2
num_packet = 30000
num_sources = range(2,3)
arrivalRate = np.linspace(0.1,5,10)
# arrivalRate = [10]
ages = []
# rateScan = np.linspace(0.1,1,num=20,endpoint=False)
schedulers = ["Normal"]
preemptions = [True]

for rate, num_source,scheduler,preemption in itertools.product(arrivalRate,num_sources,schedulers,preemptions):
	print(rate,num_source,scheduler,preemption)
	net = myNetwork.Network(num_source=num_source,
						  num_packet=num_packet,
						  arrival=("poisson",[rate, rate]),
						  service=("erlang2",[1]*num_source),
						  queue="LCFS",
						  preemption=preemption,
						  preemptiveDiscard=False,
						  scheduler=scheduler)
	net.run()

	average_age = []
	for record in net.freshstory:
		average_age.append(float(analyze.calculate_average_age(record)))

	print(average_age)
	# mu = net.service[1][0]
	# p = np.sum(net.arrivalsetting[1])/mu
	# pi = net.arrivalsetting[1][0]/mu
	# theoricAge = 1/mu * (((1+p+p**2)**2 + 2*p**3)/((1+p+p**2)*(1+p)**2) +(1+p**2/(1+p))*(1/pi))
	# print(theoricAge)
	ages.append(average_age)