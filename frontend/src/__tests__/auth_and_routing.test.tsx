import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginForm } from '../components/auth/LoginForm';
import { AuthProvider } from '../context/AuthContext';

describe('Auth and Route Security', () => {
  it('renders LoginForm with corporate email and password fields', () => {
    const handleSwitch = vi.fn();
    render(
      <AuthProvider>
        <LoginForm onSwitchToRegister={handleSwitch} />
      </AuthProvider>
    );

    expect(screen.getByText(/FINARQ/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/corporate email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in to workspace/i })).toBeInTheDocument();

    const registerLink = screen.getByRole('button', { name: /register organization/i });
    fireEvent.click(registerLink);
    expect(handleSwitch).toHaveBeenCalledTimes(1);
  });

  it('populates quick test personas when clicking demo badges', () => {
    render(
      <AuthProvider>
        <LoginForm onSwitchToRegister={vi.fn()} />
      </AuthProvider>
    );

    const tenantABtn = screen.getByRole('button', { name: /Tenant A \(Alpha\)/i });
    fireEvent.click(tenantABtn);

    const emailInput = screen.getByLabelText(/corporate email/i) as HTMLInputElement;
    expect(emailInput.value).toBe('tenant_a@financial.org');
  });
});
