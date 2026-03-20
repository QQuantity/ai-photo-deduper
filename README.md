# AI Photo Deduper

<div align="center">

**📸 AI 智能清理重复照片**

基于感知哈希(Perceptual Hash)和相似度算法的智能照片去重工具

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## ✨ 功能特点

- 🔍 **智能检测** - 基于感知哈希算法，精准识别重复照片
- 🚀 **高效扫描** - 支持多线程处理，快速扫描大量照片
- 📊 **详细报告** - 生成去重报告，清晰展示重复照片
- 🛡️ **安全可靠** - 默认仅检测不删除，保护您的珍贵照片
- 🎯 **相似度阈值** - 可调节阈值，精确控制检测灵敏度
- 📁 **递归扫描** - 自动扫描子文件夹中的所有照片

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 使用方法

```bash
# 基本用法 - 扫描照片文件夹
python deduper.py ./photos

# 设置相似度阈值 (默认为5%)
python deduper.py ./photos -t 10

# 输出报告到文件
python deduper.py ./photos -o report.md

# 显示详细日志
python deduper.py ./photos -v
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `folder` | 要扫描的文件夹路径 | (必填) |
| `-t, --threshold` | 相似度阈值 (0-100) | 5 |
| `-o, --output` | 输出报告文件路径 | 无 |
| `--hash-size` | 哈希大小 | 8 |
| `-v, --verbose` | 显示详细日志 | 否 |

## 📖 工作原理

### 感知哈希算法

本工具使用三重哈希算法组合：

1. **pHash (Perceptual Hash)** - 感知哈希，对缩放和压缩鲁棒
2. **dHash (Difference Hash)** - 差异哈希，计算速度快
3. **aHash (Average Hash)** - 平均哈希，简单高效

通过组合三种哈希算法，可以有效识别：

- ✅ 尺寸缩放的照片
- ✅ 轻微压缩的照片
- ✅ 格式转换的照片
- ✅ 轻微裁剪的照片

### 相似度计算

```
相似度 = (1 - 汉明距离 / 哈希位数) × 100%
```

汉明距离越小，两张图片越相似。

## 📊 示例输出

```
# 📸 AI 智能照片去重报告

**扫描文件夹**: ./photos
**相似度阈值**: 5%
**发现重复照片**: 3 组

---

## 🔍 重复照片详情

### 组 1 - 相似度: 98.5%

- 📄 **IMG_2024.jpg** (建议保留 - 修改时间较新)
  - 路径: `./photos/vacation/IMG_2024.jpg`
  - 大小: 3.2 MB
- 🗑️ IMG_2024_copy.jpg (建议删除)
  - 路径: `./photos/backup/IMG_2024_copy.jpg`
  - 大小: 3.1 MB
```

## ⚠️ 注意事项

1. **备份重要照片** - 删除前请确保重要照片已备份
2. **首次使用建议** - 先用 `-o report.md` 生成报告查看结果
3. **阈值调整** - 如果检测结果不准确，尝试调整阈值

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

Made with ❤️ by QQuantity

</div>
