# tests/conftest.py
import os
import sys

# Добавляем src/ в начало sys.path, чтобы можно было просто писать `import parser`
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
)
