// @vitest-environment jsdom

import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'


const bootstrap = {
  zones: [],
  themes: [
    { id: 1, name: '岭南建筑', icon: 'building', description: '建筑线索' },
    { id: 2, name: '自然水岸', icon: 'leaf', description: '水岸线索' },
  ],
  attractions: [
    {
      id: 1,
      name: '村史馆',
      slug: 'village-history-museum',
      subtitle: '祠堂里的时光容器',
      cover_image_url: '/static/村史馆.png',
      zone: { id: 1, name: '文乡雅集区' },
      map_position: { x: 40, y: 10 },
      themes: ['岭南建筑'],
    },
  ],
}

const route = {
  id: 1,
  score: 24,
  total_estimated_minutes: 30,
  attraction_sequence: [1],
  zone_sequence: [1],
  narrative_bridge: {},
  legs: [],
  stops: [
    {
      ...bootstrap.attractions[0],
      depth_level: 2,
      matched_themes: ['岭南建筑'],
      recommendation: '匹配兴趣：岭南建筑；深度故事节点',
      visit_minutes: 10,
      zone: { id: 1, name: '文乡雅集区', visual_cue: '看到村史馆木门' },
    },
  ],
}

function jsonResponse(payload, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(payload),
  })
}

describe('Bijiang village website', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('scrollTo', vi.fn())
    vi.stubGlobal(
      'fetch',
      vi.fn((url) => {
        if (url === '/api/v1/sessions/') return jsonResponse({ id: 'session-1' }, 201)
        if (url === '/api/v1/bootstrap/') return jsonResponse(bootstrap)
        if (url === '/api/v1/itineraries/generate/') return jsonResponse(route, 201)
        if (url === '/api/v1/attractions/village-history-museum/') {
          return jsonResponse({
            ...bootstrap.attractions[0],
            story: { full_text: '村史馆坐落于慕堂苏公祠内。', fun_fact: '同源工匠' },
          })
        }
        return jsonResponse({ detail: 'not found' }, 404)
      }),
    )
  })

  afterEach(() => {
    document.body.innerHTML = ''
    history.replaceState({}, '', '/')
    vi.unstubAllGlobals()
  })

  it('loads real themes, generates a route, and opens its story', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()

    await wrapper.get('[data-route="interests"]').trigger('click')
    expect(wrapper.text()).toContain('岭南建筑')
    expect(wrapper.text()).toContain('自然水岸')

    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('村史馆')
    expect(wrapper.text()).toContain('匹配兴趣：岭南建筑')

    await wrapper.get('[data-attraction-slug="village-history-museum"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('村史馆坐落于慕堂苏公祠内')
  })

  it('reuses a stored visitor session instead of creating another one', async () => {
    localStorage.setItem('bijiang_visitor_session_id', 'stored-session')
    mount(App, { attachTo: document.body })
    await flushPromises()

    expect(fetch).not.toHaveBeenCalledWith(
      '/api/v1/sessions/',
      expect.anything(),
    )
  })
})
