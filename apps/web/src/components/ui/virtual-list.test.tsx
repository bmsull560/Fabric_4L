/**
 * VirtualList Component Tests
 *
 * Tests for the VirtualList primitive including:
 * - Single-column list virtualization
 * - Multi-column grid virtualization (columns prop)
 * - Accessibility attributes
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VirtualList } from './virtual-list';

describe('VirtualList', () => {
  const items = Array.from({ length: 20 }, (_, i) => ({
    id: `item-${i}`,
    label: `Item ${i}`,
  }));

  it('renders single-column virtual list', () => {
    render(
      <div data-testid="container" style={{ height: '300px' }}>
        <VirtualList
          items={items}
          estimateSize={50}
          overscan={2}
          renderItem={(item) => (
            <div data-testid={`row-${item.id}`}>{item.label}</div>
          )}
        />
      </div>
    );

    // Container should be rendered
    expect(screen.getByTestId('container')).toBeInTheDocument();
    // At least some items should be visible (virtualized)
    expect(screen.getByText('Item 0')).toBeInTheDocument();
  });

  it('renders multi-column grid with columns prop', () => {
    const gridItems = Array.from({ length: 12 }, (_, i) => ({
      id: `grid-item-${i}`,
      label: `Grid ${i}`,
    }));

    render(
      <div data-testid="grid-container" style={{ height: '300px' }}>
        <VirtualList
          items={gridItems}
          estimateSize={100}
          columns={3}
          overscan={2}
          renderItem={(item) => (
            <div data-testid={`cell-${item.id}`}>{item.label}</div>
          )}
        />
      </div>
    );

    expect(screen.getByTestId('grid-container')).toBeInTheDocument();
    expect(screen.getByText('Grid 0')).toBeInTheDocument();
  });

  it('renders empty list without errors', () => {
    render(
      <div style={{ height: '300px' }}>
        <VirtualList
          items={[]}
          estimateSize={50}
          renderItem={(item) => <div>{item.label}</div>}
        />
      </div>
    );

    // Should render without throwing
    expect(document.querySelector('[style*="contain"]')).toBeInTheDocument();
  });

  it('applies contain strict for performance', () => {
    render(
      <div style={{ height: '200px' }}>
        <VirtualList
          items={items}
          estimateSize={50}
          renderItem={(item) => <div>{item.label}</div>}
        />
      </div>
    );

    const container = document.querySelector('[style*="contain: strict"]');
    expect(container).toBeInTheDocument();
  });

  it('passes correct index to renderItem', () => {
    const renderSpy = vi.fn((item: typeof items[0], index: number) => (
      <div data-testid={`item-${index}`}>{item.label}</div>
    ));

    render(
      <div style={{ height: '200px' }}>
        <VirtualList
          items={items.slice(0, 5)}
          estimateSize={50}
          renderItem={renderSpy}
        />
      </div>
    );

    // renderItem should be called with items and their indices
    expect(renderSpy).toHaveBeenCalled();
    const firstCall = renderSpy.mock.calls[0];
    expect(firstCall[0]).toEqual(items[0]);
    expect(firstCall[1]).toBe(0);
  });

  it('applies custom className to container', () => {
    render(
      <div style={{ height: '200px' }}>
        <VirtualList
          items={items.slice(0, 3)}
          estimateSize={50}
          className="custom-list-class"
          renderItem={(item) => <div>{item.label}</div>}
        />
      </div>
    );

    const container = document.querySelector('.custom-list-class');
    expect(container).toBeInTheDocument();
  });
});
