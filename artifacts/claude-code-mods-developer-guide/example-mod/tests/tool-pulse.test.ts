import { expect, test } from 'claude-code/testing'

test('/pulse reports observed tool calls', async ($, on) => {
  on('tool.call', () => ({ result: 'ok' }))
  on('command.register', () => ({ value: undefined }))
  on('ui.invalidate', () => ({ value: undefined }))
  on('session.start', () => ({ cwd: '/work' }))

  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  await $.tool.call({ tool: 'Read', file_path: 'README.md' })
  await $.tool.call({ tool: 'Bash', command: 'pwd' })
  const answer = await $.command.run({ command: 'pulse', args: '' })
  expect(answer.text).toBe('Tool Pulse observed 2 tool calls since this mod loaded.')
})
