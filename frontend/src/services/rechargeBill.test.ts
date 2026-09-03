import {describe,expect,it} from 'vitest'
import {validIndianMobileNumber} from './rechargeBill'

describe('Recharge & Bill Payments',()=>{
  it('accepts valid Indian mobile numbers',()=>{
    expect(validIndianMobileNumber('9876543210')).toBe(true)
    expect(validIndianMobileNumber('98765 43210')).toBe(true)
  })

  it('rejects invalid mobile numbers',()=>{
    expect(validIndianMobileNumber('1234567890')).toBe(false)
    expect(validIndianMobileNumber('987654321')).toBe(false)
  })
})
