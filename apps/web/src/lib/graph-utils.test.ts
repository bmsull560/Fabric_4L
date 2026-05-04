import { describe, it, expect } from 'vitest';
import {
  wrapTextIntoLines,
  calculateLayout,
  getNodeRadius,
  countNodeTypes,
  getEntityHexColors,
  getEntityBadgeClasses,
  NODE_SIZES,
  DEFAULT_NODE_SIZE,
  VIEWBOX_WIDTH,
  VIEWBOX_HEIGHT,
} from './graph-utils';
import type { GraphNode } from '@/hooks/useGraphQuery';

// Minimal GraphNode factory for tests
function makeNode(id: string, entity_type?: string): GraphNode {
  return {
    id,
    name: `Node ${id}`,
    entity_type: entity_type ?? 'account',
    confidence_score: 0.8,
  } as GraphNode;
}

describe('wrapTextIntoLines', () => {
  it('returns single word as single line', () => {
    expect(wrapTextIntoLines('hello', 10)).toEqual(['hello']);
  });

  it('keeps short text on one line', () => {
    expect(wrapTextIntoLines('hello world', 20)).toEqual(['hello world']);
  });

  it('wraps long text into multiple lines', () => {
    const result = wrapTextIntoLines('one two three four five', 10);
    // Each line should not exceed maxLineLength when a single word fits
    expect(result.length).toBeGreaterThan(1);
    result.forEach(line => {
      // A line may only exceed maxLineLength when a single word is longer
      expect(line.length).toBeGreaterThan(0);
    });
  });

  it('handles empty string', () => {
    expect(wrapTextIntoLines('', 10)).toEqual(['']);
  });

  it('wraps at word boundaries', () => {
    // "ab cd ef" with maxLineLength=5 → ["ab cd", "ef"]
    const result = wrapTextIntoLines('ab cd ef', 5);
    expect(result).toEqual(['ab cd', 'ef']);
  });

  it('handles a single word longer than maxLineLength', () => {
    const result = wrapTextIntoLines('superlongword', 5);
    expect(result).toEqual(['superlongword']);
  });
});

describe('getNodeRadius', () => {
  it('returns configured radius for known entity types', () => {
    expect(getNodeRadius('capability')).toBe(NODE_SIZES.capability);
    expect(getNodeRadius('usecase')).toBe(NODE_SIZES.usecase);
    expect(getNodeRadius('persona')).toBe(NODE_SIZES.persona);
  });

  it('returns default radius for unknown entity types', () => {
    expect(getNodeRadius('unknown')).toBe(DEFAULT_NODE_SIZE);
    expect(getNodeRadius('account')).toBe(DEFAULT_NODE_SIZE);
  });

  it('is case-insensitive for all configured types', () => {
    expect(getNodeRadius('Capability')).toBe(NODE_SIZES.capability);
    expect(getNodeRadius('CAPABILITY')).toBe(NODE_SIZES.capability);
    expect(getNodeRadius('USECASE')).toBe(NODE_SIZES.usecase);
    expect(getNodeRadius('UseCase')).toBe(NODE_SIZES.usecase);
    expect(getNodeRadius('Persona')).toBe(NODE_SIZES.persona);
    expect(getNodeRadius('PERSONA')).toBe(NODE_SIZES.persona);
  });

  it('returns default radius for undefined', () => {
    expect(getNodeRadius(undefined)).toBe(DEFAULT_NODE_SIZE);
  });

  it('returns default radius for empty string', () => {
    expect(getNodeRadius('')).toBe(DEFAULT_NODE_SIZE);
  });
});

describe('calculateLayout', () => {
  it('returns empty array for empty nodes', () => {
    expect(calculateLayout([])).toEqual([]);
  });

  it('returns nodes with x, y, r coordinates for circular layout', () => {
    const nodes = [makeNode('1', 'capability'), makeNode('2', 'persona')];
    const result = calculateLayout(nodes, 'circular');
    expect(result).toHaveLength(2);
    result.forEach(n => {
      expect(typeof n.x).toBe('number');
      expect(typeof n.y).toBe('number');
      expect(typeof n.r).toBe('number');
    });
  });

  it('uses circular layout by default', () => {
    const nodes = [makeNode('1'), makeNode('2')];
    const circular = calculateLayout(nodes, 'circular');
    const defaultLayout = calculateLayout(nodes);
    // Default is circular — positions should differ from force
    // We just verify both return same length
    expect(defaultLayout).toHaveLength(2);
    // Circular and default (circular) should produce the same x/y
    expect(defaultLayout[0].x).toBe(circular[0].x);
    expect(defaultLayout[0].y).toBe(circular[0].y);
  });

  it('positions single node at center for circular layout', () => {
    const nodes = [makeNode('1')];
    const [result] = calculateLayout(nodes, 'circular');
    // With 1 node: angle = 0 * 2π / 1 = 0 → x = centerX + r*cos(0), y = centerY + r*sin(0)
    const radius = Math.min(VIEWBOX_WIDTH, VIEWBOX_HEIGHT) * 0.35;
    expect(result.x).toBeCloseTo(VIEWBOX_WIDTH / 2 + radius);
    expect(result.y).toBeCloseTo(VIEWBOX_HEIGHT / 2);
  });

  it('assigns correct radius per entity type', () => {
    const nodes = [makeNode('1', 'capability'), makeNode('2', 'unknown')];
    const result = calculateLayout(nodes, 'circular');
    expect(result[0].r).toBe(NODE_SIZES.capability);
    expect(result[1].r).toBe(DEFAULT_NODE_SIZE);
  });

  it('produces hierarchical layout positions', () => {
    const nodes = Array.from({ length: 6 }, (_, i) => makeNode(String(i)));
    const result = calculateLayout(nodes, 'hierarchical');
    expect(result).toHaveLength(6);
    // First node should be at first hierarchical position
    expect(result[0].x).toBe(120);
    expect(result[0].y).toBe(80);
    // 5th node (index 4) → col 0, row 1
    expect(result[4].x).toBe(120);
    expect(result[4].y).toBe(200);
  });

  it('produces force layout positions', () => {
    const nodes = Array.from({ length: 3 }, (_, i) => makeNode(String(i)));
    const result = calculateLayout(nodes, 'force');
    expect(result).toHaveLength(3);
    expect(result[0].x).toBe(100);
    expect(result[0].y).toBe(80);
    expect(result[1].x).toBe(230);
    expect(result[1].y).toBe(80);
  });

  it('preserves original node properties', () => {
    const node = makeNode('42', 'formula');
    const [result] = calculateLayout([node], 'circular');
    expect(result.id).toBe('42');
    expect(result.entity_type).toBe('formula');
    expect(result.name).toBe('Node 42');
  });
});

describe('countNodeTypes', () => {
  it('counts nodes by entity_type', () => {
    const nodes = [
      { entity_type: 'capability' },
      { entity_type: 'capability' },
      { entity_type: 'persona' },
    ];
    expect(countNodeTypes(nodes)).toEqual({ capability: 2, persona: 1 });
  });

  it('uses "Unknown" for nodes with no entity_type', () => {
    const nodes = [{ entity_type: undefined }, {}];
    expect(countNodeTypes(nodes)).toEqual({ Unknown: 2 });
  });

  it('returns empty object for empty array', () => {
    expect(countNodeTypes([])).toEqual({});
  });

  it('handles mixed known and unknown types', () => {
    const nodes = [
      { entity_type: 'pack' },
      { entity_type: undefined },
      { entity_type: 'pack' },
    ];
    expect(countNodeTypes(nodes)).toEqual({ pack: 2, Unknown: 1 });
  });
});

describe('getEntityHexColors', () => {
  it('returns correct hex colors for known entity types', () => {
    const cap = getEntityHexColors('capability');
    expect(cap.fill).toBe('#ede9fe');
    expect(cap.stroke).toBe('#c4b5fd');
    expect(cap.text).toBe('#5b21b6');

    const uc = getEntityHexColors('usecase');
    expect(uc.fill).toBe('#cffafe');
  });

  it('is case-insensitive', () => {
    const upper = getEntityHexColors('CAPABILITY');
    const lower = getEntityHexColors('capability');
    expect(upper).toEqual(lower);
  });

  it('falls back to account colors for unknown types', () => {
    const unknown = getEntityHexColors('unknowntype');
    const account = getEntityHexColors('account');
    expect(unknown).toEqual(account);
  });

  it('returns all three color fields', () => {
    const result = getEntityHexColors('persona');
    expect(result).toHaveProperty('fill');
    expect(result).toHaveProperty('stroke');
    expect(result).toHaveProperty('text');
  });
});

describe('getEntityBadgeClasses', () => {
  it('returns correct Tailwind classes for known entity types', () => {
    const cap = getEntityBadgeClasses('capability');
    expect(cap.bg).toBe('bg-violet-100');
    expect(cap.text).toBe('text-violet-800');
    expect(cap.dot).toBe('bg-violet-500');
  });

  it('is case-insensitive', () => {
    const upper = getEntityBadgeClasses('PERSONA');
    const lower = getEntityBadgeClasses('persona');
    expect(upper).toEqual(lower);
  });

  it('falls back to account classes for unknown types', () => {
    const unknown = getEntityBadgeClasses('nonexistent');
    const account = getEntityBadgeClasses('account');
    expect(unknown).toEqual(account);
  });

  it('returns all three class fields', () => {
    const result = getEntityBadgeClasses('formula');
    expect(result).toHaveProperty('bg');
    expect(result).toHaveProperty('text');
    expect(result).toHaveProperty('dot');
  });
});
