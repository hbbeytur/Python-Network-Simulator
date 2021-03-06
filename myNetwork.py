import numpy as np
import math
import random
import json

np.random.seed(0)

class Network(object):
    def __init__(self,
                 num_source = 5,
                 num_server = 1,
                 num_packet = 10000,
                 arrival = ("poisson",[1]*5),
                 service = ("exponential",[0.1]*5),
                 queue = "FCFS",
                 queueSize = math.inf,
                 preemption = True,
                 scheduler = "Normal", #MAF, Normal, Normal-DISCARD, MAD
                 preemptiveDiscard = False,
                 verbose = False):

        self.num_source = num_source
        self.num_packet = num_packet
        self.num_server = num_server
        self.arrivalsetting = arrival
        self.service = service
        self.queue = queue
        self.queueSize = queueSize
        self.preemption = preemption
        self.scheduler = scheduler
        self.preemptiveDiscard = preemptiveDiscard
        self.verbose = verbose

        self.packet_generator(num_packet,num_source,arrival)
        self.Queue = self.Queue(queue,num_source,queueSize)
        self.Service = self.Service(num_source,num_packet,num_server,service)
        self.Scheduler = self.Scheduler(scheduler,preemption,num_source,self)

        self.currenttime = 0
        self.inservice = []
        self.preempted = []
        self.story = [[[0,0]] for i in range(num_source)]
        self.freshstory = [[[0, 0]] for i in range(num_source)]
        self.departure = math.inf
        self.termination = False

    class Queue(object): # Stores arrival time of waiting packets
        def __init__(self,queue,num_source,queueSize):
            self.Qtype = queue
            self.size = queueSize
            self.waiting = [[]]*num_source #TODO story de yaptığımız gibi tanımlamak lazım
        def add(self,source_id,packettime):
            if self.Qtype == "FCFS":
                self.waiting[source_id] = [packettime] + self.waiting[source_id]
            elif self.Qtype == "LCFS":
                self.waiting[source_id] = self.waiting[source_id] + [packettime]
            if self.size != math.inf: # Buffer size limit: when the queue is full new packets are discarded <FCFS> (old packets are discarded <LCFS>)
                self.waiting[source_id] = self.waiting[source_id][-self.size:]
        def delete(self,source_id):
            return self.waiting[source_id].pop()
        def nextvalue_delete(self,source_id):
            return self.waiting[source_id].pop()
        def nextvalue(self,source_id):
            return self.waiting[source_id][-1]

    def packet_generator(self,num_packet,num_source,arrival,seed = 0):
        if arrival[0] == "poisson":
            self.arr = np.random.exponential(np.divide(1,arrival[1]),(num_packet,num_source))
        elif arrival[0] == "deterministic":
            self.arr = np.ones((num_packet,num_source))*arrival[1]
        elif arrival[0] == "erlang2":
            self.arr = np.random.gamma(2,np.divide(1,arrival[1]),(num_packet,num_source))

        self.arr = np.cumsum(self.arr,0)
        self.generatecontrolinstances(num_source, num_packet,self.arr)

        self.arr = np.insert(self.arr,0,0,axis=0)
        self.arr = self.arr.T

    def generatecontrolinstances(self,num_source,num_packet,arr):
        b = arr.flatten()
        index = np.mod(b.argsort(),num_source).astype(int)
        b.sort()
        self.controlSteps = [[x,y] for x,y in zip(b,index)]
    def store(self,source_id,arrival,departure):
        self.story[source_id].append([arrival,departure])

    def freshstore(self,source_id,arrival,departure):
        self.freshstory[source_id].append([arrival,departure])

    class Scheduler(object):
        def __init__(self,scheduler,preemption,num_source,network):
            self.scheduler = scheduler
            self.num_source = num_source
            self.network = network
        def nextmove(self,time):
            if self.scheduler == "MAF":
                return self.MAF(time)
            elif self.scheduler == "MAD":
                return self.MAD(time)
            elif self.scheduler == "Normal":
                return self.Normal()
        def MAF(self,time):
            self.nonempties = list(filter(lambda x: self.network.Queue.waiting[x] != [], range(self.num_source)))
            # self.ageeffectives = list(filter(lambda x: self.network.Queue.waiting[x][-1] > self.network.freshstory[x][-1][0], self.nonempties))
            self.ageeffectives = self.nonempties
            if self.ageeffectives:
                self.inst_age = [time - self.network.freshstory[i][-1][0] for i in self.ageeffectives]
                self.cand = np.argwhere(np.amax(self.inst_age) == self.inst_age).ravel()
                self.cand_ids = [self.ageeffectives[i] for i in self.cand]
            else:
                self.cand_ids = self.nonempties
            return self.returnID()

        def MAD(self,time):
            self.nonempties = list(filter(lambda x: self.network.Queue.waiting[x] != [], range(self.num_source)))
            # self.ageeffectives = list(filter(lambda x: self.network.Queue.waiting[x][-1] > self.network.freshstory[x][-1][0],self.nonempties))
            self.ageeffectives = self.nonempties
            if self.ageeffectives:
                self.inst_age = [self.network.Queue.waiting[i][-1] - self.network.freshstory[i][-1][0] for i in self.ageeffectives]
                self.cand = np.argwhere(np.amax(self.inst_age) == self.inst_age).ravel()
                self.cand_ids = [self.ageeffectives[i] for i in self.cand]
            else:
                self.cand_ids = self.nonempties
            return self.returnID()

        def randomScheduler(self):
            self.cand_ids = list(filter(lambda x: self.network.Queue.waiting[x] != [], range(self.num_source)))
            return self.returnID()

        def Normal(self):
            self.nonempties = list(filter(lambda x: self.network.Queue.waiting[x] != [], range(self.num_source)))
            nonempty_values = [self.network.Queue.waiting[x][-1] for x in self.nonempties]

            if nonempty_values == []:
                self.cand_ids = []
            elif self.network.queue == "FCFS":
                self.cand = np.argwhere(nonempty_values == np.amin(nonempty_values)).ravel()
                self.cand_ids = [self.nonempties[i] for i in self.cand]
            elif self.network.queue == "LCFS":
                self.cand = np.argwhere(nonempty_values == np.amax(nonempty_values)).ravel()
                self.cand_ids = [self.nonempties[i] for i in self.cand]
            return self.returnID()

        def returnID(self):
            if len(self.cand_ids) > 0:
                return int(random.choice(self.cand_ids))
            else:
                return []

    class Service(object):
        def __init__(self,num_source,num_packet,num_server,service,seed = 15):
            self.arg = [num_source,num_packet,num_server,service,seed]

            self.service = service

            if service[0] == "exponential":
                self.servicetime = np.random.exponential(np.divide(1,service[1]),(num_packet,num_source))
            elif service[0] == "determisinistic":
                self.servicetime = np.ones((num_packet, num_source)) * service[1]
            elif service[0] == "erlang2":
                self.servicetime = np.random.gamma(2,np.divide(1, np.multiply(2,service[1])), (num_packet, num_source))
            self.servicetime = self.servicetime.T.tolist()

        def time(self,source_id):
            if not self.servicetime[source_id]:
                self.__init__(*self.arg)
            return self.servicetime[source_id].pop(0)

    def newService(self,source_id):
        self.inservice = [self.Queue.nextvalue_delete(source_id), source_id]
        if self.preempted != []:
            self.Queue.add(self.preempted[1],self.preempted[0])
            self.preempted = []
        self.servicetime = self.Service.time(source_id)
        self.departure = self.currenttime + self.servicetime

    def completeService(self,source_id):
        self.store(source_id, self.inservice[0], self.departure)  # Complete service
        if self.inservice[0] > self.freshstory[source_id][-1][0]:
            self.freshstore(source_id, self.inservice[0], self.departure)  # Age effective Complete service

    def controller(self):
        if not (self.controlSteps or any(self.Queue.waiting)):
            if self.verbose:
                print("END OF SIMULATION")
            self.termination = True
            return 0

        source_id = self.Scheduler.nextmove(self.currenttime)

        if source_id == []: # Queues are empty
            self.currenttime, source_id = self.controlSteps.pop(0)
            self.Queue.add(source_id, self.currenttime)

        self.newService(source_id)

        if self.preemption: # LCFS-preemptive için
            source_id_new = []
            source_id_action = source_id
            if len(self.controlSteps) and self.controlSteps[0][0] < self.departure:
                (self.currenttime, source_id_new) = self.controlSteps.pop(0)
                self.Queue.add(source_id_new, self.currenttime)
                source_id_action = self.Scheduler.nextmove(self.currenttime)
            if (source_id == source_id_new or (source_id_action != source_id)) and not(self.preemptiveDiscard): # PREEMPTION
                self.preempted = self.inservice
            else:
                self.currenttime = self.departure
                self.completeService(source_id)
        else: # LCFS-nonpreemptive ve FCFS için #TODO LCFS-nonpreemptive çalışmıyor!!! (rate=1 --> age=5)
            while len(self.controlSteps) and self.controlSteps[0][0] < self.departure:
                (arrivaltime_new, source_id_new) = self.controlSteps.pop(0)
                self.Queue.add(source_id_new, arrivaltime_new)
            self.currenttime = self.departure
            self.completeService(source_id)

    def run(self):
        while not self.termination:
            self.controller()

if __name__ == "__main__":
    import analyze

    database = []
    num_source = 3
    logging = False

    for arrRate in [1]:
        print(arrRate)
        net = Network(num_source= num_source,queue="LCFS",arrival=("poisson",[arrRate]),service=("exponential",[1]*num_source))
        net.run()

        ## CALCULATE Average Age per user
        average_age = []
        for record in net.freshstory:
            average_age.append(analyze.calculate_average_age(record))

        print(average_age)

        if logging:
            database.append({'num_source': net.num_source,
                             'num_server': net.num_server,
                             'num_packet': net.num_packet,
                             'arrival': net.arrivalsetting,
                             'service': net.service,
                             'queue': net.queue,
                             'preemption': net.preemption,
                             'scheduler': net.scheduler,
                             'story': net.story})
    if logging:
        with open("records/twoUser_FCFS_poisson_exponential.txt","w") as f:
            json.dump(database,f)


