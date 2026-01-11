import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Input from '../../components/ui/Input';

describe('Input Component', () => {
  it('renders with label', () => {
    render(<Input label="Email" id="email-input" />);
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(
      <Input
        label="Email"
        id="email-input"
        error="Invalid email format"
      />
    );
    const input = screen.getByRole('textbox');
    const errorElement = screen.getByText('Invalid email format');

    expect(input).toHaveClass('border-error-500');
    expect(errorElement).toBeInTheDocument();
    expect(errorElement).toHaveClass('text-error-600');
  });

  it('calls onChange handler', () => {
    const handleChange = vi.fn();
    render(
      <Input
        label="Name"
        id="name-input"
        onChange={handleChange}
      />
    );
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'John Doe' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith(expect.any(Object));
    expect((input as HTMLInputElement).value).toBe('John Doe');
  });
});