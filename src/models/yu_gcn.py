import torch
import torch.nn as nn
import torch.nn.functional as F
import torch_geometric as tg
import numpy as np

class YuGCN(torch.nn.Module):
    def __init__(self,edge_index,edge_weight,n_timepoints = 50):
        super().__init__()
        self.edge_index = edge_index
        self.edge_weight = edge_weight
        self.conv1 = tg.nn.ChebConv(in_channels=n_timepoints,out_channels=32,K=2,bias=True)
        self.conv2 = tg.nn.ChebConv(in_channels=32,out_channels=32,K=2,bias=True)
        self.conv3 = tg.nn.ChebConv(in_channels=32,out_channels=32,K=2,bias=True)
        self.conv4 = tg.nn.ChebConv(in_channels=32,out_channels=32,K=2,bias=True)
        self.conv5 = tg.nn.ChebConv(in_channels=32,out_channels=32,K=2,bias=True)
        self.conv6 = tg.nn.ChebConv(in_channels=32,out_channels=32,K=2,bias=True)
        self.fc1 = nn.Linear(512*32, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 2)
        self.dropout = nn.Dropout(0.5)

    def forward(self,x):
        x = self.conv1(x,self.edge_index,self.edge_weight)
        x = F.relu(x)
        x = self.conv2(x,self.edge_index,self.edge_weight)
        x = F.relu(x)
        x = self.conv3(x,self.edge_index,self.edge_weight)
        x = F.relu(x)
        x = self.conv4(x,self.edge_index,self.edge_weight)
        x = F.relu(x)
        x = self.conv5(x,self.edge_index,self.edge_weight)
        x = F.relu(x)
        x = self.conv6(x,self.edge_index,self.edge_weight)
        x = tg.nn.global_mean_pool(x,torch.from_numpy(np.array(range(x.size(0)),dtype=int)))
        
        x = x.view(-1, 512*32)
        x = self.fc1(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)
        x = self.fc3(x)
        return x