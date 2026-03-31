## 项目路径

``` plain-text
LlmFinetuning/
├── data/                  # 存放比赛原始数据
│   ├── train.csv
│   ├── phase_1_test.csv
│   └── phase_2_test.csv
├── outputs/               # 存放训练后的模型权重 (Adapters)
├── configs/               # 存放配置文件
│   └── accelerate_config.yaml
├── scripts/               # 存放核心逻辑代码
│   ├── data_utils.py      # 数据清洗与格式转换逻辑
│   ├── train.py           # 训练启动脚本
│   └── inference.py       # 生成提交文件的推理脚本
├── README.md              # 项目说明
└── requirements.txt       # 环境依赖列表
```
## 本地下载模型
在项目根目录下（LlmFinetuning/models）执行：
```bash
# 配置国内镜像
set HF_ENDPOINT=https://hf-mirror.com
# 标准下载命令
hf download Qwen/Qwen2.5-1.5B-Instruct --local-dir Qwen2.5-1.5B-Instruct
hf download Qwen/Qwen2.5-7B-Instruct --local-dir Qwen2.5-7B-Instruct
hf download Qwen/Qwen3-32B-Instruct --local-dir Qwen3-32B-Instruct
```


## 启动微调
在项目根目录下（LlmFinetuning/）执行：

``` bash
export CUDA_VISIBLE_DEVICES=0,1
accelerate launch --config_file configs/accelerate_config.yaml scripts/train.py
```

## 监控显存

```Bash
nvidia-smi -l 1
```

