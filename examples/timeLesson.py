from datetime import datetime , timezone
import time

#time → timestamp
dt = datetime(2026,1,20,0,0,tzinfo=timezone.utc)
ts_sec = int(dt.timestamp())
ts_ms = ts_sec * 1000

time_now = datetime.now()
time_now_utc = datetime.now(timezone.utc)
ts_sec_now = int(time.time())
ts_ms_now = int(time.time())*1000

#timestamp → time

ts_sec_before = ts_sec_now - 300
ts_ms_before = ts_sec_before * 1000

dt_before = datetime.fromtimestamp(ts_sec_before,tz=timezone.utc)

print(f'{time_now_utc} 表示 {ts_ms_now}')
print(f'{dt_before} 表示 {ts_ms_before}')



