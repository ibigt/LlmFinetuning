import pandas as pd
from datasets import Dataset


def clean_log(log_text):
    """简单清洗：例如截取日志末尾或提取含有 'Alarm'/'Error' 的行"""
    if pd.isna(log_text): return ""
    lines = str(log_text).split('\n')
    # 比赛中日志可能很长，这里演示保留最后20行
    return "\n".join(lines[-20:])


def get_telco_dataset(file_path, tokenizer):
    df = pd.read_csv(file_path)

    def apply_template(row):
        system_msg = "你是一位电信网络专家。请根据提供的路测日志和小区工参，准确判断故障类别（C1-C8）。"

        # 拼接上下文
        context = (
            f"【故障描述】: {row.get('description', '无')}\n"
            f"【路测日志】: {clean_log(row.get('log_fragment', ''))}\n"
            f"【小区参数】: {row.get('parameters', '无')}"
        )

        # 训练时需要包含答案
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": context},
            {"role": "assistant", "content": f"故障根因标签: {row.get('label', '未知')}"}
        ]
        return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}

    dataset = Dataset.from_pandas(df).map(apply_template)
    return dataset