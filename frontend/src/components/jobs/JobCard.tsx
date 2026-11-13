import React from 'react'
import {Link} from 'react-router-dom'
import {formatJobDate,jobPath,jobLastVerified,jobStatusLabel,jobCanApply,JobNotification} from '../../services/jobs'

const detail=(value?:string|null)=>value||'See official notice'

export default function JobCard({job,compact=false}:{job:JobNotification;compact?:boolean}){
  const applyUrl=job.application_url||job.official_notice_url
  const canApply=jobCanApply(job)
  return <article className={`job-card ${compact?'job-card-compact':''}`}>
    <div className="job-card-heading"><span className={`job-type-icon job-${job.job_type}`} aria-hidden="true">{job.job_type==='government'?'▥':'▣'}</span><div><div className="job-label-row"><span className={`job-type-badge ${job.job_type}`}>{job.job_type==='government'?'Government':'Private'}</span>{job.is_featured&&<span className="job-featured">Highlighted</span>}</div><h3><Link to={jobPath(job)}>{job.title}</Link></h3><p>{job.organization}</p>{job.location&&<small>⌖ {job.location}{job.appointment_type?` · ${job.appointment_type}`:''}</small>}</div></div>
    {!compact&&<><dl className="job-facts"><div><dt>Qualification</dt><dd>{detail(job.qualification)}</dd></div><div><dt>Age limit</dt><dd>{detail(job.age_limit)}</dd></div><div><dt>Application fee</dt><dd>{detail(job.application_fee)}</dd></div><div><dt>Vacancies</dt><dd>{detail(job.vacancies)}</dd></div></dl><div className="job-deadline"><span>Application status</span><strong>{jobStatusLabel(job)}</strong><small>Last date: {formatJobDate(job.deadline)}</small><small>{jobLastVerified(job)}</small></div></>}
    <div className="job-card-footer"><span className="verified-source">✓ {jobStatusLabel(job)} · {jobLastVerified(job)}</span><div><a className="btn btn-secondary small" href={applyUrl} target="_blank" rel="noopener noreferrer">{canApply?'Official website ↗':'Check official portal ↗'}</a><Link className="btn btn-primary small" to={jobPath(job)}>{canApply?'View Details &amp; Apply':'View notice details'}</Link></div></div>
  </article>
}
