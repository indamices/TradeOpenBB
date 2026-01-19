import { useState, useEffect } from 'react';

/**
 * 防抖 Hook - 延迟更新值，减少不必要的 API 调用
 *
 * 使用场景：
 * - 搜索输入框（延迟搜索直到用户停止输入）
 * - 窗口 resize 事件
 * - 滚动事件处理
 * - 任何需要延迟处理的频繁触发事件
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 *
 * useEffect(() => {
 *   // 仅在防抖值变化时执行搜索
 *   if (debouncedSearchTerm) {
 *     performSearch(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 *
 * return (
 *   <input
 *     value={searchTerm}
 *     onChange={(e) => setSearchTerm(e.target.value)}
 *     // UI 立即更新，搜索在 300ms 无输入后执行
 *   />
 * );
 * ```
 *
 * @param value - 需要防抖的值
 * @param delay - 延迟时间（毫秒），默认 300ms
 * @returns 防抖后的值
 */
function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // 设置定时器，延迟更新值
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 清理函数：如果 value 在延迟时间内再次变化，取消之前的定时器
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;
