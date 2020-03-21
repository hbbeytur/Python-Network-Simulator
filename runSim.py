import myNetwork, analyze
import numpy as np
import itertools

def runSim(num_packet = 10000,
		   num_sources=range(1,2),
		   arrivalRate = np.linspace(0.1,5,10),
		   schedulers = ["Normal"],
		   preemptions = [True],
		   preemptiveDiscard = False,
		   queue = "LCFS",
		   serviceType = "erlang2",
		   arrivalType = "poisson",
		   verbose="True"):
	ages = []
	for preemption,scheduler,rate, num_source in itertools.product(preemptions,schedulers,arrivalRate,num_sources):
		net = myNetwork.Network(num_source=num_source,
							  num_packet=num_packet,
							  arrival=(arrivalType,[rate]),
							  service=(serviceType,[num_source]),
							  queue=queue,
							  preemption=preemption,
							  preemptiveDiscard=preemptiveDiscard,
							  scheduler=scheduler)
		net.run()
		average_age = []
		for record in net.freshstory:
			average_age.append(float(analyze.calculate_average_age(record)))

		if verbose:
			print(rate,num_source,scheduler,preemption,average_age)
		ages.append(average_age[0])

	return ages


if __name__ == "__main__":

	MATLAB = True

	if MATLAB:
		import matlab.engine

		eng = matlab.engine.start_matlab("-desktop background")

	# ages = runSim()




