import React from 'react'
import {Link} from 'react-router-dom'
import {deadlineText,formatJobDate,jobPath,JobNotification} from '../../services/jobs'

const detail=(value?:string|null)=>value||'See official notice'

export default function JobCard({job,compact=false}:{job:JobNotification;compact?:boolean}){
  const applyUrl=job.application_url||job.official_notice_url
  return <article className={`job-card ${compact?'job-card-compact':''}`}>
    <div className="job-card-heading"><span className={`job-type-icon job-${job.job_type}`} aria-hidden="true">{job.job_type==='government'?'▥':'▣'}</span><div><div className="job-label-row"><span className={`job-type-badge ${job.job_type}`}>{job.job_type==='government'?'Government':'Private'}</span>{job.is_featured&&<span className="job-featured">Highlighted</span>}</div><h3><Link to={jobPath(job)}>{job.title}</Link></h3><p>{job.organization}</p>{job.location&&<small>⌖ {job.location}{job.appointment_type?` · ${job.appointment_type}`:''}</small>}</div></div>
    <dl className="job-facts"><div><dt>Qualification</dt><dd>{detail(job.qualification)}</dd></div><div><dt>Age limit</dt><dd>{detail(job.age_limit)}</dd></div><div><dt>Application fee</dt><dd>{detail(job.application_fee)}</dd></div>{!compact&&<div><dt>Vacancies</dt><dd>{detail(job.vacancies)}</dd></div>}</dl>
    <div className="job-deadline"><span>Last date</span><strong>{formatJobDate(job.deadline)}</strong><small>{deadlineText(job.deadline)}</small></div>
    <div className="job-card-footer"><span className="verified-source">✓ Official source checked</span><div><Link className="btn btn-secondary small" to={jobPath(job)}>View details</Link><a className="btn btn-primary small" href={applyUrl} target="_blank" rel="noopener noreferrer">Official website ↗</a></div></div>
  </article>
}
