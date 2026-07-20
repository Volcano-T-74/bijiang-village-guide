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
        if (url === '/api/v1/events/') return jsonResponse({ id: 1 }, 201)
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

  it('renders route attraction introductions without detail links', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()

    await wrapper.get('[data-route="interests"]').trigger('click')
    expect(wrapper.text()).toContain('岭南建筑')
    expect(wrapper.text()).toContain('自然水岸')

    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('村史馆')
    expect(wrapper.text()).toContain('匹配兴趣：岭南建筑')

    expect(wrapper.find('.route-stop').element.tagName).toBe('ARTICLE')
    expect(wrapper.find('[data-attraction-slug]').exists()).toBe(false)
    expect(wrapper.find('.route-stop .card-arrow').exists()).toBe(false)
  })

  it('starts every stamp locked and derives progress from visited places', async () => {
    history.replaceState({}, '', '/#stamps')
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()

    expect(wrapper.text()).toContain('已点亮 0 / 1 个印章点')
    expect(wrapper.findAll('.stamp-card.is-locked')).toHaveLength(1)
    expect(wrapper.findAll('.stamp-card.is-lit')).toHaveLength(0)
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

  it('requests location on demand and never uploads the coordinates', async () => {
    const getCurrentPosition = vi.fn((success) => success({
      coords: { latitude: 23.1234567, longitude: 113.7654321, accuracy: 18.4 },
    }))
    vi.stubGlobal('navigator', { geolocation: { getCurrentPosition } })
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-action="request-location"]').trigger('click')
    await flushPromises()

    expect(getCurrentPosition).toHaveBeenCalledWith(
      expect.any(Function),
      expect.any(Function),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
    )
    expect(wrapper.text()).toContain('23.123457')
    expect(wrapper.text()).toContain('113.765432')
    for (const call of fetch.mock.calls) {
      expect(call[1]?.body || '').not.toContain('23.1234567')
      expect(call[1]?.body || '').not.toContain('113.7654321')
    }
  })

  it('requires confirmation before recording a simulated arrival', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-map-slug="village-history-museum"]').trigger('click')
    expect(fetch).not.toHaveBeenCalledWith(
      '/api/v1/events/',
      expect.objectContaining({ body: expect.stringContaining('simulated_arrival') }),
    )

    await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
    await flushPromises()
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/events/',
      expect.objectContaining({
        body: expect.stringContaining('simulated_arrival'),
      }),
    )
    expect(localStorage.getItem('bijiang_indoor_demo_state')).toContain(
      'village-history-museum',
    )
  })

  it('shows a dismissible stamp celebration only on the first simulated arrival', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-map-slug="village-history-museum"]').trigger('click')
    await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="dialog"]').text()).toContain('恭喜你已点亮')
    expect(wrapper.get('[role="dialog"]').text()).toContain('村史馆')
    await wrapper.get('[data-action="close-stamp-unlock"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await wrapper.get('[data-map-slug="village-history-museum"]').trigger('click')
    await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('closes the stamp celebration when its backdrop is clicked', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-map-slug="village-history-museum"]').trigger('click')
    await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-dismiss-stamp-unlock]').trigger('click')

    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('keeps the simulated map available when location permission is denied', async () => {
    const getCurrentPosition = vi.fn((_, failure) => failure({ code: 1 }))
    vi.stubGlobal('navigator', { geolocation: { getCurrentPosition } })
    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-action="request-location"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('你已拒绝定位权限')
    expect(wrapper.find('[data-map-slug="village-history-museum"]').exists()).toBe(true)
  })

  it('restores the simulated location and route after a refresh', async () => {
    localStorage.setItem('bijiang_indoor_demo_state', JSON.stringify({
      version: 2,
      interests: ['岭南建筑'],
      duration: 60,
      mode: 'relaxed',
      route,
      currentSimulatedSlug: 'village-history-museum',
      visitedSlugs: ['village-history-museum'],
    }))
    history.replaceState({}, '', '/#route')

    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()

    expect(wrapper.find('[data-map-slug="village-history-museum"].is-current').exists()).toBe(true)
    expect(wrapper.find('[data-map-slug="village-history-museum"].is-visited').exists()).toBe(true)
  })

  it('restores unlocked stamps without replaying the celebration after refresh', async () => {
    localStorage.setItem('bijiang_indoor_demo_state', JSON.stringify({
      version: 2,
      interests: ['岭南建筑'],
      duration: 60,
      mode: 'relaxed',
      route,
      currentSimulatedSlug: 'village-history-museum',
      visitedSlugs: ['village-history-museum'],
    }))
    history.replaceState({}, '', '/#stamps')

    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()

    expect(wrapper.text()).toContain('已点亮 1 / 1 个印章点')
    expect(wrapper.findAll('.stamp-card.is-lit')).toHaveLength(1)
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('drops an old saved route but preserves simulated progress', async () => {
    localStorage.setItem('bijiang_indoor_demo_state', JSON.stringify({
      interests: ['岭南建筑'],
      duration: 60,
      mode: 'relaxed',
      route,
      currentSimulatedSlug: 'village-history-museum',
      visitedSlugs: ['village-history-museum'],
    }))
    history.replaceState({}, '', '/#route')

    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()

    expect(wrapper.text()).toContain('尚未生成专属路线')
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-map-slug="village-history-museum"].is-current').exists()).toBe(true)
    expect(wrapper.find('[data-map-slug="village-history-museum"].is-visited').exists()).toBe(true)
  })

  it('uses the bridge before choosing one new branch in the local fallback route', async () => {
    const demoBootstrap = {
      ...bootstrap,
      attractions: [
        bootstrap.attractions[0],
        {
          ...bootstrap.attractions[0],
          id: 2,
          name: '黄氏宗祠',
          slug: 'huang-ancestral-hall',
          map_position: { x: 14, y: 31 },
        },
        {
          ...bootstrap.attractions[0],
          id: 3,
          name: '碧溪书公祠',
          slug: 'bixi-scholar-hall',
          map_position: { x: 69, y: 17 },
        },
        {
          ...bootstrap.attractions[0],
          id: 4,
          name: '古桥',
          slug: 'ancient-bridge',
          map_position: { x: 50, y: 45 },
        },
        {
          ...bootstrap.attractions[0],
          id: 5,
          name: '诗词巷',
          slug: 'poetry-lane',
          map_position: { x: 21, y: 54 },
        },
      ],
    }
    fetch.mockImplementation((url) => {
      if (url === '/api/v1/sessions/') return jsonResponse({ id: 'session-1' }, 201)
      if (url === '/api/v1/bootstrap/') return jsonResponse(demoBootstrap)
      if (url === '/api/v1/itineraries/generate/') return jsonResponse({ detail: 'offline' }, 503)
      if (url === '/api/v1/events/') return jsonResponse({ id: 1 }, 201)
      return jsonResponse({ detail: 'not found' }, 404)
    })

    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()

    const stopNames = wrapper.findAll('.route-stop strong').map(item => item.text())
    expect(stopNames[0]).toBe('村史馆')
    expect(stopNames[1]).toBe('古桥')
    expect(stopNames).not.toContain('黄氏宗祠')
    expect(stopNames).not.toEqual(expect.arrayContaining(['碧溪书公祠', '诗词巷']))
    expect(
      wrapper.findAll('.map-marker.is-route').map(item => item.text()),
    ).toEqual(stopNames.map((_, index) => String(index + 1)))
    const eventBodies = fetch.mock.calls
      .filter(([url]) => url === '/api/v1/events/')
      .map(([, options]) => options.body)
    expect(eventBodies.join('')).not.toContain('local-route-')
  })

  it('replans an off-route arrival even when event recording fails', async () => {
    const eastPlace = {
      ...bootstrap.attractions[0],
      id: 2,
      name: '碧溪书公祠',
      slug: 'bixi-scholar-hall',
      map_position: { x: 69, y: 17 },
    }
    const demoBootstrap = { ...bootstrap, attractions: [bootstrap.attractions[0], eastPlace] }
    let itineraryCalls = 0
    fetch.mockImplementation((url) => {
      if (url === '/api/v1/sessions/') return jsonResponse({ id: 'session-1' }, 201)
      if (url === '/api/v1/bootstrap/') return jsonResponse(demoBootstrap)
      if (url === '/api/v1/itineraries/generate/') {
        itineraryCalls += 1
        return jsonResponse(itineraryCalls === 1 ? route : {
          ...route,
          id: 2,
          stops: [{ ...route.stops[0], ...eastPlace }],
        }, 201)
      }
      if (url === '/api/v1/events/') return jsonResponse({ detail: 'offline' }, 503)
      return jsonResponse({ detail: 'not found' }, 404)
    })

    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-map-slug="bixi-scholar-hall"]').trigger('click')
    await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
    await flushPromises()

    expect(itineraryCalls).toBe(2)
    expect(wrapper.findAll('.route-stop strong').map(item => item.text())).toEqual(['村史馆'])
    expect(wrapper.find('[data-map-slug="bixi-scholar-hall"].is-current').exists()).toBe(true)
    expect(wrapper.text()).toContain('暂无可用剩余路线')
  })

  it('does not cross from one bank to the other in a bridge-start local fallback', async () => {
    const demoBootstrap = {
      ...bootstrap,
      attractions: [
        bootstrap.attractions[0],
        { ...bootstrap.attractions[0], id: 2, name: '碧溪书公祠', slug: 'bixi-scholar-hall', map_position: { x: 69, y: 17 } },
        { ...bootstrap.attractions[0], id: 3, name: '古桥', slug: 'ancient-bridge', map_position: { x: 50, y: 45 } },
      ],
    }
    let itineraryCalls = 0
    fetch.mockImplementation((url) => {
      if (url === '/api/v1/sessions/') return jsonResponse({ id: 'session-1' }, 201)
      if (url === '/api/v1/bootstrap/') return jsonResponse(demoBootstrap)
      if (url === '/api/v1/itineraries/generate/') {
        itineraryCalls += 1
        return itineraryCalls === 1 ? jsonResponse(route, 201) : jsonResponse({ detail: 'offline' }, 503)
      }
      if (url === '/api/v1/events/') return jsonResponse({ id: 1 }, 201)
      return jsonResponse({ detail: 'not found' }, 404)
    })

    const wrapper = mount(App, { attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-route="interests"]').trigger('click')
    await wrapper.get('[data-action="generate-route"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-map-slug="ancient-bridge"]').trigger('click')
    await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
    await flushPromises()

    const stopNames = wrapper.findAll('.route-stop strong').map(item => item.text())
    expect(stopNames).toContain('古桥')
    expect(stopNames).not.toEqual(expect.arrayContaining(['村史馆', '碧溪书公祠']))
  })
})
