#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
该脚本用于在控制台测试单个用例：
1. 输入问题（字符串）；
2. 输入标准答案（已不再需要，比对逻辑已移除）；
3. 脚本会完成映射、类型检测、调用 LLM 接口，并打印模型回答及延迟信息。
"""

import json
import time
import requests

# 预加载各游戏的提示词文件
PROMPT_FILES = {
    'ssq': './ssq_system_prompt.json',
    'qlc': './qlc_system_prompt.json',
    'kl8': './kl8_system_prompt.json',
    '3d': './3d_system_prompt.json',
    'default': './default_system_prompt.json'
}

GAME_KEYWORDS = {
    'ssq': ['双色球', 'ssq', '蓝球', '红球', 'blue', 'red', '篮球'],
    'qlc': ['七乐彩', 'qlc'],
    'kl8': ['快乐8', 'kl8', '快8'],
    '3d': ['3d', '3D']
}

CHOICE_MAPPING = {
    '选10': '选十',
    '选1': '选一',
    '选2': '选二',
    '选3': '选三',
    '选4': '选四',
    '选5': '选五',
    '选6': '选六',
    '选7': '选七',
    '选8': '选八',
    '选9': '选九',
    'danshi': '单式',
    'fushi': '复式',
    'blue': '蓝球',
    'red': '红球',
}

# 将所有提示词加载到内存
PROMPTS = {}
for game, path in PROMPT_FILES.items():
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    PROMPTS[game] = '\n'.join(raw.get('system_prompt_lines', []))


def map_choices(text: str) -> str:
    """
    将文本中 '选1'~'选10' 等替换为对应的中文。
    """
    for orig, mapped in CHOICE_MAPPING.items():
        text = text.replace(orig, mapped)
    return text


def detect_game_type(question: str) -> str:
    """
    根据关键词判断彩种类型，未匹配时返回 'default'。
    """
    q = question.lower()
    for game, keywords in GAME_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                return game
    return 'default'


def call_llm_api(prompt: str, question: str):
    """
    调用本地 LLM 接口，返回 JSON 响应、首 token 延迟、总耗时。
    """
    url = "http://localhost:8000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer OPENWEBUI123"
    }
    data = {
        "model": "qwen3-8b",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "max_tokens": 8192,
        "presence_penalty": 1.5,
        "chat_template_kwargs": {"enable_thinking": False}
    }
    start = time.time()
    resp = requests.post(url, headers=headers, json=data)
    elapsed = time.time() - start
    return resp.json(), elapsed / 3, elapsed


if __name__ == '__main__':
    # 在控制台输入测试问题
    question = input("请输入测试问题：").strip()

    # 处理用户输入
    mapped_q = map_choices(question)
    game = detect_game_type(mapped_q)
    prompt = PROMPTS.get(game, PROMPTS['default'])

    # 调用 LLM 接口
    resp, ft_latency, total_time = call_llm_api(prompt, mapped_q)
    model_reply = resp.get('choices', [{}])[0].get('message', {}).get('content', '')

    # 输出模型回答和延迟
    print("\n====== 测试结果 ======")
    print(f"模型回复：{model_reply}")
    print(f"首 token 延迟：{ft_latency:.3f} 秒，总耗时：{total_time:.3f} 秒")
