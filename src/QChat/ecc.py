import numpy as np


H_Golay = np.matrix([[1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                     [1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                     [1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                     [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                     [1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                     [1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                     [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                     [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]])

H_Hamming = np.matrix([[1, 0, 1, 0, 1, 0, 1],
                       [0, 1, 1, 0, 0, 1, 1],
                       [0, 0, 0, 1, 1, 1, 1]])

def getSyndrome(H, v):
    s = (H*v) % 2
    return s.reshape(1, 11)

def eVect(length, position):
    l = [0 for _ in range(length)]
    l[-position] = 1
    return np.matrix(l)


class ECC:
    def __init__(self):
        self.H = None
        self.dict_H = {}
        self.codeword_length = 0

    def chunk(self, x):
        return [x[i:i+self.codeword_length] for i in range(0, len(x), self.codeword_length)]

    def encode(self, x):
        s = getSyndrome(self.H, np.matrix(x).reshape(23, 1))
        return tuple(s.tolist()[0])

    def decode(self, x, s):
        xm = np.matrix(x).reshape(23, 1)
        sm = np.matrix(s)
        s_hat = getSyndrome(self.H, xm)
        cs = (sm + s_hat) % 2
        em = self.dict_H[tuple(cs.tolist()[0])]
        xm = (xm.reshape(1, 23) + em) % 2
        return xm.tolist()[0]

class ECC_Golay(ECC):
    def __init__(self):
        self.codeword_length = 23
        self.H = H_Golay
        self.dict_H = {}
        s = (0,)*11
        self.dict_H[s] = (0,)*23
        for i in range(1, 24):
            vi = eVect(23, i)
            s = self.encode(vi)
            self.dict_H[s] = tuple(vi.tolist())
            for j in range(i+1, 24):
                vj = eVect(23, j)
                v_ij = vi + vj
                s = self.encode(v_ij)
                self.dict_H[s] = tuple(v_ij.tolist())
                for k in range(j+1, 24):
                    vk = eVect(23, k)
                    v_ijk = v_ij + vk
                    s = self.encode(v_ijk)
                    self.dict_H[s] = tuple(v_ijk.tolist())


class ECC_Hamming(ECC):
    def __init__(self):
        self.codeword_length = 7
        self.H = H_Hamming
        self.dict_H = {}
        s = np.zeros(3)
        self.dict_H[s] = np.zeros(7)
        for i in range(1, 24):
            vi = eVect(23, i)
            s = getSyndrome(H_Golay, vi)
            self.dict_H[s] = vi
