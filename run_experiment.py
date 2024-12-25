import os
import time
import l4s_experiment
 

#test(data_rate=100, RTT=20, competing_CC="cubic", ecn=1, aqm="dualpi2", ecn_fallback=0, run=1, out_folder="result"):
def default_ten_runs():
    for i in range(10):
        l4s_experiment.test(run=i+1, out_folder="result/ECN1")
    
def no_ecn():
    for i in range(10):
        l4s_experiment.test(run=i+1, ecn=0, out_folder="result/noECN")
        
def ecn_fallback():
    for i in range(10):
        l4s_experiment.test(run=i+1, ecn_fallback=1, out_folder="result/ECN_fallback")



if __name__ == "__main__":
    default_ten_runs()
    ecn_fallback()
    no_ecn()

