import math
import numpy as np
from numpy import matlib
from numpy.linalg import LinAlgError

np.set_printoptions(precision=3)


class IllsmError(LinAlgError):
    pass


def weights(A):
    M = A.copy()
    L = laplacian(A)[:-1, :-1]
    if np.linalg.det(L) == 0:
        raise IllsmError("The matrix is not connected, please provide additional elements")
    Lsize = L.shape[0]
    RHS = matlib.zeros([Lsize, 1])
    for j in range(Lsize):
        ColumnProduct = 1
        for i in range(Lsize+1):
            if M[i, j] == 0:
                M[i, j] = 1
            ColumnProduct = ColumnProduct * M[i, j]
        RHS[j,0] = - math.log(ColumnProduct)
    y = np.linalg.inv(L)*RHS
    w = np.matrix([math.exp(elem) for elem in y] + [1])
    w = w / w.sum()
    return w

def laplacian(A):
    """
    Expects a numpy nd-array, returns the laplacian matrix
    """
    matrixsize = max(A.shape)
    M = A.copy()
    L = matlib.zeros((matrixsize, matrixsize))

    # Az i-edik diagonális elem mindig az i-edik fokszáma
    diag = []
    for i in range(matrixsize):
        deg = matrixsize - 1
        for j in range(matrixsize):
            if M[i,j] == 0:
                deg -= 1
        diag.append(deg)
    np.fill_diagonal(L, diag)


    # Ha (i,j)\in E akkor -1, egyébként 0
    for i in range(matrixsize):
        for j in range(i + 1, matrixsize):
            if M[i,j]:
                L[i,j] = -1
                L[j,i] = -1
    return L
def test():
    A = np.matrix([
        [1, 5, 3, 7, 6, 6, 1/3, 1/4],
        [1/5, 1, 0, 5, 0, 3, 0, 1/7],
        [1/3, 0, 1, 0, 3, 0, 6, 0],
        [1/7, 1/5, 0, 1, 0, 1/4, 0, 1/8],
        [1/6, 0, 1/3, 0, 1, 0, 1/5, 0],
        [1/6, 1/3, 0, 4, 0, 1, 0, 1/6],
        [3, 0, 1/6, 0, 5, 0, 1, 0],
        [4, 7, 0, 8, 0, 6, 0, 1]
    ])
    w = weights(A)
    return w
A = np.matrix([
    [1, 5, 3, 7, 6, 6, 1/3, 1/4],
    [1/5, 1, 0, 5, 0, 3, 0, 1/7],
    [1/3, 0, 1, 0, 3, 0, 6, 0],
    [1/7, 1/5, 0, 1, 0, 1/4, 0, 1/8],
    [1/6, 0, 1/3, 0, 1, 0, 1/5, 0],
    [1/6, 1/3, 0, 4, 0, 1, 0, 1/6],
    [3, 0, 1/6, 0, 5, 0, 1, 0],
    [4, 7, 0, 8, 0, 6, 0, 1]
])
