import numpy as np
import networkx as nx
import torch_geometric as tg

def make_undirected(mat):
    """Takes an input adjacency matrix and makes it undirected (symmetric).

    Parameters
    ----------
    mat: array
        Square adjacency matrix.

    Raises
    ------
    ValueError
        If input matrix is not square.

    Returns
    -------
    array
        Symmetric input matrix. If input matrix was unweighted, output is also unweighted.
        Otherwise, output matrix is average of corresponding connection strengths of input matrix.
    """
    if not (mat.shape[0] == mat.shape[1]):
        raise ValueError('Adjacency matrix must be square.')

    sym = (mat + mat.transpose())/2
    if len(np.unique(mat)) == 2: #if graph was unweighted, return unweighted
        return np.ceil(sym) #otherwise return average
    return sym

# ANNABELLE
def knn_graph(mat,k=8,selfloops=False,symmetric=True):
    """Takes an input matrix and returns a k-Nearest Neighbour weighted adjacency matrix.

    Parameters
    ----------
    mat: array
        Input adjacency matrix, can be symmetric or not.
    k: int, default=8
        Number of neighbours.
    selfloops: bool, default=False
        Wether or not to keep selfloops in graph, if set to False resulting adjacency matrix
        has zero along diagonal.
    symmetric: bool, default=True
        Wether or not to return a symmetric adjacency matrix. In cases where a node is in the neighbourhood
        of another node that is not its neighbour, the connection strength between the two will be halved.
    
    Raises
    ------
    ValueError
        If input matrix is not square.
    ValueError
        If k not in range [1,n_nodes).
    
    Returns
    -------
    array
        Adjacency matrix of k-Nearest Neighbour graph.
    """
    if not (mat.shape[0] == mat.shape[1]):
        raise ValueError('Adjacency matrix must be square.')

    dim = mat.shape[0]
    if (k<=0) or (dim <=k):
        raise ValueError('k must be in range [1,n_nodes)')

    m = np.abs(mat) # Look at connection strength only, not direction
    mask = np.zeros((dim,dim),dtype=bool)
    for i in range(dim):
        sorted_ind = m[:,i].argsort().tolist()
        neighbours = sorted_ind[-(k + 1):] #you want to include self
        mask[:,i][neighbours] = True
    adj = mat.copy() # Original connection strengths
    adj[~mask] = 0

    if not selfloops:
        np.fill_diagonal(adj,0)

    if symmetric:
        return make_undirected(adj)
    else:
        return adj

def make_group_graph(connectomes,k=8,selfloops=False,symmetric=True):
    """
    Parameters
    ----------
    connectomes: list of array
        List of connectomes in n_roi x n_roi format, connectomes must all be the same shape.
    k: int, default=8
        Number of neighbours.
    selfloops: bool, default=False
        Wether or not to keep selfloops in graph, if set to False resulting adjacency matrix
        has zero along diagonal.
    symmetric: bool, default=True
        Wether or not to return a symmetric adjacency matrix. In cases where a node is in the neighbourhood
        of another node that is not its neighbour, the connection strength between the two will be halved.
    
    Raises
    ------
    ValueError
        If input connectomes are not square (only checks first).
    ValueError
        If k not in range [1,n_nodes).

    Returns
    -------
    graph
        Torch geometric graph object of k-Nearest Neighbours graph for the group average connectome.
    """
    if not (connectomes[0].shape[0] == connectomes[0].shape[1]):
        raise ValueError('Connectomes must be square.')

    # Group average connectome
    avg_conn = np.array(connectomes).mean(axis=0)

    # Undirected 8 k-NN graph as matrix
    avg_conn_k = knn_graph(avg_conn,k=k,selfloops=selfloops,symmetric=symmetric)

    # Format matrix into graph for torch_geometric
    graph = nx.convert_matrix.from_numpy_array(avg_conn_k)
    return tg.utils.from_networkx(graph)

# LOIC
def knn_graph_quantile(mat, self_loops=False, k=8, symmetric=True):
    """Takes an input correlation matrix and returns a k-Nearest Neighbour weighted undirected adjacency matrix."""

    if not (mat.shape[0] == mat.shape[1]):
        raise ValueError('Adjacency matrix must be square.')
    dim = mat.shape[0]
    if (k <= 0) or (dim <= k):
        raise ValueError('k must be in range [1,n_nodes)')

    is_directed = not (mat == mat.transpose()).all()
    # absolute correlation
    mat = np.abs(mat)
    adj = np.copy(mat)
    # get NN thresholds from quantile
    quantile_h = np.quantile(mat, (dim - k - 1)/dim, axis=0)
    mask_not_neighbours = (mat < quantile_h[:, np.newaxis])
    #TODO check if directed
    if is_directed:
        quantile_v = np.quantile(mat, (dim - k - 1)/dim, axis=1)
        mask_not_neighbours = mask_not_neighbours & (adj < quantile_v[np.newaxis, :])
    adj[mask_not_neighbours] = 0

    if not self_loops:
        np.fill_diagonal(adj, 0)
 
    if symmetric:
        return make_undirected(adj)
    else:
        return adj

if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt
    import src.data as data
    import src.data.data_loader
    
    data_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "cobre_difumo512", "difumo")
    DataLoad = data.data_loader.DataLoader(
        ts_dir = os.path.join(data_dir, "timeseries")
        , conn_dir = os.path.join(data_dir, "connectomes")
        , pheno_path = os.path.join(data_dir, "phenotypic_data.tsv"))
    avg_conn = np.array(DataLoad.get_valid_connectomes()).mean(axis=0)

    import time
    start = time.time()
    for ii in range(50):
        avg_conn8 = knn_graph(avg_conn, k=8)
    print("{}s".format(time.time() - start))
    start = time.time()
    for ii in range(50):
        avg_conn8_quantile = knn_graph_quantile(avg_conn, k=8)
    print("{}s".format(time.time() - start))
