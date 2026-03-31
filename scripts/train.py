import torch
# 强制关闭 TF32 以确保 2080 Ti 的稳定性
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
import pandas as pd
import argparse
import os
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, BitsAndBytesConfig
from trl import SFTTrainer, SFTConfig, DataCollatorForCompletionOnlyLM
from peft import LoraConfig, prepare_model_for_kbit_training

# 添加命令行参数解析
parser = argparse.ArgumentParser(description="电信故障诊断模型微调脚本")
parser.add_argument("--data_path", type=str, default="train.csv", help="训练数据路径")
parser.add_argument("--output_dir", type=str, default="./output", help="模型输出目录")
parser.add_argument("--adapter_dir", type=str, default="./adapter", help="LoRA 适配器保存目录")
parser.add_argument("--model_id", type=str, default="./models/Qwen2.5-1.5B-Instruct", help="预训练模型 ID")
parser.add_argument("--batch_size", type=int, default=2, help="每个设备的 batch size")
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
model_id = args.model_id
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,  # 2080Ti 使用 fp16
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
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
print(f"加载数据: {args.data_path}")
df = pd.read_csv(args.data_path)
dataset = Dataset.from_pandas(df).map(format_instruction)

# 3. 设置 LoRA 插件
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM",
)

# 4. 训练参数
sft_config = SFTConfig(
    output_dir=args.output_dir,
    per_device_train_batch_size=args.batch_size,
    gradient_accumulation_steps=args.gradient_accumulation,
    learning_rate=args.learning_rate,
    num_train_epochs=args.epochs,
    lr_scheduler_type="cosine",
    gradient_checkpointing=True, # 开启梯度检查
    gradient_checkpointing_kwargs={"use_reentrant": False}, # 配合 Qwen2 使用更稳定
    fp16=True,  # 2080Ti 必须用 fp16
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
    # 将原本报错的参数移至此处
    max_seq_length=args.max_seq_length,
    dataset_text_field="text",
    dataloader_pin_memory=False,
)

# 5. 只对 Assistant 回答计算 Loss (重要优化)
response_template = "<|im_start|>assistant\n"
collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

# 明确禁用一些可能导致同步超时的底层特性
os.environ["NCCL_P2P_DISABLE"] = "1"
os.environ["NCCL_IB_DISABLE"] = "1"

# 6. 启动训练器
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map={"": 0}  # 强制只使用第一张显卡
)
model = prepare_model_for_kbit_training(model)
# model.gradient_checkpointing_enable()



# 6. 启动训练器
trainer = SFTTrainer(
    model=model,
    args=sft_config, # 使用新的 sft_config
    train_dataset=dataset,
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