// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ensureVisitorSession, generateItinerary, getLocalVoices, SESSION_KEY } from './api.js'


function response(payload, ok = true, status = 200) {
  return Promise.resolve({ ok, status, json: () => Promise.resolve(payload) })
}


describe('tourism API client', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('creates and persists an anonymous visitor session once', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockReturnValue(response({ id: 'session-1' }, true, 201))

    expect(await ensureVisitorSession()).toBe('session-1')
    expect(await ensureVisitorSession()).toBe('session-1')
    expect(localStorage.getItem(SESSION_KEY)).toBe('session-1')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('sends the visitor session header when generating a route', async () => {
    localStorage.setItem(SESSION_KEY, 'session-2')
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockReturnValue(response({ id: 3 }, true, 201))

    await generateItinerary({ preference_tags: ['岭南建筑'] })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/itineraries/generate/',
      expect.objectContaining({
        headers: expect.objectContaining({ 'X-Visitor-Session-ID': 'session-2' }),
      }),
    )
  })

  it('loads local voices from the local voices endpoint', async () => {
    const voices = [{ id: 1, title: '乡音记录一' }]
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockReturnValue(response(voices))

    await expect(getLocalVoices()).resolves.toEqual(voices)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/local-voices/',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })
})
