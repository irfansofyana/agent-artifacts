import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parse } from 'parse5';

const source = readFileSync(new URL('../src/artifacts/llm-api-contracts/content.html', import.meta.url), 'utf8');
const generated = readFileSync(new URL('../artifacts/llm-api-contracts/index.html', import.meta.url), 'utf8');
const manifest = JSON.parse(readFileSync(new URL('../artifacts.json', import.meta.url), 'utf8'));
const visit = (node, fn) => { fn(node); for (const child of node.childNodes || []) visit(child, fn); };

// The source of truth is a body fragment; the renderer owns document chrome.
test('contract field guide covers the named providers and each wire shape', () => {
  const matches = manifest.artifacts.filter(entry => entry.slug === 'llm-api-contracts');
  assert.equal(matches.length, 1);
  for (const term of ['OpenAI', 'Anthropic', 'Amazon Bedrock', 'OpenRouter', 'Google Gemini API',
    'generateContent', 'Interactions', 'previous_response_id', 'tool_result', 'functionResponse']) {
    assert.ok(source.includes(term), `missing ${term}`);
  }
  for (const id of ['mental-model', 'matrix', 'wire', 'legacy', 'chat', 'messages',
    'responses', 'generate-content', 'interactions', 'bedrock', 'tool-loop', 'operations', 'decision']) {
    assert.ok(generated.includes(`id="${id}"`), `missing anchor ${id}`);
  }
  const doc = parse(generated);
  let articleCount = 0;
  let tables = 0;
  let codeBlocks = 0;
  visit(doc, node => {
    const attrs = Object.fromEntries((node.attrs || []).map(attr => [attr.name, attr.value]));
    if (attrs['data-artifact-content'] !== undefined) articleCount++;
    if (node.tagName === 'table') tables++;
    if (node.tagName === 'pre') codeBlocks++;
  });
  assert.equal(articleCount, 1);
  assert.ok(tables >= 2);
  assert.ok(codeBlocks >= 7);
  assert.doesNotMatch(source, /<!doctype|<html\b|<body\b/i);
});
