import numpy as np

# Golay Matrix for error correction
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

# Hamming Matrix for error correction
H_Hamming = np.matrix([[1, 0, 1, 0, 1, 0, 1],
                       [0, 1, 1, 0, 0, 1, 1],
                       [0, 0, 0, 1, 1, 1, 1]])


def getSyndrome(H, v):
    """
    Calculates the syndrome string given a matrix and codeword
    :param H:
    :param v:
    :return:
    """
    s = (H*v) % 2
    return s.reshape(1, 11)


def eVect(length, position):
    """
    Helper for constructing a zero vector of specified length with a 1 in the specified position
    :param length: Length of the zero vector
    :param position: Position of the 1
    :return: Constructed vector
    """
    vec = [0 for _ in range(length)]
    vec[-position] = 1
    return np.matrix(vec)


class ECC:
    """
    Base class that implements linear code encoding/decoding interface
    """
    def __init__(self):
        raise Exception("ECC class does not implement detailed functionality, try ECC_Golay or ECC_Hamming")

    def chunk(self, x):
        """
        Chunks a list of 0/1's into the ECC objects processing codeword length
        :param x:
        :return:
        """
        return [x[i:i+self.codeword_length] for i in range(0, len(x), self.codeword_length)]

    def encode(self, x):
        """
        Encodes a specified codeword into a JSON-able syndrome string
        :param x: The codeword to encode
        :return: An encoding of the codeword
        """
        s = getSyndrome(self.H, np.matrix(x).reshape(self.codeword_length, 1))
        return tuple(s.tolist()[0])

    def decode(self, x, s):
        """
        Corrects errors in the received codeword x using the provided encoding information s
        :param x: The codeword we wish to correct
        :param s: The original codeword's syndrome information
        :return: A corrected version of the codeword
        """
        xm = np.matrix(x).reshape(self.codeword_length, 1)
        sm = np.matrix(s)
        s_hat = getSyndrome(self.H, xm)
        cs = (sm + s_hat) % 2
        em = self.dict_H[tuple(cs.tolist()[0])]
        xm = (xm.reshape(1, self.codeword_length) + em) % 2
        return xm.tolist()[0]


class ECC_Golay(ECC):
    codeword_length = 23

    def __init__(self):
        """
        Initializes Golay error correcting code matrix for use with ECC
        """
        self.H = H_Golay
        self.dict_H = {}

        # Set the zero syndrome cases to the zero error string
        s = (0,)*11
        self.dict_H[s] = (0,)*23

        # Construct the syndrome -> error string mapping for 1, 2, and 3 bit errors
        for i in range(1, 24):
            # 1 bit errors
            vi = eVect(23, i)
            s = self.encode(vi)
            self.dict_H[s] = tuple(vi.tolist())

            for j in range(i+1, 24):
                # 2 bit errors
                vj = eVect(23, j)
                v_ij = vi + vj
                s = self.encode(v_ij)
                self.dict_H[s] = tuple(v_ij.tolist())

                for k in range(j+1, 24):
                    # 3 bit errors
                    vk = eVect(23, k)
                    v_ijk = v_ij + vk
                    s = self.encode(v_ijk)
                    self.dict_H[s] = tuple(v_ijk.tolist())


class ECC_Hamming(ECC):
    codeword_length = 7

    def __init__(self):
        """
        Initializes Hamming error correcting code matrix for use with ECC
        """
        self.H = H_Hamming
        self.dict_H = {}

        # Sets the zero syndrome case to the zero error string
        s = np.zeros(3)
        self.dict_H[s] = np.zeros(7)

        # Construct the syndrome -> error string mapping for single bit errors
        for i in range(1, 24):
            vi = eVect(23, i)
            s = getSyndrome(H_Golay, vi)
            self.dict_H[s] = vi
