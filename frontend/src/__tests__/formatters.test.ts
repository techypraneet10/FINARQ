import { describe, it, expect } from 'vitest';
import {
  formatAccountingValue,
  formatBytes,
  formatDateTime,
  getGroundingStatusBadge,
  getAnswerabilityStatusBadge,
} from '../utils/formatters';

describe('Financial Formatters Utilities', () => {
  it('formats positive financial values with standard currency and decimals', () => {
    expect(formatAccountingValue('1234567.89')).toBe('$1,234,567.89');
    expect(formatAccountingValue('100.00', { currency: 'EUR' })).toBe('EUR100.00');
  });

  it('formats negative financial values with accounting parentheses (1,234.50)', () => {
    expect(formatAccountingValue('-500000')).toBe('($500,000.00)');
    expect(formatAccountingValue('(42.50)')).toBe('($42.50)');
    expect(formatAccountingValue('1234.5', { isNegative: true })).toBe('($1,234.50)');
  });

  it('formats percentages accurately', () => {
    expect(formatAccountingValue('15.45', { isPercentage: true })).toBe('15.45%');
    expect(formatAccountingValue('-4.2', { isPercentage: true })).toBe('(4.20%)');
  });

  it('handles null, undefined, and empty string without throwing', () => {
    expect(formatAccountingValue(null)).toBe('—');
    expect(formatAccountingValue(undefined)).toBe('—');
    expect(formatAccountingValue('')).toBe('—');
  });

  it('formats byte sizes into readable human scales', () => {
    expect(formatBytes(0)).toBe('0 Bytes');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1024 * 1024 * 5.5)).toBe('5.5 MB');
  });

  it('provides correct badge configs for grounding status', () => {
    expect(getGroundingStatusBadge('grounded').label).toBe('100% Grounded');
    expect(getGroundingStatusBadge('partially_grounded').label).toBe('Partially Grounded');
    expect(getGroundingStatusBadge('ungrounded').label).toBe('Ungrounded');
  });

  it('provides correct badge configs for answerability states', () => {
    expect(getAnswerabilityStatusBadge('insufficient_evidence').label).toBe('Insufficient Evidence');
    expect(getAnswerabilityStatusBadge('conflicting_evidence').label).toBe('Conflicting Evidence');
  });
});
