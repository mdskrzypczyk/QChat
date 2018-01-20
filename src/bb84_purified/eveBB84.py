from SimulaQron.cqc.pythonLib.cqc import *

import random

def relay_bb84_states(cqc, n, p):
    known_info = []
    for i in range(n):
        q = cqc.recvEPR()
        r = random.random()
        if r <= p:
            print("Eve intercepting qubit")
            r = random.randint(0,1)

            if r:
                q.H()

            q_val = q.measure()
            known_info.append((i, r, q_val))
            q = qubit(cqc)

            if r:
                q.H()
        cqc.sendQubit(q, "Bob")

    print("Eve side info: ", known_info)


def main():
    numbits = 100
    p = 0.1
    Eve = CQCConnection("Eve")
    relay_bb84_states(Eve, numbits, p)

    Eve.close()

if __name__=='__main__':
    main()