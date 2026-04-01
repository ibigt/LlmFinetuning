import torch
import pandas as pd
import argparse
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


def main():
    # 1. 参数解析 (与 train.py 风格保持一致)
    parser = argparse.ArgumentParser(description="电信故障诊断模型推理脚本")

    # 模型与路径参数
    parser.add_argument("--base_model_path", type=str, default="./models/Qwen2.5-1.5B-Instruct", help="原始 Qwen2.5 模型路径")
    parser.add_argument("--lora_adapter_path", type=str, required=False, help="训练好的 LoRA 适配器路径（可选）")
    parser.add_argument("--use_lora", type=bool, default=True, help="是否加载LoRA适配器")
    parser.add_argument("--test_data_path", type=str, default="./data/eval.csv", help="测试数据 CSV 路径")
    parser.add_argument("--output_result_path", type=str, default="./data/infer_results.csv", help="推理结果保存路径")
    parser.add_argument("--gpu_id", type=int, default=0, help="使用的显卡序号")
    # 推理生成参数
    parser.add_argument("--max_new_tokens", type=int, default=256, help="生成的最大 token 数")
    parser.add_argument("--temperature", type=float, default=0.1, help="生成温度，控制随机性")
    parser.add_argument("--top_p", type=float, default=0.9, help="Nucleus sampling 参数")
    parser.add_argument("--batch_size", type=int, default=1, help="推理批次大小")

    args = parser.parse_args()

    # 强制脚本内部也只能看到单卡
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu_id)

    print(f"加载分词器: {args.base_model_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_path)
    tokenizer.pad_token = tokenizer.eos_token

    # 2. 配置 4-bit 量化 (必须与训练时一致)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    print("加载基础模型 (4-bit 量化)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model_path,
        quantization_config=bnb_config,
        device_map="auto",
    )

    if args.use_lora and args.lora_adapter_path:
        print(f"注入 LoRA 适配器: {args.lora_adapter_path}")
        model = PeftModel.from_pretrained(model, args.lora_adapter_path)
    else:
        print("未加载LoRA适配器，使用基础模型")
    model.eval()

    # 3. 加载测试数据
    print(f"读取测试数据: {args.test_data_path}")
    df_test = pd.read_csv(args.test_data_path)
    # 确保必要的列存在
    if 'question' not in df_test.columns:
        raise ValueError("测试数据必须包含 'question' 列")

    results = []

    # 4. 遍历数据进行推理
    # 注意：由于 2080 Ti 显存限制且生成长度不一，这里采用逐条或小批量推理
    for idx, row in df_test.iterrows():

        system_prompt = "你是一个5G电信网络专家，负责根据路测日志和工参诊断故障根因。"
        user_input = f"{row['question']}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        # 应用 Qwen2.5 的 ChatML 模版
        # add_generation_prompt=True 会自动在末尾加上 "<|im_channel|>final<|im_message|>"，提示模型开始生成
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512).to(model.device)

        # 5. 生成文本
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                # repetition_penalty=1.2,  # 惩罚重复token，降低重复内容出现的概率
                # eos_token_id=tokenizer.eos_token_id,  # 遇到结束符时停止生成
                # early_stopping=True,  # 当遇到eos_token_id时提前停止
                # num_beams=1,  # 使用贪心搜索而非束搜索，获得更确定性的输出
                # num_return_sequences=1,  # 只返回一个序列，确保输出唯一
                # length_penalty=0.6  # 鼓励更短的输出
            )

        # 解码：只获取新生成的部分 (去掉输入的 Prompt)
        generated_ids = outputs[0][inputs.input_ids.shape[-1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

        # 存储结果
        results.append({
            'id': idx,
            'original_question': row['question'],
            'predicted_answer': generated_text.strip()
        })
        print(f"进度: {idx + 1}/{len(df_test)}")
        print(f"输入: \n{row['question'][:900]}...")
        print(f"输出: \n{generated_text.strip()}\n{'-' * 50}")
        print(f"参考答案: {row['answer']}\n{'-' * 50}")

    # 6. 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_csv(args.output_result_path, index=False, encoding='utf-8-sig')
    print(f"推理完成！结果已保存至: {args.output_result_path}")


if __name__ == "__main__":
    main()