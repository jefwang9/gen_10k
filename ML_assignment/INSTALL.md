# Installation Guide

## Quick Install

```bash
pip3 install -r requirements.txt
```

## If you encounter import errors

If you see errors like:
- `ModuleNotFoundError: No module named 'langchain.text_splitter'`
- `ModuleNotFoundError: No module named 'langchain_text_splitters'`

Run these commands to install the required packages:

```bash
pip3 install langchain-text-splitters
pip3 install langchain-core
pip3 install langchain-openai
pip3 install langchain-community
```

Or reinstall all requirements:
```bash
pip3 install --upgrade -r requirements.txt
```

## Verify Installation

Test that all imports work:
```bash
python3 -c "from langchain_text_splitters import RecursiveCharacterTextSplitter; print('OK')"
python3 -c "from langchain_core.prompts import ChatPromptTemplate; print('OK')"
python3 -c "from langchain_openai import ChatOpenAI; print('OK')"
```

All should print "OK" without errors.

