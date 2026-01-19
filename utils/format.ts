/**
 * 安全的数值格式化工具函数
 * 防止 undefined/null 导致的运行时错误
 */

/**
 * 安全地格式化数字为固定小数位
 * @param value - 要格式化的值（可以是 undefined/null）
 * @param decimals - 小数位数，默认 2
 * @param defaultValue - 当 value 为 undefined/null 时的默认值，默认 '0.00'
 * @returns 格式化后的字符串
 */
export function safeToFixed(
  value: number | undefined | null,
  decimals: number = 2,
  defaultValue: string = '0.00'
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return defaultValue;
  }
  try {
    return value.toFixed(decimals);
  } catch (e) {
    console.warn('safeToFixed error:', e, 'value:', value);
    return defaultValue;
  }
}

/**
 * 安全地格式化百分比
 * @param value - 小数值（如 0.108 表示 10.8%）
 * @param decimals - 小数位数，默认 2
 * @returns 格式化后的百分比字符串（如 "10.80%"）
 */
export function safePercent(
  value: number | undefined | null,
  decimals: number = 2
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '0.00%';
  }
  try {
    return `${(value * 100).toFixed(decimals)}%`;
  } catch (e) {
    console.warn('safePercent error:', e, 'value:', value);
    return '0.00%';
  }
}

/**
 * 安全地格式化带符号的百分比
 * @param value - 小数值
 * @param decimals - 小数位数，默认 2
 * @returns 格式化后的带符号百分比（如 "+10.80%" 或 "-5.20%"）
 */
export function safeSignedPercent(
  value: number | undefined | null,
  decimals: number = 2
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '0.00%';
  }
  try {
    const formatted = (value * 100).toFixed(decimals);
    return value >= 0 ? `+${formatted}%` : `${formatted}%`;
  } catch (e) {
    console.warn('safeSignedPercent error:', e, 'value:', value);
    return '0.00%';
  }
}

/**
 * 安全地格式化货币
 * @param value - 金额值
 * @param decimals - 小数位数，默认 2
 * @returns 格式化后的货币字符串（如 "$1,234.56"）
 */
export function safeCurrency(
  value: number | undefined | null,
  decimals: number = 2
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return `$0.00`;
  }
  try {
    return `$${value.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })}`;
  } catch (e) {
    console.warn('safeCurrency error:', e, 'value:', value);
    return '$0.00';
  }
}

/**
 * 安全地格式化带符号的货币
 * @param value - 金额值
 * @param decimals - 小数位数，默认 2
 * @returns 格式化后的带符号货币（如 "+$1,234.56" 或 "-$567.89"）
 */
export function safeSignedCurrency(
  value: number | undefined | null,
  decimals: number = 2
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '$0.00';
  }
  try {
    const formatted = value.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
    return value >= 0 ? `+$${formatted}` : `-$${Math.abs(value).toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })}`;
  } catch (e) {
    console.warn('safeSignedCurrency error:', e, 'value:', value);
    return '$0.00';
  }
}

/**
 * 安全地格式化数字（带单位）
 * @param value - 数值
 * @param unit - 单位（如 'M', 'K', 'T'）
 * @param decimals - 小数位数，默认 2
 * @returns 格式化后的字符串（如 "1.23M"）
 */
export function safeFormatWithUnit(
  value: number | undefined | null,
  unit: string,
  decimals: number = 2
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return `0.00${unit}`;
  }
  try {
    return `${value.toFixed(decimals)}${unit}`;
  } catch (e) {
    console.warn('safeFormatWithUnit error:', e, 'value:', value);
    return `0.00${unit}`;
  }
}

/**
 * 通用格式化函数 - 用于显示指标值
 * @param value - 要格式化的值
 * @param unit - 单位（如 '%', '$', 'K' 等）
 * @param decimals - 小数位数
 * @returns 格式化后的字符串，如果值为 undefined/null/NaN 返回 '-'
 */
export function formatMetric(
  value: number | undefined | null,
  unit: string = '',
  decimals: number = 2
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '-';
  }
  try {
    return `${value.toFixed(decimals)}${unit}`;
  } catch (e) {
    console.warn('formatMetric error:', e, 'value:', value);
    return '-';
  }
}

/**
 * 格式化日期为本地化字符串
 * @param dateString - ISO 日期字符串
 * @param locale - 地区代码，默认 'zh-CN'
 * @returns 格式化后的日期字符串
 */
export function formatDate(
  dateString: string | Date | undefined | null,
  locale: string = 'zh-CN'
): string {
  if (!dateString) return '-';
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    if (isNaN(date.getTime())) return '-';
    return date.toLocaleDateString(locale);
  } catch (e) {
    console.warn('formatDate error:', e, 'dateString:', dateString);
    return '-';
  }
}

/**
 * 格式化日期时间为本地化字符串
 * @param dateString - ISO 日期时间字符串
 * @param locale - 地区代码，默认 'zh-CN'
 * @returns 格式化后的日期时间字符串
 */
export function formatDateTime(
  dateString: string | Date | undefined | null,
  locale: string = 'zh-CN'
): string {
  if (!dateString) return '-';
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    if (isNaN(date.getTime())) return '-';
    return date.toLocaleString(locale);
  } catch (e) {
    console.warn('formatDateTime error:', e, 'dateString:', dateString);
    return '-';
  }
}

/**
 * 格式化数量（如 1000 -> 1K, 1000000 -> 1M）
 * @param value - 数值
 * @param decimals - 小数位数
 * @returns 格式化后的字符串
 */
export function formatQuantity(
  value: number | undefined | null,
  decimals: number = 1
): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '0';
  }

  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (absValue >= 1e9) {
    return `${sign}${(absValue / 1e9).toFixed(decimals)}B`;
  } else if (absValue >= 1e6) {
    return `${sign}${(absValue / 1e6).toFixed(decimals)}M`;
  } else if (absValue >= 1e3) {
    return `${sign}${(absValue / 1e3).toFixed(decimals)}K`;
  } else {
    return `${sign}${absValue.toFixed(decimals)}`;
  }
}

/**
 * 安全的数字截断（避免精度问题）
 * @param value - 数值
 * @param decimals - 小数位数
 * @returns 截断后的数值
 */
export function safeTruncate(
  value: number | undefined | null,
  decimals: number = 2
): number {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return 0;
  }
  try {
    const multiplier = Math.pow(10, decimals);
    return Math.trunc(value * multiplier) / multiplier;
  } catch (e) {
    console.warn('safeTruncate error:', e, 'value:', value);
    return 0;
  }
}
