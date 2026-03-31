import torch
# 强制关闭 TF32 以确保 2080 Ti 的稳定性
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
import pandas as pd
import argparse
import os
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from trl import SFTTrainer, SFTConfig, DataCollatorForCompletionOnlyLM
from peft import LoraConfig, prepare_model_for_kbit_training
import data_utils

# 添加命令行参数解析
parser = argparse.ArgumentParser(description="电信故障诊断模型微调脚本")
parser.add_argument("--do_eval", type=bool, default=True, help="是否评估模型")
parser.add_argument("--model_path", type=str, default="./models/Qwen2.5-1.5B-Instruct", help="预训练模型ID/路径")
parser.add_argument("--output_dir", type=str, default="./output/model", help="模型输出目录")
parser.add_argument("--adapter_dir", type=str, default="./output/adapter", help="LoRA 适配器保存目录")
parser.add_argument("--train_data_path", type=str, default=None, help="训练数据路径")
parser.add_argument("--eval_data_path", type=str, default=None, help="验证数据路径")
parser.add_argument("--batch_size", type=int, default=2, help="每个设备的批次大小")
parser.add_argument("--gradient_accumulation", type=int, default=8, help="梯度累积步数")
parser.add_argument("--learning_rate", type=float, default=1e-4, help="学习率")
parser.add_argument("--epochs", type=int, default=3, help="训练轮数")
parser.add_argument("--max_seq_length", type=int, default=512, help="最大序列长度")
args = parser.parse_args()



# 确保输出目录存在
os.makedirs(args.output_dir, exist_ok=True)
os.makedirs(args.adapter_dir, exist_ok=True)
# 强制脚本内部也只能看到单卡
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# 1. 配置量化与模型
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                      # 启用 4 位量化
    bnb_4bit_quant_type="nf4",              # 使用 NormalFloat4 量化类型
    bnb_4bit_compute_dtype=torch.float16,   # 计算时使用 float16 精度
)

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(args.model_path)
# Qwen-2.5 没有专门的pad_token，使用eos_token作为pad_token
tokenizer.pad_token = tokenizer.eos_token


# 2. 数据处理：将电信 CSV 转为指令对
def format_instruction(sample):
    # 根据比赛描述拼接输入
    system_prompt = "你是一个5G电信网络专家，负责根据路测日志和工参诊断故障根因。"
    # user_input = f"场景描述: {sample['question']}\n路测数据: {sample['log_fragment']}\n工参: {sample['parameters']}"
    user_input = f"场景描述:\n{sample['question']}"
    # 假设标签列名为 label (C1-C8)
    assistant_output = f"诊断结果:\n{sample['answer']}"

    # 遵循 Qwen2.5 的 ChatML 模版
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_output}
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}


# 加载数据
print(f"加载训练数据: {args.train_data_path}")
df_train = pd.read_csv(args.train_data_path)
train_dataset = Dataset.from_pandas(df_train).map(format_instruction)
print(f"加载验证数据: {args.eval_data_path}")
df_eval = pd.read_csv(args.eval_data_path)
eval_dataset = Dataset.from_pandas(df_eval).map(format_instruction)

# 3. 设置 LoRA 插件
peft_config = LoraConfig(
    r=16,                   # LoRA 的秩，控制可训练参数的数量
    lora_alpha=32,          # 控制 Lora 矩阵的维度
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], # 指定要应用 LoRA 的模型模块
    lora_dropout=0.1,       # LoRA 的 dropout 率
    bias="none",            # 不训练偏置参数
    task_type="CAUSAL_LM",  # 任务类型为因果语言模型
)

# 4. 训练参数
sft_config = SFTConfig(
    output_dir=args.output_dir,
    per_device_train_batch_size=args.batch_size,
    gradient_accumulation_steps=args.gradient_accumulation,
    learning_rate=args.learning_rate,
    num_train_epochs=args.epochs,
    lr_scheduler_type="cosine",     # 使用余弦退火学习率调度器
    gradient_checkpointing=True,    # 开启梯度检查
    gradient_checkpointing_kwargs={"use_reentrant": False},
    fp16=True,                   # 使用半精度训练，适合 2080 Ti 显卡
    logging_steps=1,             # 每 1 步记录一次日志
    save_strategy="epoch",       # 每个 epoch 保存一次模型
    eval_strategy="epoch",       # 每个 epoch 评估一次
    do_eval=args.do_eval,        # 开启评估
    report_to="none",            # 不报告训练指标
    max_seq_length=args.max_seq_length,
    dataset_text_field="text",
    dataloader_pin_memory=False, # 禁用数据加载器的内存锁定
)

# 5. 只对 Assistant 回答计算 Loss
response_template = "<|im_start|>assistant\n"
collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

# 6. 启动训练器
model = AutoModelForCausalLM.from_pretrained(
    args.model_path,
    quantization_config=bnb_config,
    device_map={"": 0}  # 强制只使用第一张显卡
)
# 准备模型进行量化训练
model = prepare_model_for_kbit_training(model)

# 6. 启动训练器
trainer = SFTTrainer(
    model=model,
    args=sft_config,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    peft_config=peft_config,
    data_collator=collator,
)

# 启动训练
print("开始训练...")
trainer.train()

# 保存模型
print(f"保存 LoRA 适配器到: {args.adapter_dir}")
trainer.model.save_pretrained(args.adapter_dir)
print("训练完成！")