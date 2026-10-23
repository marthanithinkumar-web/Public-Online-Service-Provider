import assert from 'node:assert/strict'
import {isDeadlineActive} from './seo-catalog.mjs'

const today='2026-10-16'
assert.equal(isDeadlineActive({deadline:'2026-10-15'},today),false,'past-deadline listing must be excluded')
assert.equal(isDeadlineActive({deadline:'2026-10-16'},today),true,'deadline today remains visible for the published date')
assert.equal(isDeadlineActive({deadline:'2026-10-31'},today),true,'future deadline remains visible')
assert.equal(isDeadlineActive({deadline:'not-a-date'},today),false,'invalid deadline must not be advertised as active')
assert.equal(isDeadlineActive({},today),true,'missing deadline remains unchanged pending source-status policy')
console.log('Expiry-filter regression checks passed.')
