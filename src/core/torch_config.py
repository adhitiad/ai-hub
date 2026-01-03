import os

import psutil
import torch


def setup_torch_cpu():
    """
    Mengoptimalkan PyTorch agar berjalan maksimal di CPU Server.
    """
    # 1. Cek jumlah Core CPU fisik (bukan logical/hyperthreading)
    # VPS biasanya punya vCPU yang terbatas. Kita ambil fisik agar stabil.
    num_cores = psutil.cpu_count(logical=False)

    if num_cores is None:
        num_cores = psutil.cpu_count(logical=True)

    # 2. Limit Intra-Op Threads
    # Default PyTorch akan memakan SEMUA core. Ini buruk buat server multitasking.
    # Kita set agar fokus pada 1-4 core saja tergantung ketersediaan.
    torch.set_num_threads(num_cores)

    # 3. Matikan Inter-Op Threads (Parallelism antar operasi)
    # Untuk trading bot (inference 1 data per detik), kita tidak butuh ini.
    # Ini mengurangi overhead context switching.
    torch.set_num_interop_threads(1)

    print(f"🚀 PyTorch CPU Optimized: Using {num_cores} Threads")

    return torch.device("cpu")


# Global device variable
device = setup_torch_cpu()
