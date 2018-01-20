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

def distribute_bb84_states(cqc, target, n):
    x = []
    theta = []
    while len(x) < n:
        q = cqc.createEPR("Eve")
        bitflip = random.randint(0,1)
        if bitflip:
            q.X()
        basisflip = random.randint(0,1)
        if basisflip:
            q.H()

        x.append(q.measure())
        theta.append(basisflip)

        recvClassicalAssured(cqc, "Bob")

    return x, theta


def filter_theta(cqc, target, x, theta):
    x_remain = []
    sendClassicalAssured(cqc, target, theta)
    theta_hat = recvClassicalAssured(cqc, target)
    for bit, basis, basis_hat in zip(x, theta, theta_hat):
        if basis == basis_hat:
            x_remain.append(bit)

    return x_remain

def estimate_error_rate(cqc, target, x, num_test_bits):
    test_bits = []
    test_indices = []

    while len(test_indices) < num_test_bits and len(x) > 0:
        index = random.randint(0, len(x) - 1)
        test_bits.append(x.pop(index))
        test_indices.append(index)

    print("Alice finding {} test bits".format(num_test_bits))
    print("Alice test indices: ", test_indices)
    print("Alice test bits: ", test_bits)

    sendClassicalAssured(cqc, target, test_indices)
    target_test_bits = recvClassicalAssured(cqc, target)
    sendClassicalAssured(cqc, target, test_bits)
    print("Alice target_test_bits: ", target_test_bits)

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

    Alice = CQCConnection("Alice")

    x, theta = distribute_bb84_states(Alice, "Eve", numbits)
    print("Alice x: ", x)
    print("Alice theta: ", theta)

    m = bytes(recvClassicalAssured(Alice, "Bob"))
    if m != b'BB84DISTACK':
        print(m)
        raise RuntimeError("Failure to distributed BB84 states")

    x_remain = filter_theta(Alice, "Bob", x, theta)
    print("Alice x_remain: ", x_remain)

    error_rate = estimate_error_rate(Alice, "Bob", x_remain, num_test_bits)
    print("Alice error rate: ", error_rate)

    if error_rate > 1:
        raise RuntimeError("Error rate of {}, aborting protocol")

    r = [random.randint(0, 1) for _ in x_remain]
    sendClassicalAssured(Alice, "Bob", r)
    k = extract_key(x_remain, r)

    print("Alice R: ", r)
    print("Alice key_bits: ", x_remain)
    print("Alice k: ", k)

    Alice.close()

if __name__=='__main__':
    main()