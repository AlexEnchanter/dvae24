import os
import time
import l4s_experiment
 
delays = [4, 10, 20, 40, 80, 100]
rates = [5, 10, 20, 40, 80, 100, 400]
#test(data_rate=100, RTT=20, competing_CC="cubic", ecn=1, aqm="dualpi2", ecn_fallback=0, run=1, out_folder="result"):
for delay in delays:
    for rate in rates:
        for i in range(3):
            l4s_experiment.test(run=i+1, aqm="dualpi2", out_folder=f"result/dualpi2/{delay}/{rate}", ecn_fallback=1)
