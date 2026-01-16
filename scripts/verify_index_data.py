"""
POC: 验证A股指数数据获取能力
测试OpenBB/yfinance能否提供沪深300、深证成指等A股指数的历史数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# A股指数代码映射
INDEX_SYMBOLS = {
    'CSI300': '000300.SS',  # 沪深300
    'SZSE': '399001.SZ',    # 深证成指
    'SSE': '000001.SS',     # 上证指数
    'GEM': '399006.SZ',     # 创业板指
}

# 美股指数
US_INDEX_SYMBOLS = {
    'NASDAQ': '^IXIC',
    'SP500': '^GSPC',
    'DOW': '^DJI',
}

async def test_index_data(symbol: str, name: str, start_date: str, end_date: str):
    """测试单个指数的数据获取"""
    print(f"\n{'='*60}")
    print(f"测试指数: {name} ({symbol})")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"{'='*60}")
    
    try:
        # 添加延迟避免rate limit
        await asyncio.sleep(1)
        
        # 使用yfinance获取数据
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"[X] 失败: 无法获取数据（数据为空）")
            return False
        
        print(f"[OK] 成功: 获取到 {len(hist)} 条记录")
        print(f"   数据列: {list(hist.columns)}")
        print(f"   日期范围: {hist.index[0].date()} 至 {hist.index[-1].date()}")
        print(f"   最新收盘价: {hist['Close'].iloc[-1]:.2f}")
        print(f"   数据完整性: {hist.isnull().sum().sum()} 个缺失值")
        
        # 检查数据质量
        if hist.isnull().sum().sum() > len(hist) * 0.1:  # 超过10%缺失
            print(f"[!] 警告: 数据缺失率较高")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if 'RateLimit' in error_msg or 'Too Many Requests' in error_msg:
            print(f"[!] 失败: 请求频率限制，需要等待")
        else:
            print(f"[X] 失败: {error_msg}")
        return False

async def main():
    """主测试函数"""
    print("="*60)
    print("A股指数数据获取能力验证 (POC)")
    print("="*60)
    
    # 测试时间范围：最近1年
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    results = {}
    
    # 测试A股指数
    print("\n【A股指数测试】")
    for name, symbol in INDEX_SYMBOLS.items():
        success = await test_index_data(symbol, name, start_date, end_date)
        results[f"A股-{name}"] = success
    
    # 测试美股指数（作为对比）
    print("\n【美股指数测试（对比）】")
    for name, symbol in US_INDEX_SYMBOLS.items():
        success = await test_index_data(symbol, name, start_date, end_date)
        results[f"美股-{name}"] = success
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"总计: {total} 个指数")
    print(f"成功: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed > 0:
        print("\n失败的指数:")
        for name, success in results.items():
            if not success:
                print(f"  - {name}")
    
    # 结论
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    if passed >= total * 0.8:  # 80%以上成功
        print("[OK] yfinance可以较好地支持A股指数数据获取")
        print("   建议: 可以使用yfinance作为A股指数数据源")
    elif passed >= total * 0.5:
        print("[!] yfinance对A股指数支持有限")
        print("   建议: 考虑使用其他数据源（如tushare、akshare）作为补充")
    else:
        print("[X] yfinance对A股指数支持较差")
        print("   建议: 必须使用其他数据源（如tushare、akshare）")
    
    return passed >= total * 0.5

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
