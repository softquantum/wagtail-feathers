import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["groupSelect", "groupType", "locale"]
  static values = { 
    filterUrl: String,
    debug: Boolean 
  }

  connect() {
    const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
    
    if (isDebugMode) {
      console.log('ClassifierChooserController connected', this.element)
      console.log('Has groupType target:', this.hasGroupTypeTarget)
      console.log('Has groupSelect target:', this.hasGroupSelectTarget)
      console.log('Has locale target:', this.hasLocaleTarget)
      if (this.hasLocaleTarget) {
        console.log('Locale target(s):', this.localeTargets)
      }
    }
    
    if (!this.isClassifierForm()) {
      if (isDebugMode) {
        console.log('Not a classifier form, disconnecting controller')
      }
      return
    }

    // Since locale field doesn't always get Stimulus attributes properly,
    // add a manual event listener
    this.setupLocaleListener()

    this.initializeDropdown()
  }

  disconnect() {
    const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
    if (isDebugMode) {
      console.log('ClassifierChooserController disconnected')
    }
    // Clean up manual event listener
    if (this.localeChangeHandler) {
      const form = this.element.closest('form')
      if (form) {
        const localeSelect = form.querySelector('select[name="locale"]')
        if (localeSelect) {
          localeSelect.removeEventListener('change', this.localeChangeHandler)
        }
      }
    }
  }

  setupLocaleListener() {
    const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
    const form = this.element.closest('form')
    
    if (form) {
      const localeSelect = form.querySelector('select[name="locale"]')
      if (localeSelect) {
        if (isDebugMode) {
          console.log('Found locale select, adding manual listener:', localeSelect)
        }
        
        // Store the handler so we can remove it on disconnect
        this.localeChangeHandler = (event) => {
          this.localeChanged(event)
        }
        
        localeSelect.addEventListener('change', this.localeChangeHandler)
        
        // Also add as a target for Stimulus (might work for some cases)
        localeSelect.setAttribute('data-classifier-chooser-target', 'locale')
      } else if (isDebugMode) {
        console.log('No locale select found in form')
      }
    }
  }

  groupTypeChanged(event) {
    const groupType = event.target.value
    const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
    
    if (isDebugMode) {
      console.log(`Group type changed to: ${groupType}`)
    }

    const locale = this.getCurrentLocale()
    this.updateGroupDropdown(groupType, locale)
  }

  localeChanged(event) {
    const locale = event.target.value
    const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
    
    if (isDebugMode) {
      console.log(`Locale changed to: ${locale}`)
      console.log('Event target:', event.target)
      console.log('Has locale target:', this.hasLocaleTarget)
    }

    const groupType = this.getSelectedGroupType()
    
    if (isDebugMode) {
      console.log(`Current group type: ${groupType}`)
      console.log(`Updating dropdown with groupType="${groupType}", locale="${locale}"`)
    }
    
    this.updateGroupDropdown(groupType, locale)
  }

  isClassifierForm() {
    // Check if form action contains classifier_chooser
    const form = this.element.closest('form')
    if (!form) return false
    
    const formAction = form.getAttribute('action') || ''
    if (!formAction.includes('classifier_chooser')) {
      return false
    }
    
    const hasGroupType = this.hasGroupTypeTarget
    const hasGroupSelect = this.hasGroupSelectTarget
    
    const subjectRadio = form.querySelector('input[name="group_type"][value="Subject"]')
    const attributeRadio = form.querySelector('input[name="group_type"][value="Attribute"]')
    
    return !!(hasGroupType && hasGroupSelect && (subjectRadio || attributeRadio))
  }

  initializeDropdown() {
    const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
    
    if (isDebugMode) {
      console.log('Initializing classifier chooser dropdown')
    }

    const groupType = this.getSelectedGroupType()
    const locale = this.getCurrentLocale()
    
    if (isDebugMode) {
      console.log(`Initial load: group_type=${groupType}, locale=${locale}`)
    }
    
    this.updateGroupDropdown(groupType, locale)
  }

  getSelectedGroupType() {
    if (!this.hasGroupTypeTarget) return ''
    
    const checkedRadio = this.groupTypeTargets.find(radio => radio.checked)
    return checkedRadio ? checkedRadio.value : ''
  }

  getCurrentLocale() {
    // Try Stimulus target first
    if (this.hasLocaleTarget) {
      const localeElement = Array.isArray(this.localeTargets) ? this.localeTargets[0] : this.localeTarget
      if (localeElement && localeElement.value !== undefined) {
        return localeElement.value
      }
    }
    
    // Fallback: try to find locale select directly
    const form = this.element.closest('form')
    if (form) {
      const localeSelect = form.querySelector('select[name="locale"]')
      if (localeSelect) {
        return localeSelect.value
      }
    }
    
    // Last fallback: get from URL
    if (form) {
      const formAction = form.getAttribute('action')
      try {
        const url = new URL(formAction, window.location.origin)
        return url.searchParams.get('locale') || ''
      } catch {
        return ''
      }
    }
    
    return ''
  }

  async updateGroupDropdown(groupType, locale) {
    if (!this.hasGroupSelectTarget) {
      console.error('ClassifierChooser: No group select target found')
      return
    }

    const select = this.groupSelectTarget
    const originalOptions = this.saveOriginalOptions(select)

    try {
      select.disabled = true
      select.innerHTML = '<option value="">Loading...</option>'

      const url = new URL(this.filterUrlValue, window.location.origin)
      if (groupType) {
        url.searchParams.set('group_type', groupType)
      }
      if (locale) {
        url.searchParams.set('locale', locale)
      }

      const isDebugMode = this.hasDebugValue ? this.debugValue : window.CLASSIFIER_DEBUG
      if (isDebugMode) {
        console.log('Fetching from:', url.toString())
      }

      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const choices = await response.json()
      
      if (!Array.isArray(choices)) {
        throw new Error('Invalid response format: expected array')
      }

      this.populateSelect(select, choices, originalOptions[0]?.value)
      
      select.disabled = false

      if (isDebugMode) {
        console.log(`Updated group dropdown with ${choices.length} options`)
      }

      if (select.isConnected) {
        select.dispatchEvent(new Event('change', { bubbles: true }))
      }

    } catch (error) {
      console.error('Error updating group dropdown:', error)
      
      this.restoreOriginalOptions(select, originalOptions)
      select.disabled = false
    }
  }

  saveOriginalOptions(select) {
    return Array.from(select.options).map(opt => ({
      value: opt.value,
      text: opt.textContent,
      selected: opt.selected
    }))
  }

  populateSelect(select, choices, previousValue = '') {
    select.innerHTML = ''
    
    choices.forEach(choice => {
      if (choice && typeof choice === 'object' && 'id' in choice && 'name' in choice) {
        const option = document.createElement('option')
        option.value = choice.id
        option.textContent = choice.name
        
        if (choice.id === previousValue) {
          option.selected = true
        }
        
        select.appendChild(option)
      }
    })
  }

  restoreOriginalOptions(select, originalOptions) {
    try {
      select.innerHTML = ''
      if (originalOptions && originalOptions.length > 0) {
        originalOptions.forEach(opt => {
          const option = document.createElement('option')
          option.value = opt.value
          option.textContent = opt.text
          option.selected = opt.selected
          select.appendChild(option)
        })
      } else {
        select.innerHTML = '<option value="">Error loading options</option>'
      }
    } catch (restoreError) {
      select.innerHTML = '<option value="">Error loading options</option>'
    }
  }
}