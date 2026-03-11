import { ref, computed } from 'vue'

interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  response?: unknown
}

export function useUpload(options: {
  maxSize?: number
  maxCount?: number
  accept?: string[]
  onError?: (error: Error, file: UploadFile) => void
} = {}) {
  const {
    maxSize = 10 * 1024 * 1024, // 10MB default
    maxCount = 50,
    accept = ['image/jpeg', 'image/png', 'image/webp'],
    onError
  } = options

  const files = ref<UploadFile[]>([])
  const uploading = ref(false)

  const totalProgress = computed(() => {
    if (files.value.length === 0) return 0
    const total = files.value.reduce((sum, f) => sum + f.progress, 0)
    return Math.round(total / files.value.length)
  })

  const pendingFiles = computed(() => 
    files.value.filter(f => f.status === 'pending')
  )

  const uploadingFiles = computed(() => 
    files.value.filter(f => f.status === 'uploading')
  )

  const completedFiles = computed(() => 
    files.value.filter(f => f.status === 'success')
  )

  const hasErrors = computed(() => 
    files.value.some(f => f.status === 'error')
  )

  const validateFile = (file: File): string | null => {
    if (file.size > maxSize) {
      return `文件大小超过 ${(maxSize / 1024 / 1024).toFixed(0)}MB 限制`
    }
    if (accept.length > 0 && !accept.includes(file.type)) {
      return `不支持的文件类型: ${file.type}`
    }
    return null
  }

  const addFiles = (newFiles: FileList | null): UploadFile[] => {
    if (!newFiles) return []

    const addedFiles: UploadFile[] = []
    const remainingSlots = maxCount - files.value.length

    Array.from(newFiles).slice(0, remainingSlots).forEach(file => {
      const error = validateFile(file)
      
      const uploadFile: UploadFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        name: file.name,
        size: file.size,
        progress: 0,
        status: error ? 'error' : 'pending'
      }

      if (error) {
        uploadFile.error = error
        onError?.(new Error(error), uploadFile)
      }

      files.value.push(uploadFile)
      addedFiles.push(uploadFile)
    })

    return addedFiles
  }

  const removeFile = (id: string) => {
    const index = files.value.findIndex(f => f.id === id)
    if (index > -1) {
      files.value.splice(index, 1)
    }
  }

  const clearFiles = () => {
    files.value = []
  }

  const updateProgress = (id: string, progress: number) => {
    const file = files.value.find(f => f.id === id)
    if (file) {
      file.progress = Math.min(100, Math.max(0, progress))
    }
  }

  const setStatus = (id: string, status: UploadFile['status']) => {
    const file = files.value.find(f => f.id === id)
    if (file) {
      file.status = status
    }
  }

  const uploadFile = async (
    id: string,
    uploadFn: (file: File, onProgress: (progress: number) => void) => Promise<unknown>
  ): Promise<unknown> => {
    const file = files.value.find(f => f.id === id)
    if (!file || file.status === 'error') {
      throw new Error('File not found or has error')
    }

    file.status = 'uploading'

    try {
      const response = await uploadFn(file.file, (progress) => {
        updateProgress(id, progress)
      })

      file.status = 'success'
      file.response = response
      return response
    } catch (error) {
      file.status = 'error'
      file.error = error instanceof Error ? error.message : 'Upload failed'
      throw error
    }
  }

  const uploadAll = async (
    uploadFn: (file: File, onProgress: (progress: number) => void) => Promise<unknown>
  ): Promise<unknown[]> => {
    uploading.value = true

    const results = await Promise.allSettled(
      pendingFiles.value.map(file => uploadFile(file.id, uploadFn))
    )

    uploading.value = false
    return results.map(r => r.status === 'fulfilled' ? r.value : null)
  }

  return {
    // State
    files,
    uploading,
    totalProgress,
    pendingFiles,
    uploadingFiles,
    completedFiles,
    hasErrors,

    // Actions
    addFiles,
    removeFile,
    clearFiles,
    updateProgress,
    setStatus,
    uploadFile,
    uploadAll
  }
}
