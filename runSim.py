import myNetwork, analyze
import numpy as np
import itertools

def runSim(num_packet = 30000,
		   num_sources=range(1,2),
		   arrivalRate = np.linspace(0.1,5,10),
		   schedulers = ["Normal"],
		   preemptions = [True],
		   queue = "LCFS",
		   serviceType = "erlang2",
		   arrivalType = "poisson"):
	ages = []
	for rate, num_source,scheduler,preemption in itertools.product(arrivalRate,num_sources,schedulers,preemptions):
		print(rate,num_source,scheduler,preemption)
		net = myNetwork.Network(num_source=num_source,
							  num_packet=num_packet,
							  arrival=(arrivalType,[rate]),
							  service=(serviceType,[1]*num_source),
							  queue=queue,
							  preemption=preemption,
							  preemptiveDiscard=False,
							  scheduler=scheduler)
		net.run()
		average_age = []
		for record in net.freshstory:
			average_age.append(float(analyze.calculate_average_age(record)))

		print(average_age)
		ages.append(average_age)

	return ages


if __name__ == "__main__":

	MATLAB = True

	if MATLAB:
		import matlab.engine

		eng = matlab.engine.start_matlab("-desktop background")
		eng.doc(nargout=0)

	ages = runSim()




