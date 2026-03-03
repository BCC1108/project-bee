from tqdm import tqdm , trange
import time

#for i in tqdm.tqdm(range(1,100001)):
#    time.sleep(.001)
    
#for i in tqdm.trange(2000):
#    time.sleep(.01)
    
#with tqdm.tqdm(total = 200) as pbar:
#    for i in range(20):
#        pbar.update(10)
#        time.sleep(.1)

#p=1
#pbar = trange(1000)
#for i in pbar:
    #pbar.set_description(f'正在计算{i=:02d}')
    #p *= (i+1)
    #print(f'{p=:,}') 
    
pbar = tqdm(total = 1000)
p = 1
n = 100

#for i in range(n):
#    pbar.update(1000/n)
#    pbar.set_description(f'正在计算{i=:02d}')
#   p = p * (i+1)
#    time.sleep(0.05)
#pbar.close()
#print(f'{p=:,}')


        