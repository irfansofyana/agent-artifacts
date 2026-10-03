// Tool Pulse: read-only observation, UI decoration, and a local command.
let calls = 0

export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'pulse',
      description: 'Show tool calls observed since this mod loaded',
    })
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    calls += 1
    $.ui.invalidate('ui.render')
    return next(e)
  })

  on('command.run', { command: 'pulse' }, async () => ({
    text: 'Tool Pulse observed ' + calls + ' tool calls since this mod loaded.',
  }))

  on('ui.render', { component: 'Spinner' }, async ($, e, next) =>
    next({ ...e, props: { ...e.props, suffix: ' · tools: ' + calls } }),
  )
}
