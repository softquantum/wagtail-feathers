import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["searchInput", "classifierList", "classifierItem", "selectedCount"]

  connect() {
    if (window.CLASSIFIER_DEBUG) {
      console.log("ClassifierModalController connected")
    }
    this.initializeFromFormset()
    this.updateSelectedCount()
    this.setupSearchListener()
    
    this.updateGroupSelectionCounts()
    
    if (window.CLASSIFIER_DEBUG) {
      this.debugFormsetState('Initial load')
      this.setupFormSubmissionDebugging()
    }
  }

  setupSearchListener() {
    if (this.hasSearchInputTarget) {
      this.searchInputTarget.addEventListener('input', this.handleSearch.bind(this))
    }
  }

  initializeFromFormset() {
    const formsetItems = this.element.querySelectorAll('.sequence-member[data-classifier-id]')
    formsetItems.forEach(item => {
      const classifierId = item.dataset.classifierId
      if (classifierId) {
        this.markCheckboxAsSelected(classifierId)
      }
    })
  }

  markCheckboxAsSelected(classifierId) {
    const checkbox = this.element.querySelector(`input[type="checkbox"][value="${classifierId}"]`)
    if (checkbox) {
      checkbox.checked = true
      const item = checkbox.closest('.classifier-item')
      if (item) {
        item.classList.add('selected')
      }
    }
  }

  handleSelection(event) {
    const input = event.target
    const classifierId = input.value
    const group = input.closest('.classifier-group')
    const maxSelections = parseInt(group.dataset.maxSelections) || 0
    
    if (input.type === 'radio') {
      this.clearGroupSelections(group, input)
      if (input.checked) {
        this.addClassifierToFormset(classifierId)
      }
    } else {
      if (input.checked) {
        if (maxSelections > 0) {
          const currentSelections = group.querySelectorAll('input[type="checkbox"]:checked').length
          if (currentSelections > maxSelections) {
            input.checked = false
            this.showLimitError(group, maxSelections)
            return
          }
        }
        this.addClassifierToFormset(classifierId)
      } else {
        this.removeClassifierFromFormset(classifierId)
      }
    }
    
    this.updateSelectedCount()
  }

  addClassifierToFormset(classifierId) {
    const existingMember = this.element.querySelector(`.sequence-member[data-classifier-id="${classifierId}"]`)
    if (existingMember) {
      const deleteField = existingMember.querySelector('input[name*="-DELETE"]')
      if (deleteField && deleteField.value === '1') {
        deleteField.value = ''
        existingMember.style.display = ''
        const checkbox = this.element.querySelector(`input[value="${classifierId}"]`)
        if (checkbox) checkbox.checked = true
      }
      return
    }

    const prefix = this.getFormsetPrefix()
    const formsetContainer = this.element.querySelector('.w-sequence')
    if (!formsetContainer) return
    
    const existingForms = formsetContainer.querySelectorAll('.sequence-member').length
    const newIndex = existingForms
    
    const newFormHtml = `
      <div class="sequence-member sequence-member-${newIndex}" data-classifier-id="${classifierId}">
        <input type="hidden" name="${prefix}-${newIndex}-id" value="">
        <input type="hidden" name="${prefix}-${newIndex}-ORDER" value="${newIndex}">
        <input type="hidden" name="${prefix}-${newIndex}-DELETE" value="">
        <select name="${prefix}-${newIndex}-classifier" id="id_${prefix}-${newIndex}-classifier" style="display: none;">
          <option value="${classifierId}" selected>${classifierId}</option>
        </select>
      </div>
    `
    
    formsetContainer.insertAdjacentHTML('beforeend', newFormHtml)
    this.updateManagementForm()
    
    const newSelect = formsetContainer.querySelector(`select[name="${prefix}-${newIndex}-classifier"]`)
    if (newSelect) {
      newSelect.value = classifierId
      newSelect.dispatchEvent(new Event('change', { bubbles: true }))
    }
  }

  removeClassifierFromFormset(classifierId) {
    const member = this.element.querySelector(`.sequence-member[data-classifier-id="${classifierId}"]`)
    if (member) {
      const idField = member.querySelector('input[name*="-id"]')
      const deleteField = member.querySelector('input[name*="-DELETE"]')
      
      if (idField && idField.value) {
        if (deleteField) {
          deleteField.value = '1'  // Django expects '1' for true
          member.style.display = 'none'  // Hide but don't remove
        }
      } else {
        member.remove()
        this.renumberFormsetIndices()  // Renumber remaining forms
      }
      
      this.updateManagementForm()
    }
  }

  updateManagementForm() {
    const prefix = this.getFormsetPrefix()
    const totalFormsInput = this.element.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`)
    const initialFormsInput = this.element.querySelector(`input[name="${prefix}-INITIAL_FORMS"]`)
    
    if (totalFormsInput) {
      const allForms = this.element.querySelectorAll('.sequence-member')
      totalFormsInput.value = allForms.length
    }
  }
  
  getFormsetPrefix() {
    const totalFormsInput = this.element.querySelector('input[name*="-TOTAL_FORMS"]')
    if (totalFormsInput) {
      const name = totalFormsInput.name
      return name.replace('-TOTAL_FORMS', '')
    }
    return 'classifiers'  // Default fallback
  }
  
  renumberFormsetIndices() {
    const prefix = this.getFormsetPrefix()
    const forms = this.element.querySelectorAll('.sequence-member')
    
    forms.forEach((form, index) => {
      const inputs = form.querySelectorAll('input, select, textarea')
      inputs.forEach(input => {
        const name = input.name
        const id = input.id
        
        if (name) {
          const newName = name.replace(new RegExp(`${prefix}-(\\d+)-`), `${prefix}-${index}-`)
          input.name = newName
        }
        
        if (id) {
          const newId = id.replace(new RegExp(`${prefix}-(\\d+)-`), `${prefix}-${index}-`)
          input.id = newId
        }
      })
      
      form.className = form.className.replace(/sequence-member-\d+/, `sequence-member-${index}`)
    })
  }

  toggleGroup(event) {
    const button = event.target.closest('.group-toggle')
    const groupName = button.dataset.group
    const group = button.closest('.classifier-group')
    const items = group.querySelector('.classifier-items')
    const icon = button.querySelector('.toggle-icon')
    
    if (items.style.display === 'none') {
      items.style.display = 'block'
      icon.textContent = '▼'
      button.classList.add('expanded')
    } else {
      items.style.display = 'none'
      icon.textContent = '▶'
      button.classList.remove('expanded')
    }
  }
  
  toggleAllGroups(event) {
    const button = event.target.closest('.collapse-all-button')
    const currentState = button.dataset.state
    const icon = button.querySelector('.collapse-all-icon')
    const text = button.querySelector('.collapse-all-text')
    const groups = this.element.querySelectorAll('.classifier-group')
    
    if (currentState === 'expanded') {
      groups.forEach(group => {
        const items = group.querySelector('.classifier-items')
        const toggleIcon = group.querySelector('.toggle-icon')
        const groupToggle = group.querySelector('.group-toggle')
        
        items.style.display = 'none'
        toggleIcon.textContent = '▶'
        groupToggle.classList.remove('expanded')
      })
      
      button.dataset.state = 'collapsed'
      text.textContent = 'Expand All'
    } else {
      groups.forEach(group => {
        const items = group.querySelector('.classifier-items')
        const toggleIcon = group.querySelector('.toggle-icon')
        const groupToggle = group.querySelector('.group-toggle')
        
        items.style.display = 'block'
        toggleIcon.textContent = '▼'
        groupToggle.classList.add('expanded')
      })
      
      button.dataset.state = 'expanded'
      text.textContent = 'Collapse All'
    }
  }

  handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase()
    const items = this.classifierItemTargets
    
    items.forEach(item => {
      const name = item.dataset.classifierName?.toLowerCase() || ''
      const group = item.dataset.group?.toLowerCase() || ''
      const type = item.dataset.type?.toLowerCase() || ''
      
      const matches = name.includes(searchTerm) || 
                     group.includes(searchTerm) || 
                     type.includes(searchTerm)
      
      item.style.display = matches ? 'block' : 'none'
      
      if (matches) {
        const parentGroup = item.closest('.classifier-group')
        if (parentGroup) {
          parentGroup.style.display = 'block'
          const groupItems = parentGroup.querySelector('.classifier-items')
          const toggleButton = parentGroup.querySelector('.group-toggle')
          const icon = toggleButton.querySelector('.toggle-icon')
          
          if (groupItems.style.display === 'none') {
            groupItems.style.display = 'block'
            icon.textContent = '▼'
            toggleButton.classList.add('expanded')
          }
        }
      }
    })
    
    const groups = this.element.querySelectorAll('.classifier-group')
    groups.forEach(group => {
      const visibleItems = group.querySelectorAll('.classifier-item[style*="block"], .classifier-item:not([style*="none"])')
      if (visibleItems.length === 0 && searchTerm !== '') {
        group.style.display = 'none'
      } else if (searchTerm === '') {
        group.style.display = 'block'
      }
    })
  }

  clearAllAction() {
    const checkedInputs = this.element.querySelectorAll('.classifier-item input:checked')
    checkedInputs.forEach(input => {
      input.checked = false
      this.removeClassifierFromFormset(input.value)
    })
    this.updateSelectedCount()
  }

  updateSelectedCount() {
    const selectedCount = this.element.querySelectorAll('.classifier-item input:checked').length
    
    if (this.hasSelectedCountTarget) {
      this.selectedCountTarget.textContent = selectedCount
    }
    
    const countContainer = this.element.querySelector('.selected-count-container')
    if (countContainer) {
      countContainer.style.display = selectedCount > 0 ? 'inline-block' : 'none'
    }
    
    const totalCountContainer = this.element.querySelector('.total-selected-count-container')
    if (totalCountContainer) {
      totalCountContainer.style.display = selectedCount > 0 ? 'inline-block' : 'none'
    }
    
    this.updateGroupSelectionCounts()
  }

  clearGroupSelections(group, exceptInput = null) {
    const groupName = group.dataset.group
    
    const selectedInputs = group.querySelectorAll('input:checked')
    selectedInputs.forEach(input => {
      if (input !== exceptInput) { // Don't clear the one we just selected
        input.checked = false
        this.removeClassifierFromFormset(input.value)
      }
    })
  }
  
  showLimitError(group, maxSelections) {
    const groupName = group.dataset.group
    const groupType = group.dataset.type
    
    let errorElement = group.querySelector('.selection-limit-error')
    if (!errorElement) {
      errorElement = document.createElement('div')
      errorElement.className = 'selection-limit-error'
      group.appendChild(errorElement)
    }
    
    errorElement.textContent = `Maximum ${maxSelections} selection${maxSelections > 1 ? 's' : ''} allowed for ${groupType}: ${groupName}`
    errorElement.style.display = 'block'
    
    setTimeout(() => {
      if (errorElement) {
        errorElement.style.display = 'none'
      }
    }, 3000)
  }

  updateGroupSelectionCounts() {
    const groups = this.element.querySelectorAll('.classifier-group')
    
    groups.forEach(group => {
      const groupName = group.dataset.group
      const groupType = group.dataset.type
      const maxSelections = parseInt(group.dataset.maxSelections) || 0
      
      const selectedInGroup = group.querySelectorAll('.classifier-item input:checked').length
      const totalInGroup = group.querySelectorAll('.classifier-item input').length
      
      const groupHeader = group.querySelector('.group-toggle')
      const existingBadge = groupHeader.querySelector('.group-selected-badge')
      const toggleIcon = groupHeader.querySelector('.toggle-icon')
      const groupItems = group.querySelector('.classifier-items')
      
      if (existingBadge) {
        existingBadge.remove()
      }
      
      if (selectedInGroup > 0) {
        const badge = document.createElement('span')
        badge.className = 'badge group-selected-badge'
        
        if (maxSelections === 1) {
          badge.textContent = '1 selected'
        } else if (maxSelections > 1) {
          badge.textContent = `${selectedInGroup}/${maxSelections} selected`
        } else {
          badge.textContent = `${selectedInGroup} selected`
        }
        
        groupHeader.appendChild(badge)
        
        if (groupItems.style.display === 'none') {
          groupItems.style.display = 'block'
          toggleIcon.textContent = '▼'
          groupHeader.classList.add('expanded')
        }
      } else {
        groupItems.style.display = 'none'
        toggleIcon.textContent = '▶'
        groupHeader.classList.remove('expanded')
      }
    })
  }
  
  debugFormsetState(context = '') {
    console.group(`Formset Debug: ${context}`)
    
    const prefix = this.getFormsetPrefix()
    const totalFormsInput = this.element.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`)
    const initialFormsInput = this.element.querySelector(`input[name="${prefix}-INITIAL_FORMS"]`)
    const forms = this.element.querySelectorAll('.sequence-member')
    
    console.log('Management form:')
    console.log(`  TOTAL_FORMS: ${totalFormsInput?.value || 'not found'}`)
    console.log(`  INITIAL_FORMS: ${initialFormsInput?.value || 'not found'}`)
    console.log(`  Prefix: ${prefix}`)
    
    console.log(`\nForms found: ${forms.length}`)
    forms.forEach((form, index) => {
      const classifierId = form.dataset.classifierId
      const idField = form.querySelector('input[name*="-id"]')
      const deleteField = form.querySelector('input[name*="-DELETE"]')
      const selectField = form.querySelector('select[name*="-classifier"]')
      
      console.log(`Form ${index}:`)
      console.log(`  data-classifier-id: ${classifierId || 'none'}`)
      console.log(`  id field value: ${idField?.value || 'empty'}`)
      console.log(`  DELETE field value: ${deleteField?.value || 'empty'}`)
      console.log(`  classifier select value: ${selectField?.value || 'none'}`)
      console.log(`  visible: ${form.style.display !== 'none'}`)
    })
    
    console.groupEnd()
  }
  
  setupFormSubmissionDebugging() {
    const form = this.element.closest('form')
    if (form) {
      form.addEventListener('submit', (e) => {
        console.group('Form Submission Debug')
        
        const formData = new FormData(form)
        const classifierData = []
        
        for (let [key, value] of formData.entries()) {
          if (key.includes('classifiers')) {
            classifierData.push({ key, value })
          }
        }
        
        console.log('Classifier form data being submitted:')
        console.table(classifierData)
        this.debugFormsetState('Form submission')
        console.groupEnd()
      })
    }
  }
}