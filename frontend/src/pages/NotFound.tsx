import {Link} from 'react-router-dom'

export default function NotFound(){
  return <div className="form-page"><section className="form-hero"><span className="eyebrow">Page not found</span><h1>We couldn’t find that page</h1><p>The link may be old or incomplete. Return home, search for a service, or contact the provider if you still need help.</p><div className="cta-row"><Link className="btn btn-primary" to="/#service-search">Search services</Link><Link className="btn btn-secondary" to="/contact">Contact support</Link></div></section></div>
}
