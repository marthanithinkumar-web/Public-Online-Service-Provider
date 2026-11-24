import React, {useRef, useState} from 'react'

type Detector = new () => {detect(image: ImageBitmap): Promise<Array<{rawValue: string}>>}
const noticeTerms = /deadline|last date|closing date|eligib|qualification|documents?|certificate|fee|अंतिम|पात्रता|दस्तावेज|शुल्क|గడువు|అర్హత|పత్రాలు|రుసుము|ఫీజు/i

async function readNotice(file: File): Promise<string> {
  if (/\.txt$/i.test(file.name)) {
    if (file.size > 256 * 1024) throw new Error('Choose a text file smaller than 256 KB.')
    return new TextDecoder('utf-8', {fatal: true}).decode(await file.arrayBuffer())
  }
  if (!/\.png$/i.test(file.name)) throw new Error('Choose a UTF-8 text file or PNG image.')
  const DetectorClass = (window as Window & {TextDetector?: Detector}).TextDetector
  if (!DetectorClass || typeof createImageBitmap !== 'function') {
    throw new Error('This browser cannot read text from images. Choose a text file instead.')
  }
  if (file.size > 4 * 1024 * 1024) throw new Error('Choose a PNG smaller than 4 MB.')
  const header = new Uint8Array(await file.slice(0, 24).arrayBuffer())
  const signature = [137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82]
  if (header.length < 24 || !signature.every((value, i) => header[i] === value)) {
    throw new Error('Choose a valid PNG image.')
  }
  const view = new DataView(header.buffer)
  const pixels = view.getUint32(16) * view.getUint32(20)
  if (pixels === 0 || pixels > 8000000) throw new Error('Choose a PNG with at most 8 million pixels.')
  const bitmap = await createImageBitmap(file)
  try {
    const blocks = await new DetectorClass().detect(bitmap)
    return blocks.map(block => block.rawValue).join('\n')
  } finally {
    bitmap.close()
  }
}

export default function LocalNoticeReader() {
  const version = useRef(0)
  const [lines, setLines] = useState<string[]>([])
  const [status, setStatus] = useState('')
  async function select(file?: File) {
    const current = ++version.current
    setLines([])
    setStatus(file ? 'Reading notice…' : '')
    if (!file) return
    try {
      const text = await readNotice(file)
      if (version.current !== current) return
      const matches = text.split(/\r?\n/).map(line => line.trim()).filter(line => noticeTerms.test(line))
      setLines(matches.slice(0, 12).map(line => line.slice(0, 600)))
      setStatus(matches.length ? 'Excerpts from your file. Confirm dates and requirements with the issuing authority.' : 'No deadline, eligibility, fee or document lines were recognized.')
    } catch (error) {
      if (version.current === current) setStatus(error instanceof Error && error.constructor === Error
        ? error.message : 'Could not read this file. Try a UTF-8 text file.')
    }
  }
  return <details onToggle={event => {if (!event.currentTarget.open) void select()}}>
    <summary>Read a public notice on this device</summary>
    <p>Choose a public notice to find deadlines, eligibility, fees and required documents. POSP keeps it out of your chat and provider requests.</p>
    <label>Notice file <input type="file" accept=".txt,.png" onChange={event => {
      const file = event.target.files?.[0]
      event.target.value = ''
      void select(file)
    }}/></label>
    <p role="status">{status}</p>
    {lines.length > 0 && <ul>{lines.map((line, i) => <li key={i} style={{overflowWrap:'anywhere'}}>{line}</li>)}</ul>}
  </details>
}
