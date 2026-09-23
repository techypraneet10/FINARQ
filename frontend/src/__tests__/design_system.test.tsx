import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../design-system/Button';
import { Badge } from '../design-system/Badge';
import { StatusBadge } from '../design-system/StatusBadge';
import { Alert } from '../design-system/Alert';
import { Input } from '../design-system/Input';
import { Card } from '../design-system/Card';

describe('Financial Design System Components', () => {
  it('renders Button with variants and handles click events', () => {
    const handleClick = vi.fn();
    render(
      <Button variant="primary" onClick={handleClick}>
        Execute Query
      </Button>
    );
    const btn = screen.getByRole('button', { name: /execute query/i });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders Button in loading state and disables click', () => {
    const handleClick = vi.fn();
    render(
      <Button loading onClick={handleClick}>
        Loading Data
      </Button>
    );
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('renders Badge with correct variant styling', () => {
    render(<Badge variant="emerald">VERIFIED</Badge>);
    expect(screen.getByText('VERIFIED')).toBeInTheDocument();
  });

  it('renders StatusBadge for answerability correctly', () => {
    render(<StatusBadge type="answerability" status="insufficient_evidence" />);
    expect(screen.getByText(/insufficient evidence/i)).toBeInTheDocument();
  });

  it('renders Alert component with dismiss trigger', () => {
    const handleClose = vi.fn();
    render(
      <Alert variant="warning" title="Warning Note" onClose={handleClose}>
        Grounding threshold below 90%
      </Alert>
    );
    expect(screen.getByText('Warning Note')).toBeInTheDocument();
    expect(screen.getByText(/grounding threshold below 90%/i)).toBeInTheDocument();
    const closeBtn = screen.getByLabelText(/dismiss alert/i);
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders Input with labels and helper text', () => {
    render(
      <Input
        label="Document Title"
        placeholder="Apple 10-K"
        helperText="Enter official SEC disclosure title"
      />
    );
    expect(screen.getByText('Document Title')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Apple 10-K')).toBeInTheDocument();
    expect(screen.getByText('Enter official SEC disclosure title')).toBeInTheDocument();
  });

  it('renders Card with header and custom footer', () => {
    render(
      <Card title="Balance Sheet Analysis" subtitle="Q4 2024" footer={<div>Card Footer Note</div>}>
        <div>Card Main Content</div>
      </Card>
    );
    expect(screen.getByText('Balance Sheet Analysis')).toBeInTheDocument();
    expect(screen.getByText('Q4 2024')).toBeInTheDocument();
    expect(screen.getByText('Card Main Content')).toBeInTheDocument();
    expect(screen.getByText('Card Footer Note')).toBeInTheDocument();
  });
});
