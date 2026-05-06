/**
 * VirtualList Visual Regression Tests
 *
 * Snapshot tests to ensure VirtualList rendering does not unexpectedly change.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { VirtualList } from './virtual-list';

describe('VirtualList visual regression', () => {
  it('single-column list matches snapshot', () => {
    const items = Array.from({ length: 5 }, (_, i) => ({
      id: `item-${i}`,
      label: `Item ${i}`,
    }));

    const { container } = render(
      <div style={{ height: '300px' }}>
        <VirtualList
          items={items}
          estimateSize={50}
          renderItem={(item) => (
            <div className="p-4 border-b">{item.label}</div>
          )}
        />
      </div>
    );

    expect(container).toMatchSnapshot();
  });

  it('multi-column grid matches snapshot', () => {
    const items = Array.from({ length: 6 }, (_, i) => ({
      id: `grid-${i}`,
      label: `Grid ${i}`,
    }));

    const { container } = render(
      <div style={{ height: '300px' }}>
        <VirtualList
          items={items}
          estimateSize={100}
          columns={3}
          renderItem={(item) => (
            <div className="p-4 border rounded">{item.label}</div>
          )}
        />
      </div>
    );

    expect(container).toMatchSnapshot();
  });

  it('empty list matches snapshot', () => {
    const { container } = render(
      <div style={{ height: '200px' }}>
        <VirtualList
          items={[]}
          estimateSize={50}
          renderItem={(item: { label: string }) => <div>{item.label}</div>}
        />
      </div>
    );

    expect(container).toMatchSnapshot();
  });
});
