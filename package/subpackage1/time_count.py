import time

sum_t=0.0            #花費的總時間
def time_start():
    global timeStart
    timeStart = time.time() #開始計時
    
def time_reset():
    global sum_t
    sum_t=0.0

def time_end():
    global sum_t, timeStart
    timeEnd = time.time()    #結束計時
    sum_t = (timeEnd - timeStart) + sum_t   #執行所花時間
    print('time cost', sum_t, 's')