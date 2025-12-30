"""
pytest配置文件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.setdefault("TESTING", "true")

# 导入测试所需的模块
import pytest
from app.core.config import settings

@pytest.fixture
def test_settings():
    """测试配置"""
    return settings

@pytest.fixture
def project_root_path():
    """项目根目录路径"""
    return project_root 