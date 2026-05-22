import pytest

from app.services.classifier import classify
from app.schemas import QueryProfile


@pytest.mark.parametrize("query,expected", [
    ("LangGraph checkpointer 报错怎么解决", QueryProfile.TECH),
    ("Docker Windows WSL2 install failed", QueryProfile.TECH),
    ("FastAPI redis connection pool timeout", QueryProfile.TECH),
    ("pip install numpy failed", QueryProfile.TECH),
    ("公众号文章怎么写", QueryProfile.WECHAT),
    ("小红书文案 种草", QueryProfile.WECHAT),
    ("LLM agent benchmark arxiv", QueryProfile.RESEARCH),
    ("RAG evaluation metrics paper", QueryProfile.RESEARCH),
    ("OpenAI 最新模型 2026", QueryProfile.FRESH_CN),
    ("中国 AI 政策 2026", QueryProfile.FRESH_CN),
    ("广州 AI 公司", QueryProfile.GENERAL_CN),
    ("儿童牙膏 国家标准", QueryProfile.GENERAL_CN),
])
def test_classifier(query, expected):
    assert classify(query) == expected
