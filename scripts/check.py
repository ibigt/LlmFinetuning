import torch
import bitsandbytes as bnb

print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"GPU Count: {torch.cuda.device_count()}")
print(f"Current GPU: {torch.cuda.get_device_name(0)}")
# 测试 bitsandbytes 是否能找到 CUDA 库
print(f"bitsandbytes version: {bnb.__version__}")