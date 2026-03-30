import torch
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, BitsAndBytesConfig
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
from peft import LoraConfig, prepare_model_for_kbit_training

# 1. 配置量化与模型
model_id = "Qwen/Qwen2.5-1.5B-Instruct"
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
    user_input = f"场景描述: {sample['description']}\n路测数据: {sample['log_fragment']}\n工参: {sample['parameters']}"
    # 假设标签列名为 label (C1-C8)
    assistant_output = f"诊断结果: {sample['label']}"

    # 遵循 Qwen2.5 的 ChatML 模版
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_output}
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}


# 加载数据 (请确保 train.csv 在当前目录)
df = pd.read_csv("train.csv")
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
training_args = TrainingArguments(
    output_dir="./qwen-1.5b-telco-lora",
    per_device_train_batch_size=2,  # 双卡合起来 batch 为 4
    gradient_accumulation_steps=8,  # 总有效 batch = 4 * 8 = 32
    learning_rate=1e-4,
    num_train_epochs=3,
    lr_scheduler_type="cosine",
    fp16=True,  # 2080Ti 必须用 fp16
    logging_steps=10,
    save_strategy="epoch",
    ddp_find_unused_parameters=False,  # 提升 DDP 稳定性
    report_to="none"
)

# 5. 只对 Assistant 回答计算 Loss (重要优化)
response_template = "<|im_start|>assistant\n"
collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

# 6. 启动训练器
model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config,
                                             device_map={"": torch.cuda.current_device()})
model = prepare_model_for_kbit_training(model)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    peft_config=peft_config,
    max_seq_length=2048,  # 电信日志较长，设为 2048
    dataset_text_field="text",
    data_collator=collator,
)

trainer.train()
trainer.model.save_pretrained("./final_adapter")