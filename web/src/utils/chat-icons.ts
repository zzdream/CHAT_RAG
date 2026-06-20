/** 聊天 UI 用 SVG 图标（Markdown v-html 与 Vue 组件共用） */

export function copyIconSvg(size = 16): string {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" `
    + `viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" `
    + `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">`
    + `<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>`
  + `<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>`
    + `</svg>`
  )
}

export function regenerateIconSvg(size = 16): string {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" `
    + `viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" `
    + `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">`
    + `<path d="M1 4v6h6"></path>`
    + `<path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>`
    + `</svg>`
  )
}

export function checkIconSvg(size = 16): string {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" `
    + `viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" `
    + `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">`
    + `<path d="M20 6 9 17l-5-5"></path>`
    + `</svg>`
  )
}
