import time
import numpy as np
import sys
import random
import os
import warnings

import torch
from torch.utils.tensorboard import SummaryWriter
import torch.distributed as dist
import torch.multiprocessing as mp
import torch.utils.data.distributed
from tqdm import tqdm

sys.path.append('./')

# from data_process.ttnet_dataloader import create_train_val_dataloader, create_test_dataloader
from models.model_utils import create_model
# load_pretrained_model, make_data_parallel, resume_model, get_num_parameters
# from models.model_utils import freeze_model
# from utils.train_utils import create_optimizer, create_lr_scheduler, get_saved_state, save_checkpoint
# from utils.train_utils import reduce_tensor, to_python_float
# from utils.misc import AverageMeter, ProgressMeter
# from utils.logger import Logger
from config.config import parse_configs


def main():
    configs = parse_configs()

    # Re-produce results
    if configs.seed is not None:
        random.seed(configs.seed)
        np.random.seed(configs.seed)
        torch.manual_seed(configs.seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    if configs.gpu_idx is not None:
        warnings.warn('You have chosen a specific GPU. This will completely '
                      'disable data parallelism.')

    main_worker(configs.gpu_idx, configs)


def main_worker(gpu_idx, configs):
    configs.gpu_idx = gpu_idx
    print("Main Initialization")
    
    if configs.gpu_idx is not None:
        print("Use GPU: {} for training".format(configs.gpu_idx))
        configs.device = torch.device('cuda:{}'.format(configs.gpu_idx))
        
    model = create_model(configs)
    print(model)

if __name__ == "__main__":
    main()