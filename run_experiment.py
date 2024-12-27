import os
import time
import l4s_experiment
 

#test(data_rate=100, RTT=20, competing_CC="cubic", ecn=1, aqm="dualpi2", ecn_fallback=0, run=1, out_folder="result"):
def ecn():
    for i in range(10):
        l4s_experiment.test(run=i+1, aqm="FIFO",     out_folder="result/ECN1/fifo")
        l4s_experiment.test(run=i+1, aqm="FIFO+ECN", out_folder="result/ECN1/fifoWithEcn")
        l4s_experiment.test(run=i+1, aqm="CoDel",    out_folder="result/ECN1/CoDel")
        l4s_experiment.test(run=i+1, aqm="dualpi2",  out_folder="result/ECN1/dualpi2")
    
def no_ecn():
    for i in range(10):
        l4s_experiment.test(run=i+1, ecn=0, aqm="FIFO",     out_folder="result/noECN/fifo")
        l4s_experiment.test(run=i+1, ecn=0, aqm="FIFO+ECN", out_folder="result/noECN/fifoWithEcn")
        l4s_experiment.test(run=i+1, ecn=0, aqm="CoDel",    out_folder="result/noECN/CoDel")
        l4s_experiment.test(run=i+1, ecn=0, aqm="dualpi2",  out_folder="result/noECN/dualpi2")
        
def ecn_fallback():
    for i in range(10):
        l4s_experiment.test(run=i+1, ecn_fallback=1, aqm="FIFO",     out_folder="result/ECN_fallback/fifo")
        l4s_experiment.test(run=i+1, ecn_fallback=1, aqm="FIFO+ECN", out_folder="result/ECN_fallback/fifoWithEcn")
        l4s_experiment.test(run=i+1, ecn_fallback=1, aqm="CoDel",    out_folder="result/ECN_fallback/CoDel")
        l4s_experiment.test(run=i+1, ecn_fallback=1, aqm="dualpi2",  out_folder="result/ECN_fallback/dualpi2")



if __name__ == "__main__":
    ecn()
    ecn_fallback()
    no_ecn()

