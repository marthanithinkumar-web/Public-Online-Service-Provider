import {readFileSync} from 'node:fs'
import {describe,expect,it} from 'vitest'

const source=readFileSync(new URL('../UniversalServiceRequestV2.tsx',import.meta.url),'utf8')

describe('job and scholarship application notification context',()=>{
  it('shows notification details in the application flow',()=>{
    expect(source).toContain('Selected job notification')
    expect(source).toContain('Qualification')
    expect(source).toContain('Age limit')
    expect(source).toContain('Official application fee')
    expect(source).toContain('Selected scholarship notification')
    expect(source).toContain('Eligibility')
    expect(source).toContain('Income limit')
    expect(source).toContain('Award / benefit')
  })

  it('stores selected notification context with the submitted request',()=>{
    expect(source).toContain('job_qualification:job.qualification')
    expect(source).toContain('job_deadline:job.deadline')
    expect(source).toContain('scholarship_eligibility:scholarship.eligibility')
    expect(source).toContain('scholarship_deadline:scholarship.deadline')
  })
})
