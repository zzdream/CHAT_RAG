type SpeechRecognitionCtor = new () => SpeechRecognition

type AvailabilityStatus = 'unavailable' | 'downloadable' | 'downloading' | 'available'

type RecognitionMode = 'local' | 'cloud' | 'none'

type SpeechRecognitionOptions = {
  langs?: string[]
  processLocally?: boolean
  quality?: 'command' | 'dictation' | 'conversation'
}

type SpeechRecognitionStatic = SpeechRecognitionCtor & {
  available?: (options: SpeechRecognitionOptions) => Promise<AvailabilityStatus>
  install?: (options: SpeechRecognitionOptions) => Promise<boolean>
}

const START_TIMEOUT_MS = 8000
const LANG_CANDIDATES = ['zh-CN', 'zh']

const QUALITY_CANDIDATES: Array<'dictation' | 'command'> = ['dictation', 'command']

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') return null
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

function getUnsupportedReason(): string {
  if (typeof window === 'undefined') return '当前环境不支持语音输入'
  if (!getSpeechRecognitionCtor()) {
    return '当前浏览器不支持 Web Speech API，请使用 Chrome / Edge / Safari'
  }
  if (!window.isSecureContext) {
    const host = window.location.hostname
    if (host && host !== 'localhost' && host !== '127.0.0.1') {
      return `语音输入需 HTTPS 或 localhost，请改用 http://localhost:${window.location.port || '5173'} 访问`
    }
    return '语音输入需要 HTTPS 或 localhost 安全上下文'
  }
  return ''
}

export function useSpeechRecognition(options?: {
  lang?: string
  onFinal?: (text: string) => void
  onInterim?: (text: string) => void
  onPending?: () => void
  onListening?: () => void
  onError?: (message: string) => void
  onSettled?: () => void
}) {
  const preferredLang = options?.lang ?? 'zh-CN'
  const unsupportedReason = ref(getUnsupportedReason())
  const isSupported = computed(() => !unsupportedReason.value)
  const isListening = ref(false)
  const isPending = ref(false)
  const isBootstrapping = ref(true)
  const error = ref('')
  const recognitionMode = ref<RecognitionMode>('none')
  const activeLang = ref(preferredLang)
  const localModelStatus = ref<AvailabilityStatus | 'unsupported'>('unsupported')

  let recognition: SpeechRecognition | null = null
  let baseInput = ''
  let sessionFinalText = ''
  let manuallyStopped = false
  let sessionStarted = false
  let sessionGotResult = false
  let sessionGotError = false
  let startTimeoutId: ReturnType<typeof setTimeout> | null = null

  function clearStartTimeout() {
    if (startTimeoutId !== null) {
      clearTimeout(startTimeoutId)
      startTimeoutId = null
    }
  }

  function settle() {
    isPending.value = false
    isListening.value = false
    options?.onSettled?.()
  }

  function reportError(message: string) {
    if (!message) return
    sessionGotError = true
    error.value = message
    options?.onError?.(message)
  }

  function cleanupRecognition() {
    clearStartTimeout()
    if (!recognition) return
    recognition.onstart = null
    recognition.onresult = null
    recognition.onerror = null
    recognition.onend = null
    try {
      recognition.abort()
    } catch {
      try {
        recognition.stop()
      } catch {
        /* ignore */
      }
    }
    recognition = null
  }

  function cleanup() {
    cleanupRecognition()
    settle()
  }

  function formatError(code: string): string {
    switch (code) {
      case 'not-allowed':
      case 'service-not-allowed':
        return '麦克风权限被拒绝，请在浏览器地址栏左侧允许麦克风访问'
      case 'no-speech':
        return manuallyStopped ? '' : '未检测到语音，请再试一次'
      case 'network':
        return recognitionMode.value === 'local'
          ? '本地语音识别失败，请刷新页面后重试'
          : '云端语音识别不可用（国内网络通常无法访问 Google）。可尝试 Safari，或使用文字输入'
      case 'aborted':
        return ''
      case 'audio-capture':
        return '未检测到可用麦克风，请检查系统音频输入设备'
      case 'language-not-supported':
        return `当前浏览器不支持 ${activeLang.value} 语音识别`
      default:
        return `语音识别失败（${code}）`
    }
  }

  async function probeLocalForLang(
    Ctor: SpeechRecognitionStatic,
    lang: string
  ): Promise<AvailabilityStatus | null> {
    for (const quality of QUALITY_CANDIDATES) {
      const probeOptions: SpeechRecognitionOptions = {
        langs: [lang],
        processLocally: true,
        quality
      }
      let status = await Ctor.available!(probeOptions)

      if (status === 'downloadable' && Ctor.install) {
        localModelStatus.value = 'downloading'
        const installed = await Ctor.install({
          langs: [lang],
          processLocally: true,
          quality
        })
        if (!installed) continue
        status = await Ctor.available!(probeOptions)
      }

      if (status === 'available' || status === 'downloading') {
        return status
      }
    }
    return null
  }

  async function refreshLocalModel() {
    const Ctor = getSpeechRecognitionCtor() as SpeechRecognitionStatic | null
    if (!Ctor?.available) {
      recognitionMode.value = 'cloud'
      localModelStatus.value = 'unsupported'
      activeLang.value = preferredLang
      isBootstrapping.value = false
      return
    }

    const langCandidates = [preferredLang, ...LANG_CANDIDATES.filter(item => item !== preferredLang)]

    try {
      for (const lang of langCandidates) {
        const localStatus = await probeLocalForLang(Ctor, lang)
        if (localStatus === 'available') {
          activeLang.value = lang
          localModelStatus.value = 'available'
          recognitionMode.value = 'local'
          isBootstrapping.value = false
          return
        }
        if (localStatus === 'downloading') {
          activeLang.value = lang
          localModelStatus.value = 'downloading'
          recognitionMode.value = 'local'
          isBootstrapping.value = false
          return
        }
      }

      for (const lang of langCandidates) {
        const cloudStatus = await Ctor.available({ langs: [lang], processLocally: false })
        if (cloudStatus === 'available') {
          activeLang.value = lang
          localModelStatus.value = 'unavailable'
          recognitionMode.value = 'cloud'
          isBootstrapping.value = false
          return
        }
      }

      recognitionMode.value = 'none'
      localModelStatus.value = 'unavailable'
    } catch {
      recognitionMode.value = 'cloud'
      localModelStatus.value = 'unsupported'
      activeLang.value = preferredLang
    } finally {
      isBootstrapping.value = false
    }
  }

  function getStartBlockReason(): string | null {
    if (isBootstrapping.value) return '正在检测语音识别能力…'
    if (localModelStatus.value === 'downloading') return '本地语音模型正在下载，请稍候再试'
    if (recognitionMode.value === 'none') {
      return '当前环境无法使用语音识别。本地中文模型未就绪，且云端识别也不可用'
    }
    return null
  }

  function warmUpMicrophone() {
    if (!navigator.mediaDevices?.getUserMedia) return
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(stream => stream.getTracks().forEach(track => track.stop()))
      .catch(() => {
        /* SpeechRecognition.onerror 会给出更明确的提示 */
      })
  }

  function failStart(message: string) {
    reportError(message)
    cleanup()
  }

  function start(initialText = '') {
    error.value = ''
    manuallyStopped = false
    sessionStarted = false
    sessionGotResult = false
    sessionGotError = false

    const blockedReason = getUnsupportedReason()
    unsupportedReason.value = blockedReason
    if (blockedReason) {
      reportError(blockedReason)
      settle()
      return
    }

    const startBlockReason = getStartBlockReason()
    if (startBlockReason) {
      reportError(startBlockReason)
      settle()
      return
    }

    const Ctor = getSpeechRecognitionCtor()
    if (!Ctor) {
      reportError('当前浏览器不支持 Web Speech API，请使用 Chrome / Edge / Safari')
      settle()
      return
    }

    cleanupRecognition()
    baseInput = initialText.trim()
    sessionFinalText = ''
    isPending.value = true
    options?.onPending?.()

    warmUpMicrophone()

    recognition = new Ctor()
    recognition.lang = activeLang.value
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    if ('processLocally' in recognition) {
      recognition.processLocally = recognitionMode.value === 'local'
    }

    recognition.onstart = () => {
      clearStartTimeout()
      sessionStarted = true
      isPending.value = false
      isListening.value = true
      options?.onListening?.()
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      sessionGotResult = true
      let interim = ''
      let finalText = ''

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0]?.transcript ?? ''
        if (event.results[i].isFinal) {
          finalText += transcript
        } else {
          interim += transcript
        }
      }

      if (interim) {
        const parts = [baseInput, sessionFinalText, interim].filter(Boolean)
        options?.onInterim?.(parts.join(' '))
      }

      if (finalText.trim()) {
        sessionFinalText = sessionFinalText
          ? `${sessionFinalText} ${finalText.trim()}`
          : finalText.trim()
        const merged = baseInput ? `${baseInput} ${sessionFinalText}` : sessionFinalText
        options?.onFinal?.(merged)
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      clearStartTimeout()
      const message = formatError(event.error)
      if (message) reportError(message)
      cleanupRecognition()
      settle()
    }

    recognition.onend = () => {
      clearStartTimeout()
      if (!sessionStarted && !sessionGotError && !manuallyStopped) {
        reportError('语音识别未能启动，请确认浏览器已允许麦克风访问')
      } else if (
        sessionStarted &&
        !sessionGotResult &&
        !sessionGotError &&
        !manuallyStopped &&
        !error.value
      ) {
        reportError('语音识别已结束但未收到内容，请再试一次')
      }
      cleanupRecognition()
      settle()
    }

    try {
      recognition.start()
      startTimeoutId = setTimeout(() => {
        if (isPending.value && !sessionStarted) {
          failStart('语音识别启动超时，请检查麦克风权限后重试')
        }
      }, START_TIMEOUT_MS)
    } catch {
      failStart('无法启动语音识别，请刷新页面后重试')
    }
  }

  function stop() {
    manuallyStopped = true
    cleanup()
  }

  function toggle(initialText = '') {
    if (isListening.value || isPending.value) {
      stop()
      return
    }
    start(initialText)
  }

  onMounted(() => {
    unsupportedReason.value = getUnsupportedReason()
    void refreshLocalModel()
  })

  onUnmounted(() => {
    cleanup()
  })

  return {
    isSupported,
    unsupportedReason,
    isListening,
    isPending,
    isBootstrapping,
    recognitionMode,
    localModelStatus,
    error,
    refreshLocalModel,
    start,
    stop,
    toggle
  }
}
