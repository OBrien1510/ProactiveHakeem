from ProactiveApi import ProactiveApi
import time


p = ProactiveApi()

while True:

    p.checkUserActivity()
    print("waiting")
    time.sleep(60)

