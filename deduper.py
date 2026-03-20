#!/usr/bin/env python3
"""
AI Photo Deduper - 智能照片去重工具
基于感知哈希(Perceptual Hash)和相似度算法自动检测并清理重复照片
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging

# 尝试导入图像处理库
try:
    from PIL import Image
    import imagehash
    HAS_IMAGING = True
except ImportError:
    HAS_IMAGING = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PhotoDeduper:
    """AI 照片去重器"""
    
    def __init__(self, folder_path: str, threshold: float = 5.0, hash_size: int = 8):
        """
        初始化去重器
        
        Args:
            folder_path: 要扫描的文件夹路径
            threshold: 相似度阈值 (0-100)，低于此值认为是重复照片
            hash_size: 哈希大小，越大越精确但越慢
        """
        self.folder_path = Path(folder_path)
        self.threshold = threshold
        self.hash_size = hash_size
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        
    def is_image(self, file_path: Path) -> bool:
        """检查文件是否为支持的图片格式"""
        return file_path.suffix.lower() in self.supported_formats
    
    def get_image_hash(self, image_path: Path) -> str:
        """
        获取图片的感知哈希
        
        使用 pHash (Perceptual Hash) 算法，对图片进行缩放和模糊处理后生成哈希值
        这种方法对图片的缩放、压缩、轻微修改具有很好的鲁棒性
        """
        try:
            if not HAS_IMAGING:
                # 如果没有安装图像库，使用文件哈希作为后备
                with open(image_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
            
            img = Image.open(image_path)
            
            # 使用多种哈希算法组合
            # 1. pHash - 感知哈希，对缩放和压缩鲁棒
            phash = str(imagehash.phash(img, hash_size=self.hash_size))
            
            # 2. dHash - 差异哈希，速度快
            dhash = str(imagehash.dhash(img, hash_size=self.hash_size))
            
            # 3. aHash - 平均哈希
            ahash = str(imagehash.ahash(img, hash_size=self.hash_size))
            
            # 组合哈希
            return f"{phash}|{dhash}|{ahash}"
            
        except Exception as e:
            logger.warning(f"无法处理图片 {image_path}: {e}")
            return None
    
    def calculate_similarity(self, hash1: str, hash2: str) -> float:
        """
        计算两个哈希值的相似度
        
        Returns:
            相似度 (0-100)，100 表示完全相同
        """
        if not hash1 or not hash2:
            return 0.0
        
        if '|' not in hash1:
            # 后备方案：使用简单的哈希比较
            h1 = int(hash1, 16) if len(hash1) == 32 else 0
            h2 = int(hash2, 16) if len(hash2) == 32 else 0
            xor = h1 ^ h2
            diff_bits = bin(xor).count('1')
            max_bits = 128
            return (1 - diff_bits / max_bits) * 100
        
        # 多重哈希相似度计算
        hash1_parts = hash1.split('|')
        hash2_parts = hash2.split('|')
        
        similarities = []
        for h1, h2 in zip(hash1_parts, hash2_parts):
            h1_int = int(h1, 16)
            h2_int = int(h2, 16)
            xor = h1_int ^ h2_int
            diff_bits = bin(xor).count('1')
            max_bits = self.hash_size * self.hash_size
            sim = (1 - diff_bits / max_bits) * 100
            similarities.append(sim)
        
        return sum(similarities) / len(similarities)
    
    def scan_folder(self) -> Dict[str, str]:
        """扫描文件夹获取所有图片的哈希值"""
        image_hashes = {}
        
        image_files = [f for f in self.folder_path.rglob('*') 
                      if f.is_file() and self.is_image(f)]
        
        logger.info(f"找到 {len(image_files)} 张图片")
        
        for image_path in image_files:
            file_hash = self.get_image_hash(image_path)
            if file_hash:
                image_hashes[str(image_path)] = file_hash
                logger.debug(f"已处理: {image_path.name}")
        
        return image_hashes
    
    def find_duplicates(self, image_hashes: Dict[str, str]) -> List[Tuple[str, str, float]]:
        """
        查找重复照片
        
        Returns:
            [(图片1路径, 图片2路径, 相似度), ...]
        """
        duplicates = []
        files = list(image_hashes.keys())
        
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                similarity = self.calculate_similarity(
                    image_hashes[file1], 
                    image_hashes[file2]
                )
                
                if similarity >= self.threshold:
                    duplicates.append((file1, file2, similarity))
        
        # 按相似度排序
        duplicates.sort(key=lambda x: x[2], reverse=True)
        
        return duplicates
    
    def generate_report(self, duplicates: List[Tuple[str, str, float]]) -> str:
        """生成去重报告"""
        report_lines = [
            "# 📸 AI 智能照片去重报告",
            "",
            f"**扫描文件夹**: {self.folder_path}",
            f"**相似度阈值**: {self.threshold}%",
            f"**发现重复照片**: {len(duplicates)} 组",
            "",
            "---",
            ""
        ]
        
        if not duplicates:
            report_lines.append("✅ 未发现重复照片！")
            return "\n".join(report_lines)
        
        report_lines.append("## 🔍 重复照片详情\n")
        
        for i, (file1, file2, similarity) in enumerate(duplicates, 1):
            path1 = Path(file1)
            path2 = Path(file2)
            
            # 智能推荐保留哪张（通常保留文件修改时间较新的）
            mtime1 = path1.stat().st_mtime
            mtime2 = path2.stat().st_mtime
            
            keep_file = path2 if mtime2 > mtime1 else path1
            delete_file = path1 if mtime2 > mtime1 else path2
            
            report_lines.append(f"### 组 {i} - 相似度: {similarity:.1f}%\n")
            report_lines.append(f"- 📄 **{keep_file.name}** (建议保留 - 修改时间较新)")
            report_lines.append(f"  - 路径: `{keep_file}`")
            report_lines.append(f"  - 大小: {keep_file.stat().st_size / 1024:.1f} KB")
            report_lines.append(f"- 🗑️ {delete_file.name} (建议删除)")
            report_lines.append(f"  - 路径: `{delete_file}`")
            report_lines.append(f"  - 大小: {delete_file.stat().st_size / 1024:.1f} KB")
            report_lines.append("")
        
        # 统计信息
        total_size = sum(
            Path(f).stat().st_size 
            for _, f, _ in duplicates 
            for f in [Path(f).stat().st_size]
        )
        
        report_lines.extend([
            "---",
            "",
            "## 📊 统计信息",
            "",
            f"- 重复照片组数: **{len(duplicates)}**",
            f"- 可释放空间: **{total_size / 1024 / 1024:.2f} MB**",
            "",
            "---",
            "",
            "*💡 提示: 移动重复照片到回收站前，请先确认重要照片已备份*",
            "",
            f"报告生成时间: {logging.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return "\n".join(report_lines)
    
    def run(self) -> Dict:
        """运行去重检查"""
        logger.info("🔍 开始扫描照片...")
        
        image_hashes = self.scan_folder()
        
        if not image_hashes:
            logger.warning("未找到任何图片文件")
            return {"success": False, "message": "未找到图片文件"}
        
        logger.info("🔬 分析相似度...")
        duplicates = self.find_duplicates(image_hashes)
        
        report = self.generate_report(duplicates)
        
        return {
            "success": True,
            "total_images": len(image_hashes),
            "duplicate_groups": len(duplicates),
            "duplicates": duplicates,
            "report": report
        }


def main():
    parser = argparse.ArgumentParser(
        description='AI 智能照片去重工具 - 基于感知哈希算法检测重复照片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python deduper.py ./photos                    # 扫描当前目录
  python deduper.py ./photos -t 10             # 设置阈值为10%
  python deduper.py ./photos -o report.md      # 输出报告到文件
  python deduper.py ./photos --delete          # 自动删除重复照片（谨慎）
        """
    )
    
    parser.add_argument('folder', help='要扫描的文件夹路径')
    parser.add_argument('-t', '--threshold', type=float, default=5.0,
                       help='相似度阈值 (0-100)，默认: 5')
    parser.add_argument('-o', '--output', type=str,
                       help='输出报告文件路径')
    parser.add_argument('--hash-size', type=int, default=8,
                       help='哈希大小，默认: 8')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='显示详细日志')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 检查依赖
    if not HAS_IMAGING:
        logger.warning("⚠️  未安装 imagehash 库，使用简单哈希算法")
        logger.warning("   安装完整功能: pip install pillow imagehash")
    
    # 运行去重
    deduper = PhotoDeduper(args.folder, args.threshold, args.hash_size)
    result = deduper.run()
    
    # 输出报告
    if result.get('report'):
        print(result['report'])
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result['report'])
            logger.info(f"📄 报告已保存到: {args.output}")
    
    # 总结
    if result.get('success'):
        logger.info(f"✅ 扫描完成！发现 {result['duplicate_groups']} 组重复照片")
    else:
        logger.error(f"❌ 扫描失败: {result.get('message')}")
        sys.exit(1)


if __name__ == '__main__':
    import logging as logging_module
    logging_module.datetime = logging_module
    main()
