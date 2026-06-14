/** 金瓶梅货币换算 v1（见 docs/金瓶梅-知识图谱架构.md §6.1） */
export type CurrencyUnit = '银' | '钱' | '贯' | '文';

export interface NormalizeInput {
  amount: number;
  currency: CurrencyUnit;
}

export interface NormalizeResult {
  amount_normalized: number | null;
  conversion_note: string;
  conversion_disputed?: boolean;
}

const QIAN_PER_LIANG = 1000; // 晚明常用口径，因地因时浮动

export function normalizeToLiang({ amount, currency }: NormalizeInput): NormalizeResult {
  switch (currency) {
    case '银':
      return { amount_normalized: amount, conversion_note: '银两，直接计' };
    case '钱':
    case '文':
      return {
        amount_normalized: amount / QIAN_PER_LIANG,
        conversion_note: `${amount}${currency} ÷ ${QIAN_PER_LIANG} ≈ ${(amount / QIAN_PER_LIANG).toFixed(3)} 两（晚明口径，存疑时可修订）`,
        conversion_disputed: amount >= 500,
      };
    case '贯':
      return {
        amount_normalized: amount,
        conversion_note: '1 贯 ≈ 1 两（简化口径，一条鞭法后白银化相关）',
        conversion_disputed: true,
      };
    default:
      return { amount_normalized: null, conversion_note: '未知单位，未换算' };
  }
}

export function formatLiang(value: number): string {
  if (value >= 100) return `${value.toFixed(0)} 两`;
  if (value >= 10) return `${value.toFixed(1)} 两`;
  return `${value.toFixed(2)} 两`;
}
