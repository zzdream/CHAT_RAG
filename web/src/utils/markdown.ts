import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { copyIconSvg } from '@/utils/chat-icons'

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function normalizeLang(lang: string): string {
  const trimmed = lang.trim().toLowerCase()
  return trimmed || 'text'
}

function highlightCode(code: string, lang: string): string {
  if (lang && lang !== 'text' && hljs.getLanguage(lang)) {
    try {
      return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
    } catch {
      // fall through
    }
  }

  return escapeHtml(code)
}

function renderCodeBlock(code: string, lang: string): string {
  const language = normalizeLang(lang)
  const highlighted = highlightCode(code, language)

  return (
    `<div class="code-block">`
    + `<div class="code-block__header">`
    + `<span class="code-block__lang">${escapeHtml(language)}</span>`
    + `<button type="button" class="code-block__copy" title="复制代码" aria-label="复制代码">${copyIconSvg(14)}</button>`
    + `</div>`
    + `<pre class="hljs"><code class="language-${escapeHtml(language)}">${highlighted}</code></pre>`
    + `</div>`
  )
}

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code: string, lang: string): string {
    return renderCodeBlock(code, lang)
  }
})

export function renderMarkdown(content: string): string {
  if (!content.trim()) return ''
  return md.render(content)
}
