import numpy as np
import math
import random
import json
# import analyze

class Network(object):
    def __init__(self,
                 num_source = 5,
               num_server = 1,
               num_packet = 20000,
               arrival = ("poisson",[1]*5),
               service = ("exponential",[0.1]*5),
               queue = "FCFS",
               preemption = False,
               scheduler = "MAF"):

        self.num_source = num_source
        self.num_packet = num_packet
        self.num_server = num_server
        self.arrivalsetting = arrival
        self.service = service
        self.queue = queue
        self.preemption = preemption
        self.scheduler = scheduler

        self.packet_generator(num_packet,num_source,arrival)
        self.Queue = self.Queue(queue,num_source)
        self.Service = self.Service(num_source,num_packet,num_server,service)
        self.Scheduler = self.Scheduler(scheduler,preemption,num_source,self)

        self.currenttime = 0
        self.arrival = []
        self.story = [[[0,0]] for i in range(num_source)]
        self.freshstory = [[[0, 0]] for i in range(num_source)]
        # self.freshness = [True for i in range(num_source)]
        self.departure = math.inf
        self.termination = False

    class Queue(object): # Stores arrival time of waiting packets
        def __init__(self,queue,num_source):
            self.Qtype = queue
            self.waiting = [[]]*num_source #TODO story de yaptığımız gibi tanımlamak lazım
        def add(self,source_id,packet):
            source_id = int(source_id)
            if self.Qtype == "FCFS":
                self.waiting[source_id] = [packet] + self.waiting[source_id]
            elif self.Qtype == "LCFS":
                self.waiting[source_id] = self.waiting[source_id] + [packet]
        def delete(self,source_id):
            if self.waiting[source_id]:
                return self.waiting[source_id].pop()
            else: return -1
        def nextvalue(self,source_id):
            return self.waiting[source_id][-1]
        def preempt(self,source_id,packet):
            self.waiting[source_id] = self.waiting[source_id] + [packet]


    def packet_generator(self,num_packet,num_source,arrival,seed = 0):
        if arrival[0] == "poisson":
            self.arr = np.random.exponential(np.divide(1,arrival[1]),(num_packet,num_source))
        elif arrival[0] == "deterministic":
            self.arr = np.ones((num_packet,num_source))*arrival[1]

        self.arr = np.cumsum(self.arr,0)
        self.generatecontrolinstances(num_source, num_packet,self.arr)

        self.arr = np.insert(self.arr,0,0,axis=0)
        self.arr = self.arr.T

    def generatecontrolinstances(self,num_source,num_packet,arr):
        b = arr.flatten()
        index = np.mod(b.argsort(),num_source)
        b.sort()
        self.controlSteps = np.concatenate([[b],[index]]).T.tolist()

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
        def MAF(self,time):
        # TODO: decide schedule among age-effective and exist packets. Burası daha iyi olabilir
            inst_age = [time - item[-1][1] for item in self.network.story] # Calculates the inst. age by currentTime - lastDeparture
            nonempties = list(filter(lambda x: self.network.Queue.waiting[int(x)] != [], range(self.num_source)))
            cand_ids = []
            max_age = 0
            for x in nonempties:
                if inst_age[x] > max_age:
                    max_age = inst_age[x]
                    cand_ids = [x]
                elif inst_age[x] == max_age:
                    cand_ids.append(x)

            if len(cand_ids) > 0:
                return int(random.choice(cand_ids))
            else:
                return []
        def MAD(self,time):
            pass

    class Service(object):
        def __init__(self,num_source,num_packet,num_server,service,seed = 15):
            self.arg = [num_source,num_packet,num_server,service,seed]

            if service[0] == "exponential":
                self.servicetime = np.random.exponential(np.divide(1,service[1]),(num_packet,num_source))
            elif service[0] == "determisinistic":
                self.servicetime = np.ones((num_packet, num_source)) * service[1]
            self.servicetime = self.servicetime.T.tolist()

        def time(self,source_id):
            if not self.servicetime[source_id]:
                self.__init__(*self.arg)
            return self.servicetime[source_id].pop(0)

    # def newService(self,source_id):
    #     self.arrival = self.Queue.delete(int(source_id))
    #     self.departure = self.currenttime + self.Service.time(source_id)
    #     self.Service.id = source_id

    def newService(self,source_id):
        source_id = int(source_id)
        self.arrival = self.Queue.nextvalue(source_id)
        self.departure = self.currenttime + self.Service.time(source_id)

    def completeService(self,source_id):
        source_id = int(source_id)
        self.Queue.delete(source_id)
        self.store(source_id, self.arrival, self.departure)  # Complete service
        if self.arrival > self.freshstory[source_id][-1][0]:
            self.freshstore(source_id, self.arrival, self.departure)  # Age effective Complete service

    # def freshcompleteService(self,source_id):
    #     if self.arrival > self.freshstory[int(source_id)][-1][0]:
    #         self.freshstore(int(source_id), self.arrival, self.departure)  # Age effective Complete service
    #         # self.freshness[int(source_id)] = False

    def controller(self):
        if not (self.controlSteps or any(self.Queue.waiting)):
            print("END OF SIMULATION")
            self.termination = True
            return 0

        if self.preemption: # LCFS-preemptive için
            source_id = self.Scheduler.nextmove(self.currenttime)

            if source_id == []:
                self.currenttime, source_id = self.controlSteps.pop(0)
                self.Queue.add(source_id, self.currenttime)
            # else:
            #     arrivaltime = self.Queue.nextvalue(source_id)
            self.newService(source_id)
            if len(self.controlSteps) and self.controlSteps[0][0] < self.departure:
                (arrivaltime_ib, source_id_ib) = self.controlSteps.pop(0)
                self.Queue.add(source_id_ib, arrivaltime_ib)
                self.currenttime = arrivaltime_ib
                new_source_id = self.Scheduler.nextmove(self.currenttime)
                if not(source_id == source_id_ib or (new_source_id != source_id)):
                    # NO PREEMPTION
                    self.currenttime = self.departure
                    self.completeService(source_id)
            else:
                self.currenttime = self.departure
                self.completeService(source_id)


        else: # LCFS-nonpreemptive ve FCFS için #TODO LCFS-nonpreemptive çalışmıyor!!! (rate=1 --> age=5)
            source_id = self.Scheduler.nextmove(self.currenttime)

            if source_id == []:
                self.currenttime, source_id = self.controlSteps.pop(0)
                self.Queue.add(source_id, self.currenttime)

            self.newService(source_id)
            while len(self.controlSteps) and self.controlSteps[0][0] < self.departure:
                (arrivaltime_ib, source_id_ib) = self.controlSteps.pop(0)
                self.Queue.add(source_id_ib, arrivaltime_ib)
            self.currenttime = self.departure
            self.completeService(source_id)

    def run(self):
        while not self.termination:
            self.controller()

if __name__ == "__main__":
    import analyze

    database = []
    num_source = 1
    logging = False


    for arrRate in [0.5]:
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


