from SimulaQron.cqc.pythonLib.cqc import *

import random

def sendClassicalAssured(cqc, target, data):
    cqc.sendClassical(target, data)
    while bytes(cqc.recvClassical(msg_size=3)) != b'ACK':
        pass

def recvClassicalAssured(cqc, target):
    data = list(cqc.recvClassical())
    cqc.sendClassical(target, list(b'ACK'))
    return data

def receive_bb84_states(cqc, target, n):
    x = []
    theta = []
    while len(x) < n:
        q = cqc.recvQubit()
        basisflip = random.randint(0,1)
        if basisflip:
            q.H()

        theta.append(basisflip)
        x.append(q.measure())
        sendClassicalAssured(cqc, "Alice", list(b'ACK'))

    return x, theta


def filter_theta(cqc, target, x, theta):
    x_remain = []
    theta_hat = recvClassicalAssured(cqc, target)
    sendClassicalAssured(cqc, target, theta)
    for bit, basis, basis_hat in zip(x, theta, theta_hat):
        if basis == basis_hat:
            x_remain.append(bit)

    return x_remain


def estimate_error_rate(cqc, target, x, num_test_bits):
    test_bits = []
    test_indices = recvClassicalAssured(cqc, target)
    for index in test_indices:
        test_bits.append(x.pop(index))

    print("Bob test indices: ", test_indices)
    print("Bob test bits: ", test_bits)

    sendClassicalAssured(cqc, target, test_bits)
    target_test_bits = recvClassicalAssured(cqc, target)

    print("Bob target_test_bits: ", target_test_bits)
    num_error = 0
    for t1, t2 in zip(test_bits, target_test_bits):
        if t1 != t2:
            num_error += 1

    return (num_error / num_test_bits)


def extract_key(x, r):
    return (sum([xj*rj for xj, rj in zip(x, r)]) % 2)

def main():
    numbits = 100
    num_test_bits = numbits // 4

    Bob = CQCConnection("Bob")
    x, theta = receive_bb84_states(Bob, "Alice", numbits)
    print("Bob x: ", x)
    print("Bob theta: ", theta)

    sendClassicalAssured(Bob, "Alice", list(b'BB84DISTACK'))
    x_remain = filter_theta(Bob, "Alice", x, theta)
    print("Bob x_remain: ", x_remain)

    error_rate = estimate_error_rate(Bob, "Alice", x_remain, num_test_bits)
    print("Bob error_rate: ", error_rate)

    r = recvClassicalAssured(Bob, "Alice")
    print("Bob R: ", r)
    print("Bob key bits: ", x_remain)

    k = extract_key(x_remain, r)
    print("Bob k: ", k)

    Bob.close()

if __name__=='__main__':
    main()