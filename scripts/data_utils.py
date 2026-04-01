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


def format_instruction_basic(sample, tokenizer, system_prompt=None):
    """基础提示词制作方式

    Args:
        sample: 数据样本
        tokenizer: 分词器
        system_prompt: 系统提示词，默认使用电信专家提示词

    Returns:
        格式化后的文本
    """
    user_input = f"{sample['question']}"
    assistant_output = f"\\boxed{{{sample['answer'].strip()}}}"

    # 遵循 Qwen2.5 的 ChatML 模版
    messages = [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_output}
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}


def format_instruction_detailed(sample, tokenizer, system_prompt=None):
    """详细提示词制作方式

    Args:
        sample: 数据样本
        tokenizer: 分词器
        system_prompt: 系统提示词，默认使用详细的电信专家提示词

    Returns:
        格式化后的文本
    """
    if system_prompt is None:
        system_prompt = ("你是一个资深的5G电信网络专家，拥有丰富的故障诊断经验。请根据提供的场景描述，"
                         "详细分析可能的故障根因，并给出专业、准确的诊断结果。")

    user_input_parts = ["场景描述:{}".format(sample['question'].split('\n\n')[0])]
    if 'C1:' in sample['question']:
        answer_options = '\nC1:' + sample['question'].split('C1:')[1].split('\n\n')[0]
        user_input_parts.append("答案选项{}".format(answer_options))
    if 'Given:' in sample['question']:
        given_conditions = sample['question'].split('Given:')[1].split('\n\n')[0]
        user_input_parts.append("已知条件{}".format(given_conditions))
    if 'Beam Scenario and Vertical Beamwidth Relationships' in sample['question']:
        beam_relationships = sample['question'].split('Beam Scenario and Vertical Beamwidth Relationships')[1].split('\n\n')[0]
        user_input_parts.append("波束场景与垂直波束宽度关系{}".format(beam_relationships))
    if 'User plane drive test data as follows' in sample['question']:
        user_drive_data = sample['question'].split('User plane drive test data as follows')[1].split('\n\n\n')[0]
        user_input_parts.append("用户驾驶数据{}".format(user_drive_data))
    if 'Engeneering parameters data as follows' in sample['question']:
        engineering_params = sample['question'].split('Engeneering parameters data as follows')[1].split()
        user_input_parts.append("工参:{}".format(engineering_params))

    user_input = "\n".join(user_input_parts)
    assistant_output = f"\\boxed{{{sample['answer'].strip()}}}"

    # 遵循 Qwen2.5 的 ChatML 模版
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_output}
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}


def format_instruction_technical(sample, tokenizer, system_prompt=None):
    """技术型提示词制作方式

    Args:
        sample: 数据样本
        tokenizer: 分词器
        system_prompt: 系统提示词，默认使用技术型提示词

    Returns:
        格式化后的文本
    """
    if system_prompt is None:
        system_prompt = "你是一个技术专家，专注于5G网络故障诊断。请基于提供的信息，运用专业知识进行分析，返回故障根因诊断编号"

    user_input = f"【故障分析任务\n{sample['question']}"
    assistant_output = f"\\boxed{{{sample['answer'].strip()}}}"

    # 遵循 Qwen2.5 的 ChatML 模版
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_output}
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}


def load_and_process_data(data_path, tokenizer, format_func=None, encoding='utf-8'):

    # 尝试不同编码读取文件
    try:
        df = pd.read_csv(data_path, encoding=encoding)
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(data_path, encoding='cp1252')
        except UnicodeDecodeError:
            df = pd.read_csv(data_path, encoding='gbk')

    # 如果没有指定格式化函数，使用默认函数
    if format_func is None:
        def default_format(sample):
            return format_instruction_basic(sample, tokenizer)
        wrapped_format = default_format
    else:
        # 包装格式化函数，使其只接受 sample 参数
        def wrapped_format(sample):
            return format_func(sample, tokenizer)

    # 处理数据
    dataset = Dataset.from_pandas(df).map(wrapped_format)
    return dataset


def process_to_dict(dataset):
    """
    确保返回的是 SFTTrainer 能够直接使用的 Dataset 格式。
    如果 dataset 已经是 Dataset 对象且包含 'text' 键，直接返回。
    """
    # 如果已经是符合要求的 Dataset，直接返回其本身
    if hasattr(dataset, "column_names") and "text" in dataset.column_names:
        return dataset

    # 如果是列表格式，则转换为 Dataset
    if isinstance(dataset, list):
        return Dataset.from_list([{"text": x} if isinstance(x, str) else x for x in dataset])

    return dataset